import numpy as np
import pymc as pm

rng = np.random.default_rng(1234)


def ilogit(x):
    return np.exp(x) / (1 + np.exp(x))


def common_causes():
    N = 5000
    sex = rng.binomial(1, 0.5, size=N)
    age = rng.lognormal(np.log(30), 0.2, N)

    sex_z = sex - 0.5
    age_z = (age - age.mean()) / age.std()

    immigration = rng.binomial(1, ilogit(sex_z + -0.5 * age_z))
    crime = rng.binomial(1, ilogit(-1 + sex_z + -0.5 * age_z))

    with pm.Model() as model:
        alpha = pm.Normal("alpha", 0, 10)
        beta = pm.Normal("beta", 0, 2)
        eta = pm.math.invlogit(alpha + beta * (immigration - 0.5))
        likelihood = pm.Binomial("crime", n=1, p=eta, observed=crime)
        idata = pm.sample(1000, tune=1000, random_seed=rng)

    print(
        "Wrong: ",
        (
            (idata.posterior.beta.mean(), pm.stats.hdi(idata.posterior.beta, 0.95)),
            (
                np.exp(idata.posterior.beta).mean(),
                pm.stats.hdi(np.exp(idata.posterior.beta), 0.95),
            ),
        ),
    )

    with pm.Model() as model:
        alpha = pm.Normal("alpha", 0, 10)
        beta0 = pm.Normal("beta0", 0, 2)
        beta1 = pm.Normal("beta1", 0, 2)
        beta2 = pm.Normal("beta2", 0, 2)
        eta = pm.math.invlogit(
            alpha + beta0 * (immigration - 0.5) + beta1 * sex_z + beta2 * age_z
        )
        likelihood = pm.Binomial("crime", n=1, p=eta, observed=crime)
        idata = pm.sample(1000, tune=1000, random_seed=rng)

    print(
        "Right: ",
        (
            (idata.posterior.beta0.mean(), pm.stats.hdi(idata.posterior.beta0, 0.95)),
            (
                np.exp(idata.posterior.beta0).mean(),
                pm.stats.hdi(np.exp(idata.posterior.beta0), 0.95),
            ),
        ),
    )


def collider_bias():
    N = 5000

    immigration = rng.binomial(1, 0.5, size=N)
    crime = rng.binomial(1, 0.5, size=N)
    prison = rng.binomial(1, ilogit(immigration + 2 * crime))

    immigration_in_prison = immigration[prison == 1]
    crime_in_prison = crime[prison == 1]

    with pm.Model() as model:
        alpha = pm.Normal("alpha", 0, 10)
        beta = pm.Normal("beta", 0, 2)
        eta = pm.math.invlogit(alpha + beta * (immigration_in_prison - 0.5))
        likelihood = pm.Binomial("crime", n=1, p=eta, observed=crime_in_prison)
        idata = pm.sample(1000, tune=1000, random_seed=rng)

    print(
        "Wrong: ",
        (
            (idata.posterior.beta.mean(), pm.stats.hdi(idata.posterior.beta, 0.95)),
            (
                (1 - np.exp(idata.posterior.beta)).mean(),
                pm.stats.hdi(1 - np.exp(idata.posterior.beta), 0.95),
            ),
        ),
    )

    with pm.Model() as model:
        alpha = pm.Normal("alpha", 0, 10)
        beta = pm.Normal("beta", 0, 2)
        eta = pm.math.invlogit(alpha + beta * (immigration - 0.5))
        likelihood = pm.Binomial("crime", n=1, p=eta, observed=crime)
        idata = pm.sample(1000, tune=1000, random_seed=rng)

    print(
        "Right: ",
        (
            (idata.posterior.beta.mean(), pm.stats.hdi(idata.posterior.beta, 0.95)),
            (
                np.exp(idata.posterior.beta).mean(),
                pm.stats.hdi(np.exp(idata.posterior.beta), 0.95),
            ),
        ),
    )


def main():
    common_causes()
    collider_bias()


if __name__ == "__main__":
    main()
