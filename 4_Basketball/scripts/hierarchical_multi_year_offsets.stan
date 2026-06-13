// Hierarchical multi-year residual-offset model.
//
// For each (stat, class, class_value, year), we have a per-player residual
// from the v4-lite-tq_g audit. The model pools class effects across years
// with appropriate shrinkage:
//
//   residual[i] = mu_class[c[i]] + delta_class_year[c[i], y[i]] + e[i]
//   delta_class_year[c, y] ~ Normal(0, tau_class[c])
//   e[i] ~ Normal(0, sigma_class[c[i]])
//
// Cross-year-stable classes have small tau_class (delta_class_year shrinks
// to zero, mu_class is the shipped offset). Year-specific classes have large
// tau_class (delta_class_year stays large per year, mu_class shrinks toward
// zero — gets filtered out).
//
// At ship time, use posterior_mean(mu_class) as the offset, weighted by the
// "stability fraction" 1 - tau_class^2 / (tau_class^2 + sigma_class^2 / N_c)
// to discount unstable classes.

data {
  int<lower=1> N;                  // total observations (player-seasons)
  int<lower=1> n_classes;          // number of distinct (class_name × class_value) cells
  int<lower=1> n_years;            // number of seasons in pool
  array[N] int<lower=1, upper=n_classes> class_idx;
  array[N] int<lower=1, upper=n_years> year_idx;
  vector[N] residual;
}

parameters {
  vector[n_classes] mu_class;       // grand-mean offset per class
  matrix[n_classes, n_years] z_class_year;  // standardized year-deviations
  vector<lower=0>[n_classes] tau_class;     // cross-year SD of class effect
  vector<lower=0>[n_classes] sigma_class;   // residual SD per class
}

transformed parameters {
  matrix[n_classes, n_years] delta_class_year;
  for (c in 1:n_classes)
    for (y in 1:n_years)
      delta_class_year[c, y] = tau_class[c] * z_class_year[c, y];
}

model {
  // Priors
  mu_class ~ normal(0, 5);          // class-level grand mean (broad)
  to_vector(z_class_year) ~ normal(0, 1);
  tau_class ~ normal(0, 2);         // half-normal cross-year SD prior
  sigma_class ~ normal(0, 5);       // half-normal residual SD prior

  // Likelihood
  for (i in 1:N) {
    residual[i] ~ normal(
      mu_class[class_idx[i]] + delta_class_year[class_idx[i], year_idx[i]],
      sigma_class[class_idx[i]]
    );
  }
}

generated quantities {
  // Stability fraction per class: 1 means perfectly stable (tau small),
  // 0 means year-specific noise (tau large vs sigma)
  vector[n_classes] stability_fraction;
  for (c in 1:n_classes) {
    real var_year = tau_class[c]^2;
    real var_resid = sigma_class[c]^2;
    stability_fraction[c] = var_resid / (var_resid + var_year);
  }
}
