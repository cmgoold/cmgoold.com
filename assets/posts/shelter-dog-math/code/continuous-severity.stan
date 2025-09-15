data {
    int<lower=1> n;
    int<lower=0> k;
    real<lower=0, upper=1> pi_;
    real<lower=0, upper=1> gamma;
    real<lower=0, upper=1> mu;
    real<lower=0> nu;
}

parameters {
    real<lower=0, upper=1> theta;
    real z;
}

transformed parameters {
    real<lower=0, upper=1> z_star = pi_ * inv_logit(z) + (1 - gamma) * (1 - inv_logit(z));
}

model {
    theta ~ beta(mu * nu, (1 - mu) * nu);
    z ~ normal(logit(theta), 0.25);
    target += binomial_lpmf(k | n, z_star);
}

generated quantities {
    real<lower=0, upper=1> p_z = pi_ * inv_logit(z) / z_star;
}
