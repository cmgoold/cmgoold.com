data {
    int<lower=1> n;
    int<lower=0> k;
    real<lower=0, upper=1> pi_;
    real<lower=0, upper=1> gamma;
}

parameters {
    real<lower=0, upper=1> z;
}

transformed parameters {
    real<lower=0, upper=1> z_star = pi_ * z + (1 - gamma) * z;
}

model {
    z ~ beta(5.5, 24.5);
    target += binomail_lpmf(k | n, z_star);
}
