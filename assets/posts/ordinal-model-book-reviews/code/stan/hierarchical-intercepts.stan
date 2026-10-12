functions {
    real ordered_probit_lpmf(int y, real mu, real sigma, vector theta) {
        int J = size(theta);
        int K = J + 1;
        vector[K] pi;
        pi[1] = Phi_approx( (theta[1] - mu) / sigma);
        pi[K] = 1 - Phi_approx( (theta[J] - mu) / sigma);
        pi[2:J] = (
            Phi_approx( (theta[2:J] - mu) / sigma ) -
            Phi_approx( (theta[1:J-1] - mu) / sigma )
        );
        return categorical_lupmf(y | pi);
    }
}

data {
    int<lower=0> N;
    int<lower=0> T;
    real L;
    real<lower=L> U;
    int<lower=1> K;
    int<lower=1> M;
    int<lower=1> P;
    array[N] int<lower=1, upper=M> m;
    array[N] int<lower=1, upper=P> p;
    array[T] int<lower=0> m_test;
    array[T] int<lower=0> p_test;
    array[N] int<lower=1, upper=K> y;
    array[T] int<lower=1, upper=K> y_test;
}

transformed data {
    int<lower=1> J = K - 1;
}

parameters {
    simplex[J - 1] theta_star;
    real mu;
    vector[M] z_m;
    vector[P] z_p;
    real<lower=0> sigma;
    real<lower=0> tau;
    real<lower=0> delta;
}

transformed parameters {
    vector[N] lp;
    positive_ordered[J] theta;
    theta[1] = L;
    theta[2:J] = L + (U - L) * cumulative_sum(theta_star);

    {
        vector[N] eta = mu + tau * z_m[m] + delta * z_p[p];
        for(n in 1:N) {
            lp[n] = ordered_probit_lpmf(y[n] | eta[n], sigma, theta);
        }
    }
}

model {
    mu ~ normal(0, 10);
    sigma ~ normal(0, 10);
    z_m ~ std_normal();
    z_p ~ std_normal();
    tau ~ std_normal();
    delta ~ std_normal();
    target += sum(lp);
}

generated quantities {
    vector[T] lp_test;

    for(t in 1:T) {
        real zeta = mu;
        if(m_test[t] > 0)
            zeta += tau * z_m[m_test[t]];
        if(p_test[t] > 0)
            zeta += delta * z_p[p_test[t]];
        lp_test[t] = ordered_probit_lpmf(y_test[t] | zeta, sigma, theta);
    }
}
