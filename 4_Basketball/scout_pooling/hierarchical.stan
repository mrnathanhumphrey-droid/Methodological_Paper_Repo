// Hierarchical partial-pooling fit per PRE_REG_SCOUTS_v1.md §4.2.
//
// edge(S, C) ~ Normal(mu_S + nu_C + gamma_{S,C}, sigma_obs)
// mu_S      ~ Normal(0, tau_scout)
// nu_C      ~ Normal(0, tau_cell)
// gamma     ~ Normal(0, tau_interaction)         // specialist term
//
// Observation noise sigma_obs absorbs Fisher-SE of the correlation estimate
// (per pre-reg §4.1) plus residual unmodelled noise.
//
// F1 maps to posterior(tau_interaction): if τ_interaction concentrates
// near zero, specialists do not have cell-specific edge structure.

data {
  int<lower=1> N;                   // n observed (scout, cell) edge values
  int<lower=1> n_scout;
  int<lower=1> n_cell;
  array[N] int<lower=1, upper=n_scout> scout_idx;
  array[N] int<lower=1, upper=n_cell> cell_idx;
  vector[N] edge;                   // observed edge value (Pearson r in [-1, 1])
  vector<lower=0>[N] fisher_se;     // observation SE per pre-reg §4.1 (1/sqrt(n-3))
}

parameters {
  vector[n_scout] mu_s_raw;
  vector[n_cell] nu_c_raw;
  matrix[n_scout, n_cell] gamma_raw;
  real<lower=0> tau_scout;
  real<lower=0> tau_cell;
  real<lower=0> tau_interaction;
  real<lower=0> sigma_extra;        // residual noise beyond Fisher SE
}

transformed parameters {
  vector[n_scout] mu_s = tau_scout * mu_s_raw;
  vector[n_cell] nu_c = tau_cell * nu_c_raw;
  matrix[n_scout, n_cell] gamma = tau_interaction * gamma_raw;
}

model {
  // Weakly informative priors on scale parameters
  tau_scout ~ normal(0, 0.5);
  tau_cell ~ normal(0, 0.5);
  tau_interaction ~ normal(0, 0.5);
  sigma_extra ~ normal(0, 0.3);

  // Non-centered parameterization (helps NUTS convergence with small n)
  mu_s_raw ~ std_normal();
  nu_c_raw ~ std_normal();
  to_vector(gamma_raw) ~ std_normal();

  // Likelihood: observation noise = sqrt(fisher_se^2 + sigma_extra^2)
  for (i in 1:N) {
    real noise = sqrt(square(fisher_se[i]) + square(sigma_extra));
    edge[i] ~ normal(mu_s[scout_idx[i]] + nu_c[cell_idx[i]]
                      + gamma[scout_idx[i], cell_idx[i]], noise);
  }
}

generated quantities {
  // Per-cell predicted edge under model (excludes residual sigma)
  vector[N] edge_pred;
  for (i in 1:N) {
    edge_pred[i] = mu_s[scout_idx[i]] + nu_c[cell_idx[i]]
                    + gamma[scout_idx[i], cell_idx[i]];
  }
}
