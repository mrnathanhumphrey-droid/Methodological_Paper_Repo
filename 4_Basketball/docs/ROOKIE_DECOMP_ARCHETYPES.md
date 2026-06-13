# Rookie Decomp — Archetype Clusters

K-means K=8 on 16 features (combine + pre-NBA per-40).
Window: 2014-2024 draft years.

## Cluster sizes

| archetype        |   count |
|:-----------------|--------:|
| Utility Wing 2   |     125 |
| Utility Wing 3   |      84 |
| Stretch Big      |      66 |
| Pass-First PG    |      62 |
| Score-First Wing |      60 |
| Wing Shooter     |      42 |
| Utility Wing     |      25 |
| Defensive Big    |      21 |

## Y1 outcome means per archetype

| archetype        |   n |   nba_y1_pts_per36 |   nba_y1_reb_per36 |   nba_y1_ast_per36 |   nba_y1_stl_per36 |   nba_y1_blk_per36 |   nba_y1_fg3m_per36 |   nba_y1_mpg |   nba_y1_gp |   nba_y1_fg_pct |   nba_y1_fg3_pct |
|:-----------------|----:|-------------------:|-------------------:|-------------------:|-------------------:|-------------------:|--------------------:|-------------:|------------:|----------------:|-----------------:|
| Utility Wing 2   |  95 |              13.16 |               5.5  |               2.51 |               1.14 |               0.54 |                1.61 |        19.59 |       58.61 |            0.42 |             0.32 |
| Utility Wing 3   |  69 |              13.35 |               5.33 |               3.83 |               1.17 |               0.53 |                1.55 |        20.35 |       54.81 |            0.41 |             0.32 |
| Stretch Big      |  45 |              13.88 |               8.91 |               1.8  |               0.91 |               1.35 |                1.05 |        16.39 |       52.71 |            0.48 |             0.27 |
| Pass-First PG    |  42 |              13.25 |               4.3  |               4.89 |               1.36 |               0.36 |                1.71 |        17.28 |       53.4  |            0.39 |             0.31 |
| Score-First Wing |  41 |              14.91 |               8.2  |               2.1  |               1.05 |               1.28 |                1.1  |        21.71 |       57.8  |            0.48 |             0.27 |
| Wing Shooter     |  26 |              13.72 |               4.54 |               2.58 |               1.04 |               0.36 |                2.25 |        13.97 |       47.62 |            0.4  |             0.34 |
| Utility Wing     |  18 |              11.54 |               5.08 |               3.15 |               1.22 |               0.59 |                1.18 |        15.3  |       53.17 |            0.43 |             0.32 |
| Defensive Big    |  15 |              11.59 |               8.99 |               1.94 |               0.87 |               1.75 |                0.19 |        13.82 |       49.47 |            0.56 |             0.09 |

## Sample players per cluster (top 5 by draft pick)

### Utility Wing 2

| player_name_raw   |   draft_year |   draft_pick |   combine_height_with_shoes_inches |   nba_y1_pts_per36 |   nba_y1_reb_per36 |   nba_y1_ast_per36 |
|:------------------|-------------:|-------------:|-----------------------------------:|-------------------:|-------------------:|-------------------:|
| Andrew Wiggins    |         2014 |            1 |                              nan   |               16.8 |                4.5 |                2.1 |
| Brandon Ingram    |         2016 |            2 |                              nan   |               11.7 |                5   |                2.6 |
| Aaron Gordon      |         2014 |            4 |                               80.8 |               11   |                7.6 |                1.5 |
| Stephon Castle    |         2024 |            4 |                              nan   |               19.8 |                4.9 |                5.5 |
| Amen Thompson     |         2023 |            4 |                              nan   |               15.3 |               10.6 |                4.2 |
| Patrick Williams  |         2020 |            4 |                              nan   |               11.9 |                5.9 |                1.8 |
| De'Andre Hunter   |         2019 |            4 |                              nan   |               13.9 |                5.1 |                2   |
| Ausar Thompson    |         2023 |            5 |                              nan   |               12.6 |                9.1 |                2.7 |

### Utility Wing 3

| player_name_raw    |   draft_year |   draft_pick |   combine_height_with_shoes_inches |   nba_y1_pts_per36 |   nba_y1_reb_per36 |   nba_y1_ast_per36 |
|:-------------------|-------------:|-------------:|-----------------------------------:|-------------------:|-------------------:|-------------------:|
| Cade Cunningham    |         2021 |            1 |                                nan |               19.2 |                6.1 |                6.1 |
| Anthony Edwards    |         2020 |            1 |                                nan |               21.7 |                5.2 |                3.3 |
| Ben Simmons        |         2016 |            1 |                                nan |               16.9 |                8.7 |                8.7 |
| Paolo Banchero     |         2022 |            1 |                                nan |               21.3 |                7.4 |                4   |
| Zaccharie Risacher |         2024 |            1 |                                nan |               18.4 |                5.2 |                1.8 |
| D'Angelo Russell   |         2015 |            2 |                                 77 |               16.8 |                4.4 |                4.2 |
| Jalen Green        |         2021 |            2 |                                nan |               19.5 |                3.8 |                3   |
| Lonzo Ball         |         2017 |            2 |                                nan |               10.7 |                7.3 |                7.6 |

### Stretch Big

| player_name_raw    |   draft_year |   draft_pick |   combine_height_with_shoes_inches |   nba_y1_pts_per36 |   nba_y1_reb_per36 |   nba_y1_ast_per36 |
|:-------------------|-------------:|-------------:|-----------------------------------:|-------------------:|-------------------:|-------------------:|
| Alex Sarr          |         2024 |            2 |                              nan   |               17.2 |                8.6 |                3.2 |
| Jaren Jackson Jr.  |         2018 |            4 |                               83.2 |               19   |                6.5 |                1.5 |
| Mo Bamba           |         2018 |            6 |                               84.8 |               13.7 |               11   |                1.8 |
| Wendell Carter Jr. |         2018 |            7 |                               82   |               14.8 |               10   |                2.5 |
| Donovan Clingan    |         2024 |            7 |                              nan   |               11.9 |               14.3 |                2.1 |
| Jaxson Hayes       |         2019 |            8 |                               83.5 |               15.7 |                8.6 |                1.9 |
| Marquese Chriss    |         2016 |            8 |                               82   |               15.6 |                7.2 |                1.2 |
| Noah Vonleh        |         2014 |            9 |                               81.5 |               11.5 |               12   |                0.6 |

### Pass-First PG

| player_name_raw   |   draft_year |   draft_pick |   combine_height_with_shoes_inches |   nba_y1_pts_per36 |   nba_y1_reb_per36 |   nba_y1_ast_per36 |
|:------------------|-------------:|-------------:|-----------------------------------:|-------------------:|-------------------:|-------------------:|
| Reed Sheppard     |         2024 |            3 |                              nan   |               12.6 |                4.3 |                4.1 |
| De'Aaron Fox      |         2017 |            5 |                               75.2 |               15   |                3.6 |                5.7 |
| Trae Young        |         2018 |            5 |                               73.8 |               22.3 |                4.3 |                9.4 |
| Coby White        |         2019 |            7 |                               76.8 |               18.5 |                4.9 |                3.8 |
| Rob Dillingham    |         2024 |            8 |                              nan   |               15.3 |                3.5 |                6.8 |
| Collin Sexton     |         2018 |            8 |                               73.5 |               18.9 |                3.3 |                3.4 |
| Dyson Daniels     |         2022 |            8 |                               79.5 |                7.8 |                6.5 |                4.6 |
| Davion Mitchell   |         2021 |            9 |                               73.2 |               14.9 |                2.9 |                5.4 |

### Score-First Wing

| player_name_raw    |   draft_year |   draft_pick |   combine_height_with_shoes_inches |   nba_y1_pts_per36 |   nba_y1_reb_per36 |   nba_y1_ast_per36 |
|:-------------------|-------------:|-------------:|-----------------------------------:|-------------------:|-------------------:|-------------------:|
| Deandre Ayton      |         2018 |            1 |                                nan |               19.1 |               12   |                2.1 |
| Karl-Anthony Towns |         2015 |            1 |                                nan |               20.6 |               11.8 |                2.2 |
| Chet Holmgren      |         2022 |            2 |                                nan |               20.2 |                9.7 |                3   |
| Brandon Miller     |         2023 |            2 |                                nan |               19.3 |                4.8 |                2.6 |
| Jabari Parker      |         2014 |            2 |                                nan |               15   |                6.7 |                2   |
| Jayson Tatum       |         2017 |            3 |                                nan |               16.4 |                5.9 |                1.9 |
| Jahlil Okafor      |         2015 |            3 |                                nan |               21   |                8.4 |                1.5 |
| Jabari Smith Jr.   |         2022 |            3 |                                nan |               14.8 |                8.4 |                1.5 |

### Wing Shooter

| player_name_raw   |   draft_year |   draft_pick |   combine_height_with_shoes_inches |   nba_y1_pts_per36 |   nba_y1_reb_per36 |   nba_y1_ast_per36 |
|:------------------|-------------:|-------------:|-----------------------------------:|-------------------:|-------------------:|-------------------:|
| Nik Stauskas      |         2014 |            8 |                               78.5 |               10.2 |                2.8 |                2.1 |
| Cody Williams     |         2024 |           10 |                              nan   |                7.8 |                3.8 |                2   |
| Doug McDermott    |         2014 |           11 |                               79.8 |               12.2 |                4.8 |                0.7 |
| Malik Monk        |         2017 |           11 |                              nan   |               17.7 |                2.8 |                3.8 |
| Luke Kennard      |         2017 |           12 |                               77.5 |               13.7 |                4.3 |                3.1 |
| T.J. Warren       |         2014 |           14 |                               80.2 |               14.4 |                5   |                1.5 |
| Jordan Hawkins    |         2023 |           14 |                              nan   |               16.2 |                4.6 |                2.2 |
| Moses Moody       |         2021 |           14 |                               78   |               13.5 |                4.7 |                1.4 |

### Utility Wing

| player_name_raw   |   draft_year |   draft_pick |   combine_height_with_shoes_inches |   nba_y1_pts_per36 |   nba_y1_reb_per36 |   nba_y1_ast_per36 |
|:------------------|-------------:|-------------:|-----------------------------------:|-------------------:|-------------------:|-------------------:|
| Josh Jackson      |         2017 |            4 |                              nan   |               18.6 |                6.5 |                2.2 |
| Marcus Smart      |         2014 |            6 |                               75.2 |               10.4 |                4.4 |                4.1 |
| Jonathan Isaac    |         2017 |            6 |                              nan   |                9.8 |                6.7 |                1.2 |
| Elfrid Payton     |         2014 |           10 |                               75.8 |               10.6 |                5   |                7.7 |
| Matas Buzelis     |         2024 |           11 |                              nan   |               16.4 |                6.6 |                1.9 |
| Josh Green        |         2020 |           18 |                               77.5 |                8.2 |                6.3 |                2.3 |
| Delon Wright      |         2015 |           20 |                               77.5 |               16.2 |                5.8 |                4.9 |
| DeAndre' Bembry   |         2016 |           21 |                               77.8 |                9.8 |                5.7 |                2.7 |

### Defensive Big

| player_name_raw     |   draft_year |   draft_pick |   combine_height_with_shoes_inches |   nba_y1_pts_per36 |   nba_y1_reb_per36 |   nba_y1_ast_per36 |
|:--------------------|-------------:|-------------:|-----------------------------------:|-------------------:|-------------------:|-------------------:|
| James Wiseman       |         2020 |            2 |                              nan   |               19.3 |                9.7 |                1.1 |
| Willie Cauley-Stein |         2015 |            6 |                               84.5 |               11.8 |                9   |                0.9 |
| Jakob Poeltl        |         2016 |            9 |                               85   |                9.5 |                9.5 |                0.7 |
| Zach Collins        |         2017 |           10 |                               84   |               10.1 |                7.6 |                1.8 |
| Caleb Swanigan      |         2017 |           26 |                               80.5 |               11.6 |               10.3 |                2.7 |
| Daniel Oturu        |         2020 |           33 |                              nan   |               12.1 |               10.7 |                2.2 |
| Christian Koloko    |         2022 |           33 |                               84   |                8.2 |                7.7 |                1.4 |
| Bruno Fernando      |         2019 |           34 |                               82.2 |               12.1 |               10   |                2.5 |
