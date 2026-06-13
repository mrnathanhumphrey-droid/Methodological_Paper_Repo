# α calibration summary — PTS 2022-23

Train: 2019-20,2020-21,2021-22  ·  OOS_SD: 1.792  ·  n=199

**Locked config:** α=0.05, threshold=1.00×OOS_SD, gate=over_projection_only

## Top 10 by MAE (within coverage band)

```
 alpha  thresh_mult            direction  n_adjusted      mae     rmse     bias  coverage_50  coverage_80  coverage_90
  0.05          1.0 over_projection_only          15 1.978724 2.621822 0.115956     0.487437     0.753769     0.829146
  0.05          1.5 over_projection_only          13 1.979808 2.622105 0.114871     0.487437     0.753769     0.829146
  0.05          2.5 over_projection_only           9 1.980365 2.623648 0.110846     0.487437     0.753769     0.829146
  0.05          2.0 over_projection_only          12 1.980630 2.622927 0.114049     0.487437     0.753769     0.829146
  0.05          1.0                 both          45 1.981843 2.637902 0.062187     0.492462     0.738693     0.824121
  0.10          1.0 over_projection_only          15 1.982083 2.633385 0.136198     0.482412     0.753769     0.829146
  0.05          2.0                 both          34 1.983432 2.637238 0.065831     0.492462     0.738693     0.824121
  0.10          1.5 over_projection_only          13 1.983572 2.633903 0.134030     0.482412     0.753769     0.829146
  0.05          1.5                 both          40 1.983580 2.638616 0.062800     0.492462     0.738693     0.824121
  0.10          2.5 over_projection_only           9 1.983942 2.636663 0.125980     0.482412     0.753769     0.829146
```