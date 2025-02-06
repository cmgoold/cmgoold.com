from argparse import ArgumentParser
import matplotlib.pyplot as plt
import numpy as np
import pymc as pm
import statsmodels.api as sm
from typing import Optional

BACKGROUNDS = {
    "light": {
        "background": "#f9f8ef",
    },
    "dark": {
        "background": "#0f141a",
    },
}

SEED = 1234
RNG = np.random.default_rng(SEED)


def ilogit(x: np.ndarray) -> np.ndarray:
    return np.array([1 / (1 + np.exp(-i)) for i in x])


def sim_domestication_hypothesis(N: int, n: int, rng: Optional[np.random.Generator] = None):
    if rng is None:
        rng = RNG
    b_sw_w = 0
    b_sw_d = 3.5
    b_sp_w = 0.5
    b_sp_d = 1.3

    S = rng.binomial(n=1, p=0.5, size=N)
    theta = ilogit(b_sw_d * S + b_sw_w * (1 - S))
    W = rng.binomial(n=1, p=theta)
    pi = ilogit(b_sp_d * S + b_sp_w * (1 - S))
    P = rng.binomial(n=n, p=pi)

    return b_sw_w, b_sw_d, b_sp_w, b_sp_d, S, W, P


def sim_developmental_hypothesis(N: int, n: int, rng: Optional[np.random.Generator] = None):
    if rng is None:
        rng = RNG
    b_sr_w = 0
    b_sr_d = 2
    b_rw_y = 3.5
    b_rw_n = 0
    b_wp_y = 1.3
    b_wp_n = 0.5

    S = rng.binomial(n=1, p=0.5, size=N)
    gamma = ilogit(b_sr_d * S + b_sr_w * (1 - S))
    R = rng.binomial(n=1, p=gamma)
    theta = ilogit(b_rw_y * R + b_rw_n * (1 - R))
    W = rng.binomial(n=1, p=theta)
    pi = ilogit(b_wp_y * W + b_wp_n * (1 - W))
    P = rng.binomial(n=n, p=pi)

    return b_sr_w, b_sr_d, b_rw_y, b_rw_n, b_wp_y, b_wp_n, S, R, W, P


def fit_regression(
    N: int,
    n: int,
    S: np.ndarray,
    W: np.ndarray,
    P: np.ndarray,
    R: Optional[np.ndarray] = None,
    species: bool = True,
    willingness: bool = True,
    rearing: bool = False,
    rng: Optional[np.random.Generator] = None,
):
    with pm.Model() as _:
        alpha = pm.Normal("alpha", mu=0, sigma=5)
        if species:
            beta_S = pm.Normal("beta_S", mu=0, sigma=1)
        if willingness:
            beta_W = pm.Normal("beta_W", mu=0, sigma=1)
        if rearing:
            beta_R = pm.Normal("beta_R", mu=0, sigma=1)
        eta_logit = alpha
        if species:
            eta_logit += beta_S * (S - 0.5)
        if willingness:
            eta_logit += beta_W * (W - 0.5)
        if rearing:
            eta_logit += beta_R * (R - 0.5)
        eta = pm.math.invlogit(eta_logit)
        log_lik = pm.Binomial("P", n=n, p=eta, observed=P)
        samples = pm.sample(1000, tune=1000, random_seed=rng or RNG)
        idata = pm.compute_log_likelihood(samples)

    return idata


def developmental_hypothesis_combined(N: int, n: int):
    b_sr_w, b_sr_d, b_rw_y, b_rw_n, b_wp_y, b_wp_n, S, R, W, P = (
        sim_developmental_hypothesis(N, n)
    )
    fit = fit_regression(N, n, S=S, W=W, P=P, R=None, species=True, willingness=True)
    elpd = pm.loo(fit).elpd_loo
    alpha = fit.posterior.alpha.values.flatten()
    beta_S = fit.posterior.beta_S.values.flatten()
    beta_W = fit.posterior.beta_W.values.flatten()

    style = f"blog.light.mplstyle"
    ylim = (0, 6)
    for background, colors in BACKGROUNDS.items():
        if background.lower() == "dark":
            style = [style, style.replace("light", "dark")]
        with plt.style.context(style, after_reset=True):
            fig, ax = plt.subplots(1, 2)
            ax[0].hist(beta_S, bins=20, density=True)
            ax[0].axvline(x=0, ls=":", label="true")
            ax[0].plot(
                pm.hdi(beta_S),
                [0.1, 0.1],
                lw=2,
                color="blue",
                label="94% HDI",
            )
            ax[0].set_ylabel("density")
            ax[0].set_xlabel(r"$\beta_{\mathrm{S}}$")
            ax[0].text(-0.3, ylim[1] + 1, f"ELPD: {elpd:.02f}")
            ax[0].legend(frameon=False, bbox_to_anchor=(0.7, 0.5))
            ax[0].set_ylim(ylim)
            ax[1].hist(beta_W, bins=20, density=True)
            ax[1].axvline(x=b_wp_y - b_wp_n, ls=":")
            ax[1].set_xlabel(r"$\beta_{\mathrm{W}}$")
            ax[1].plot(pm.hdi(beta_W), [0.1, 0.1], lw=2, color="blue")
            ax[1].set_ylim(ylim)
            plt.savefig(
                f"../static/developmental-hypothesis-{background}.png",
            )
            plt.close()


def developmental_hypothesis_separate(N: int, n: int):
    b_sr_w, b_sr_d, b_rw_y, b_rw_n, b_wp_y, b_wp_n, S, R, W, P = (
        sim_developmental_hypothesis(N, n)
    )
    fit_species = fit_regression(N, n, S=S, W=W, P=P, species=True, willingness=False)
    fit_willingness = fit_regression(
        N, n, S=S, W=W, P=P, species=False, willingness=True
    )
    elpd_species = pm.loo(fit_species).elpd_loo
    elpd_willingness = pm.loo(fit_willingness).elpd_loo

    beta_S = fit_species.posterior.beta_S.values.flatten()
    beta_W = fit_willingness.posterior.beta_W.values.flatten()

    style = f"blog.light.mplstyle"
    ylim = (0, 6)
    for background, colors in BACKGROUNDS.items():
        if background.lower() == "dark":
            style = [style, style.replace("light", "dark")]
        with plt.style.context(style, after_reset=True):
            fig, ax = plt.subplots(1, 2)
            ax[0].hist(beta_S, bins=20, density=True)
            ax[0].axvline(x=0, ls=":", label="true")
            ax[0].plot(
                pm.hdi(beta_S),
                [0.1, 0.1],
                lw=2,
                color="blue",
                label="94% HDI",
            )
            ax[0].set_ylabel("density")
            ax[0].set_xlabel(r"$\beta_{\mathrm{S}}$")
            ax[0].legend(frameon=False, bbox_to_anchor=(0.5, 0.7))
            ax[0].set_ylim(ylim)
            ax[0].text(-0.225, ylim[-1] + 1, f"ELPD: {elpd_species:.02f}")
            ax[1].hist(beta_W, bins=20, density=True)
            ax[1].axvline(x=b_wp_y - b_wp_n, ls=":")
            ax[1].set_xlabel(r"$\beta_{\mathrm{W}}$")
            ax[1].plot(pm.hdi(beta_W), [0.1, 0.1], lw=2, color="blue")
            ax[1].set_ylim(ylim)
            ax[1].text(0.3, ylim[-1] + 1, f"ELPD: {elpd_willingness:.02f}")
            plt.savefig(
                f"../static/developmental-hypothesis-separate-{background}.png",
            )
            plt.close()


def developmental_hypothesis_rearing(N: int, n: int):
    b_sr_w, b_sr_d, b_rw_y, b_rw_n, b_wp_y, b_wp_n, S, R, W, P = (
        sim_developmental_hypothesis(N, n)
    )
    fit = fit_regression(N, n, S=S, W=W, P=P, R=R, species=True, willingness=True, rearing=True)
    elpd = pm.loo(fit).elpd_loo
    beta_S = fit.posterior.beta_S.values.flatten()
    beta_W = fit.posterior.beta_W.values.flatten()
    beta_R = fit.posterior.beta_R.values.flatten()

    style = f"blog.light.mplstyle"
    ylim = (0, 6)
    for background, colors in BACKGROUNDS.items():
        if background.lower() == "dark":
            style = [style, style.replace("light", "dark")]
        with plt.style.context(style, after_reset=True):
            fig, ax = plt.subplots(1, 3)
            ax[0].hist(beta_S, bins=20, density=True)
            ax[0].axvline(x=0, ls=":", label="true")
            ax[0].plot(
                pm.hdi(beta_S),
                [0.1, 0.1],
                lw=2,
                color="blue",
                label="94% HDI",
            )
            ax[0].set_ylabel("density")
            ax[0].set_xlabel(r"$\beta_{\mathrm{S}}$")
            ax[0].text(-0.3, ylim[1] + 1, f"ELPD: {elpd:.02f}")
            ax[0].legend(frameon=False, bbox_to_anchor=(0.5, 0.7), fontsize=8)
            ax[0].set_ylim(ylim)
            ax[1].hist(beta_W, bins=20, density=True)
            ax[1].axvline(x=b_wp_y - b_wp_n, ls=":")
            ax[1].set_xlabel(r"$\beta_{\mathrm{W}}$")
            ax[1].plot(pm.hdi(beta_W), [0.1, 0.1], lw=2, color="blue")
            ax[1].set_ylim(ylim)
            ax[2].hist(beta_R, bins=20, density=True)
            ax[2].axvline(x=0, ls=":")
            ax[2].set_xlabel(r"$\beta_{\mathrm{R}}$")
            ax[2].plot(pm.hdi(beta_R), [0.1, 0.1], lw=2, color="blue")
            ax[2].set_ylim(ylim)
            plt.savefig(
                f"../static/developmental-hypothesis-rearing-{background}.png",
            )
            plt.close()

def domestication_hypothesis_combined(N: int, n: int):
    b_sw_w, b_sw_d, b_sp_w, b_sp_d, S, W, P = sim_domestication_hypothesis(N, n)
    fit = fit_regression(N, n, S, W, P, species=True, willingness=True)
    elpd = pm.loo(fit).elpd_loo
    beta_S = fit.posterior.beta_S.values.flatten()
    beta_W = fit.posterior.beta_W.values.flatten()

    style = f"blog.light.mplstyle"
    ylim = (0, 6)
    for background, colors in BACKGROUNDS.items():
        if background.lower() == "dark":
            style = [style, style.replace("light", "dark")]
        with plt.style.context(style, after_reset=True):
            fig, ax = plt.subplots(1, 2)
            ax[0].hist(beta_S, bins=20, density=True)
            ax[0].axvline(x=b_sp_d - b_sp_w, ls=":", label="true")
            ax[0].plot(
                pm.hdi(beta_S),
                [0.1, 0.1],
                lw=2,
                color="blue",
                label="94% HDI",
            )
            ax[0].set_ylabel("density")
            ax[0].set_xlabel(r"$\beta_{\mathrm{S}}$")
            ax[0].text(0.5, ylim[-1] + 1, f"ELPD: {elpd:.02f}")
            ax[0].legend(frameon=False, bbox_to_anchor=(0.5, 0.7))
            ax[0].set_ylim(ylim)
            ax[1].hist(beta_W, bins=20, density=True)
            ax[1].axvline(x=0, ls=":")
            ax[1].set_xlabel(r"$\beta_{\mathrm{W}}$")
            ax[1].plot(pm.hdi(beta_W), [0.1, 0.1], lw=2, color="blue")
            ax[1].set_ylim(ylim)
            plt.savefig(
                f"../static/domestication-hypothesis-{background}.png",
            )
            plt.close()


def domestication_hypothesis_separate(N: int, n: int):
    b_sw_w, b_sw_d, b_sp_w, b_sp_d, S, W, P = sim_domestication_hypothesis(N, n)
    fit_species = fit_regression(N, n, S, W, P, species=True, willingness=False)
    fit_willingness = fit_regression(N, n, S, W, P, species=False, willingness=True)
    elpd_species = pm.loo(fit_species).elpd_loo
    elpd_willingness = pm.loo(fit_willingness).elpd_loo
    alpha_S = fit_species.posterior.alpha.values.flatten()
    beta_S = fit_species.posterior.beta_S.values.flatten()
    beta_W = fit_willingness.posterior.beta_W.values.flatten()

    style = f"blog.light.mplstyle"
    ylim = (0, 6)
    for background, colors in BACKGROUNDS.items():
        if background.lower() == "dark":
            style = [style, style.replace("light", "dark")]
        with plt.style.context(style, after_reset=True):
            fig, ax = plt.subplots(1, 2)
            ax[0].hist(beta_S, bins=20, density=True)
            ax[0].axvline(x=b_sp_d - b_sp_w, ls=":", label="true")
            ax[0].plot(
                pm.hdi(beta_S),
                [0.1, 0.1],
                lw=2,
                color="blue",
                label="94% HDI",
            )
            ax[0].set_ylabel("density")
            ax[0].set_xlabel(r"$\beta_{\mathrm{S}}$")
            ax[0].legend(frameon=False, bbox_to_anchor=(0.5, 0.7))
            ax[0].set_ylim(ylim)
            ax[0].text(0.45, ylim[-1] + 1, f"ELPD: {elpd_species:.02f}")
            ax[1].hist(beta_W, bins=20, density=True)
            ax[1].axvline(x=0, ls=":")
            ax[1].set_xlabel(r"$\beta_{\mathrm{W}}$")
            ax[1].plot(pm.hdi(beta_W), [0.1, 0.1], lw=2, color="blue")
            ax[1].set_ylim(ylim)
            ax[1].text(-0.1, ylim[-1] + 1, f"ELPD: {elpd_willingness:.02f}")
            plt.savefig(
                f"../static/domestication-hypothesis-separate-{background}.png",
            )
            plt.close()

def power_analyses(M: int, N: list[int]) -> None:
    results = {}
    n = 6
    for N_star in N:
        for m in range(M):
            b_sw_w, b_sw_d, b_sp_w, b_sp_d, S, W, P = sim_domestication_hypothesis(N_star, n, rng=np.random.default_rng())
            fit = sm.GLM(np.array([P, n - P]).T, np.array([np.ones(N_star), W, S]).T, family=sm.families.Binomial()).fit()
            results[("domestication", N_star, m)] = dict(
                beta_W=fit.pvalues[1] > 0.05,
                beta_S=fit.pvalues[2] < 0.05,
            )

            b_sr_w, b_sr_d, b_rw_y, b_rw_n, b_wp_y, b_wp_n, S, R, W, P = (
                sim_developmental_hypothesis(N_star, n, rng=np.random.default_rng())
            )
            fit = sm.GLM(np.array([P, n - P]).T, np.array([np.ones(N_star), W, S, R]).T, family=sm.families.Binomial()).fit()
            results[("developmental", N_star, m)] = dict(
                beta_W=fit.pvalues[1] < 0.05,
                beta_S=fit.pvalues[2] > 0.05,
                beta_R=fit.pvalues[3] > 0.05,
            )

    style = f"blog.light.mplstyle"
    ylim = (0, 105)
    beta_W_domestication = [np.mean([
            r["beta_W"]
            for k, r in results.items()
            if k[0] == "domestication" and k[1] == n_star
        ]) * 100
        for n_star in N
    ]
    beta_S_domestication = [np.mean([
            r["beta_S"]
            for k, r in results.items()
            if k[0] == "domestication" and k[1] == n_star
        ]) * 100
        for n_star in N
    ]
    beta_W_developmental = [np.mean([
            r["beta_W"]
            for k, r in results.items()
            if k[0] == "developmental" and k[1] == n_star
        ]) * 100
        for n_star in N
    ]
    beta_S_developmental = [np.mean([
            r["beta_S"]
            for k, r in results.items()
            if k[0] == "developmental" and k[1] == n_star
        ]) * 100
        for n_star in N
    ]
    beta_R_developmental = [np.mean([
            r["beta_R"]
            for k, r in results.items()
            if k[0] == "developmental" and k[1] == n_star
        ]) * 100
        for n_star in N
    ]

    for background, colors in BACKGROUNDS.items():
        xlabels = [30, 50, 100, 200]
        if background.lower() == "dark":
            style = [style, style.replace("light", "dark")]
        with plt.style.context(style, after_reset=True):
            fig, ax = plt.subplots(1, 2)
            ax[0].plot(np.log(N), beta_W_domestication, label=r"$\beta_W$")
            ax[0].plot(np.log(N), beta_S_domestication, ls="dotted", label=r"$\beta_S$")
            ax[0].set_xticks(np.log(xlabels))
            ax[0].set_xticklabels(xlabels)
            ax[0].set_yticks([0, 20, 40, 60, 80, 100])
            ax[0].set_ylabel("True positive/\nnegative")
            ax[0].set_xlabel("Number of subjects")
            ax[0].set_ylim(ylim)
            ax[0].axhline(y=80, color="blue", label="80%", zorder=-1)
            ax[0].legend(frameon=False, loc="lower right")
            ax[0].set_title("Domestication hypothesis", fontsize=8, fontweight="bold", loc="left")
            ax[1].plot(np.log(N), beta_W_developmental, label=r"$\beta_W$")
            ax[1].plot(np.log(N), beta_S_developmental, ls="dotted", label=r"$\beta_S$")
            ax[1].plot(np.log(N), beta_R_developmental, ls="dashed", label=r"$\beta_R$")
            ax[1].set_xticks(np.log(xlabels))
            ax[1].set_xticklabels(xlabels)
            ax[1].set_yticks([0, 20, 40, 60, 80, 100])
            ax[1].set_xlabel("Number of subjects")
            ax[1].set_ylim(ylim)
            ax[1].axhline(y=80, color="blue", label="80%", zorder=-1)
            ax[1].legend(frameon=False, loc="lower right")
            ax[1].set_title("Developmental hypothesis", fontsize=8, fontweight="bold", loc="left")
            plt.savefig(
                f"../static/power-{background}.png",
            )
            plt.close()



def main():
    parser = ArgumentParser(description="Dogs, pointing, causal inference")
    parser.add_argument(
        "--power",
        action="store_true",
    )
    args = parser.parse_args()

    if args.power:
        power_analyses(M = 1000, N = [30, 50, 100, 150, 200])
    else:
        domestication_hypothesis_combined(500, 6)
        domestication_hypothesis_separate(500, 6)
        developmental_hypothesis_combined(500, 6)
        developmental_hypothesis_separate(500, 6)
        developmental_hypothesis_rearing(500, 6)


if __name__ == "__main__":
    main()
