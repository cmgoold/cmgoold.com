from scipy.stats import norm, rv_discrete
import numpy as np

SEED = 1234
state = {"random_state": SEED}

def max_lik(y: list[float], mu_grid: list[float], sigma: float):
    log_liks = norm(mu_grid, [sigma]*len(mu_grid)).logpdf(y[:,None]).sum(axis=0)

    return mu_grid[log_liks.argmax()]

def coverage(mu: float, sigma: float, N: int):
    S = 1000

    means: list[float] = []
    cis: list[tuple[float, float]] = []
    cover: list[bool] = []

    for _ in range(S):
        s = norm(mu, sigma).rvs(N)
        s_mu = s.mean()
        s_sigma = s.std(ddof=1)
        lower, upper = (
            s_mu - 1.96 * s_sigma/np.sqrt(N), 
            s_mu + 1.96 * s_sigma/np.sqrt(N),
        )
        means.append(s_mu)
        cis.append((lower, upper))
        cover.append(lower <= mu <= upper)

    return np.mean(cover)

def bayes(y: list[float], mu_grid: list[float], sigma: float, prior_mu: float, prior_sigma: float):
    log_liks = norm(mu_grid, [sigma]*len(mu_grid)).logpdf(y[:,None]).sum(axis=0)

    log_prior = norm(prior_mu, prior_sigma).logpdf(mu_grid)

    log_post = log_liks + log_prior

    posterior_raw = np.exp(log_post)
    posterior = posterior_raw / posterior_raw.sum()

    return rv_discrete(values=(mu_grid, posterior)).rvs(size=1_000, **state)

def main():
    N = 100
    mu = 64.0
    sigma = 10.0

    y = norm(mu, sigma).rvs(N, **state)
    lower, upper = (
        y.mean() - 1.96 * sigma/np.sqrt(N), 
        y.mean() + 1.96 * sigma/np.sqrt(N),
    )
    print(y.mean(), (lower, upper))

    mu_grid = np.linspace(0, 150, 10_000)
    mu_hat = max_lik(y, mu_grid, sigma)
    cov = coverage(mu, sigma, N)
    print(cov)

    posterior = bayes(y, mu_grid, sigma, 60, 20)
    lower, upper = np.quantile(posterior, (0.025, 0.975))
    print(posterior.mean(), (lower, upper))

    posterior = bayes(y, mu_grid, sigma, 65, 1)
    lower, upper = np.quantile(posterior, (0.025, 0.975))
    print(posterior.mean(), (lower, upper))

if __name__ == "__main__":
    main()
