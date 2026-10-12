import numpy as np
from cmdstanpy import CmdStanModel
from scipy.stats import norm


def kruschke_ordinal_rng(
    theta: list[float],
    mu: float,
    sigma: float,
    rng: np.random.Generator | None = None,
    n: int | None = None,
) -> tuple[list[float], list[int]]:
    """Simulate from Kruschke's (2014) ordered-probit"""
    if rng is None:
        rng = np.random.default_rng()
    K = len(theta) + 1
    thetab = np.array([-np.inf] + [*theta] + [np.inf])
    pi = norm.cdf((thetab[1:] - mu) / sigma) - norm.cdf((thetab[:-1] - mu) / sigma)
    if n is None:
        sims = rng.choice(range(1, K + 1, 1), p=pi)
    else:
        sims = rng.choice(range(1, K + 1, 1), size=n, p=pi)
    return pi, sims


rng = np.random.default_rng(1234)

M = 100
P = 10
N = M * P
K = 5
J = K - 1
L = 1.5
U = 4.5
m = [i for i in range(M) for _ in range(P)]
p = [i for _ in range(M) for i in range(P)]
tau = 0.5
delta = 0.25
nu = norm.rvs(size=M) * tau
psi = norm.rvs(size=P) * delta
mu = 0
sigma = 5
theta = np.arange(L, U + 1)
eta = mu + nu[m] + psi[p]
_, y = zip(*[kruschke_ordinal_rng(theta, mu, sigma, rng) for _ in range(N)])

def fit_models():
    model = CmdStanModel(stan_file="stan/hierarchical-intercepts.stan")
    simple = CmdStanModel(stan_file="stan/complete-pooling.stan")

    fit = model.sample(
        data={
            "N": N,
            "L": L,
            "U": U,
            "K": K,
            "M": M,
            "P": P,
            "p": [i + 1 for i in p],
            "m": [i + 1 for i in m],
            "y": np.asarray(y),
            "T": 0,
            "m_test": [],
            "p_test": [],
        },
        iter_warmup=1000,
        iter_sampling=1000,
        chains=4,
        inits=0,
    )

    fit = simple.sample(
        data={
            "N": N,
            "L": L,
            "U": U,
            "K": K,
            "y": y,
        },
        iter_warmup=1000,
        iter_sampling=1000,
        chains=4,
    )
