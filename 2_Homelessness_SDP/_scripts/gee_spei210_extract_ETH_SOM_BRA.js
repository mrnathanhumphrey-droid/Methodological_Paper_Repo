// GEE Code Editor script for PRE_REG_036 (P8-F).
// Extracts December 12-month SPEI (v2.10, 1901-2023) area-means over the
// ETH / SOM / BRA-Amazon boxes, 1950-2023, as a CSV for the ENSO test.
// Paste into https://code.earthengine.google.com, Run, then run the Export task.

var spei = ee.ImageCollection("CSIC/SPEI/2_10").select('SPEI_12_month');

// bbox = [west, south, east, north]
var boxes = {
  ETH: ee.Geometry.Rectangle([33, 3, 48, 15]),
  SOM: ee.Geometry.Rectangle([41, -2, 51, 12]),
  BRA: ee.Geometry.Rectangle([-73, -12, -50, 5])   // Amazon basin
};

var SCALE = 55660;  // ~0.5 deg native SPEI grid

var years = ee.List.sequence(1950, 2023);

var rows = years.map(function (y) {
  y = ee.Number(y);
  var start = ee.Date.fromYMD(y, 12, 1);                 // December value
  var img = spei.filterDate(start, start.advance(1, 'month')).first();
  function box(g) {
    return ee.Algorithms.If(
      img,
      img.reduceRegion({reducer: ee.Reducer.mean(), geometry: g,
                        scale: SCALE, maxPixels: 1e9}).get('SPEI_12_month'),
      null);
  }
  return ee.Feature(null, {
    year: y,
    ETH: box(boxes.ETH),
    SOM: box(boxes.SOM),
    BRA: box(boxes.BRA)
  });
});

var fc = ee.FeatureCollection(rows);
print('SPEI_12 December area-means 1950-2023', fc);

Export.table.toDrive({
  collection: fc,
  description: 'SPEI12_Dec_ETH_SOM_BRA_1950_2023',
  fileFormat: 'CSV',
  selectors: ['year', 'ETH', 'SOM', 'BRA']
});
