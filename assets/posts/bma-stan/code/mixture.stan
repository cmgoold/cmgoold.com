data {
    int<lower=0> N;
    array[N] int<lower=0, upper=1> v;
}

transformed data {
    int<lower=0> K = 2;
    real<lower=0, upper=1> pi = 3.0 / N;
    vector<lower=0, upper=1>[K] theta = [0.05, 0.25]';
}

transformed parameters {
    vector[K] lp = [log(pi), log1m(pi)]';

    for(i in 1:N){
        for(k in 1:2)
            lp[k] += bernoulli_lpmf(v[i] | theta[k]);
    }
}

model {
    target += log_sum_exp(lp);
}

generated quantities {
    simplex[K] p_z;
    int<lower=0, upper=1> z;
    p_z = softmax(lp);
    z = bernoulli_rng(p_z[1]);
}
