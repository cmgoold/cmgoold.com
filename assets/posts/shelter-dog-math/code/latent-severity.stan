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
}

transformed parameters {
    vector[2] lp = [
        log(theta) + binomial_lpmf(k | n, pi_),
        log1m(theta) + binomial_lpmf(k | n, (1 - gamma))
    ]';
}

model {
    theta ~ beta(mu * nu, (1 - mu) * nu);
    target += log_sum_exp(lp);
}

generated quantities {
    vector[2] p_z = softmax(lp);
    real z = bernoulli_rng(p_z[1]);
}
