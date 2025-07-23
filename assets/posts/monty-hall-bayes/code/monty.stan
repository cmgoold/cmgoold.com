data {
    int <lower=0> N;
    array[N] int<lower=1, upper=3> contestant;
    array[N] int<lower=1, upper=3> monty;
    array[N] int<lower=1, upper=3> car;
}

transformed data {
    int K = 3;
    array[K, K] row_vector[K] theta;

    // contestant = 1, car = k
    theta[1, 1] = [0.0, 0.5, 0.5];
    theta[1, 2] = [0.0, 0.0, 1.0];
    theta[1, 3] = [0.0, 1.0, 0.0];
    // contestant = 2, car = k
    theta[2, 1] = [0.0, 0.0, 1.0];
    theta[2, 2] = [0.5, 0.0, 0.5];
    theta[2, 3] = [1.0, 0.0, 0.0];
    // contestant = 3, car = k
    theta[3, 1] = [0.0, 1.0, 0.0];
    theta[3, 2] = [1.0, 0.0, 0.0];
    theta[3, 3] = [0.5, 0.5, 0.0];
}

transformed parameters {
    matrix[N, K] lps = rep_matrix(-log(K), N, K);
    vector[N] lp;

    for(i in 1:N) {
        for(k in 1:K) {
            lps[i, k] += log(theta[contestant[i], k, monty[i]]);
        }
        lp[i] = log_sum_exp(lps[i]);
    }
}

model {
    target += sum(lp);
}

generated quantities {
    matrix[N, K] z_probs;
    array[N] int<lower=1, upper=3> z;
    array[N] int<lower=0, upper=1> correct;

    for(i in 1:N) {
        z_probs[i] = softmax(lps[i]')';
        z[i] = categorical_rng(z_probs[i]');
        correct[i] = z[i] == car[i];
    }
}
