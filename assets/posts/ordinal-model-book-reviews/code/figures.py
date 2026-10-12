from scipy.stats import norm, lognorm, poisson as _poisson
import numpy as np
import matplotlib.pyplot as plt
import json
from sim import kruschke_ordinal_rng
from arviz import hdi
import re

BACKGROUNDS = {
    "light": {
        "background": "#f9f8ef",
        "highlight": "#e35336",
        "blue": "#227FA5",
        "edgecolors": "black",
    },
    "dark": {
        "background": "#0f141a",
        "highlight": "#04da75",
        "blue": "#82C8E5",
        "edgecolors": "#c5c5c5",
    },
}

hierarchical_intercepts = json.load(
    open("posteriors/hierarchical-intercepts-summary.json")
)
complete_pooling = json.load(open("posteriors/complete-pooling-summary.json"))
linear = json.load(open("posteriors/linear-hierarchical-intercepts-summary.json"))
poisson = json.load(open("posteriors/poisson-hierarchical-intercepts-summary.json"))
models = [hierarchical_intercepts, complete_pooling, linear, poisson]

def threshold_example():
    grid = np.linspace(-5, 10, 1000)
    xticks = [-5, 1, 2, 3, 4, 5, 10]
    theta = [1.5, 2.5, 3.5, 4.5]
    style = f"blog.light.mplstyle"
    R = 3
    C = 2
    rc = [(r, c) for r in range(R) for c in range(C)]
    mu_sigmas = [
        (mu, sigma)
        for mu, sigma in zip([3.5, 3.5, -2, -2, 8, 8], [1.0, 4.0, 1.0, 4.0, 1.0, 4.0])
    ]
    for background, colors in BACKGROUNDS.items():
        if background.lower() == "dark":
            style = [style, style.replace("light", "dark")]
        with plt.style.context(style, after_reset=True):
            figsize = 6, 5
            fig, ax = plt.subplots(R, C, figsize=figsize)
            for plt_idx, (r, c) in enumerate(rc):
                mu, sigma = mu_sigmas[plt_idx]
                pi, sims = kruschke_ordinal_rng(
                    theta, mu, sigma, n=500, rng=np.random.default_rng(1234)
                )
                ax[r, c].plot(
                    grid,
                    norm(mu, sigma).cdf(grid),
                    lw=1,
                    color=colors["highlight"],
                    label="cdf",
                )
                ax[r, c].plot(grid, norm(mu, sigma).pdf(grid), lw=1, label="pdf")
                for idx, i in enumerate(theta):
                    ax[r, c].axvline(
                        i, ls=":", color="darkgray", label=None if idx else r"$\theta$"
                    )
                ax[r, c].errorbar(
                    np.mean(sims),
                    0.8,
                    xerr=np.std(sims),
                    fmt="o",
                    color=colors["blue"],
                    label=r"$\hat{y}$",
                )
                ax[r, c].bar([1, 2, 3, 4, 5], pi, width=0.2, label="y")
                ax[r, c].set_xticks(xticks)
                ax[r, c].set_xticklabels(xticks)
                if not plt_idx:
                    ax[r, c].legend(frameon=False, loc="upper left", fontsize="8")
                ax[r, c].set_ylim([0, 1.1])
                if c == 0:
                    ax[r, c].set_yticks([0, 1])
                    ax[r, c].set_yticklabels([0, 1])
                else:
                    ax[r, c].set_yticks([])
                    ax[r, c].set_yticklabels([])
                ax[r, c].set_title(rf"$\mu = {mu}$, $\sigma = {sigma}$", fontsize="8")
            fig.supylabel("p(y)")
            fig.supxlabel(r"$y$ on $z$")
            plt.savefig(f"../static/threshold-example-{background}.png")
            plt.close()

def book_1_differences():
    style = f"blog.light.mplstyle"
    R = 1
    C = 1
    for background, colors in BACKGROUNDS.items():
        if background.lower() == "dark":
            style = [style, style.replace("light", "dark")]
        with plt.style.context(style, after_reset=True):
            figsize = 6, 4
            fig, ax = plt.subplots(R, C, figsize=figsize)
            model = hierarchical_intercepts
            ax.axvline(0, lw=0.25, color="darkgray", ls=":")
            mean_ranks = np.argsort([v["eta_mean"] for v in model.values()])[-10:]
            top_book = list(model.values())[mean_ranks[-1]]
            for i, r in enumerate(mean_ranks):
                k, v = list(model.items())[r]
                posterior_diff = np.array(v["eta_samples"]) - top_book["eta_samples"]
                ranks, counts = np.unique(v["posterior_rank"], return_counts=True)
                rank = ranks[counts.argsort()[-1]]
                x = np.mean(
                    np.array(v["eta_samples"]) - np.array(top_book["eta_samples"])
                )
                y = 1 + i #v["train_rank"] + 1 #v["eta_mean"]
                lower, upper = min(posterior_diff), max(posterior_diff)
                lower05, upper95 = np.quantile(posterior_diff, (0.05, 0.95))
                ax.plot([lower, upper], 2 * [y], lw=0.3)
                ax.plot([lower05, upper95], 2 * [y], lw=0.8)
                ax.scatter(x, y, s=5, fc="none", ec=colors["edgecolors"], lw=0.5)
                clean_title = re.sub(r"\([^)]*\)", "", v["title"]).strip()
                ax.text(0.2, y, clean_title, fontsize="6", va="center")
            xticks = [-0.5, 0, 0.5]
            yticks = [i for i in list(range(1, 11, 1))]
            ax.set_yticks(yticks)
            ax.set_yticklabels(yticks[::-1])
            ax.set_xticks(xticks)
            ax.set_xticklabels(xticks)
            ax.set_ylabel(r"$R(\hat{\mu})$")
            ax.set_xlabel(r"$R(\mu_{1}) - R(\mu_{i})$")
            ax.set_title("The Hunger Games vs top 10 books", fontsize="10", loc="left")
            plt.savefig(f"../static/top-100-differences-{background}.png")
            plt.close()


def top_100_ranks():
    style = f"blog.light.mplstyle"
    R = 1
    C = 1
    for background, colors in BACKGROUNDS.items():
        if background.lower() == "dark":
            style = [style, style.replace("light", "dark")]
        with plt.style.context(style, after_reset=True):
            figsize = 5, 8
            fig, ax = plt.subplots(R, C, figsize=figsize)
            model = hierarchical_intercepts
            ax.axvline(0, lw=0.25, color="darkgray", ls=":")
            mean_ranks = np.argsort([v["eta_mean"] for v in model.values()])
            for i, r in enumerate(mean_ranks):
                k, v = list(model.items())[r]
                posterior_diff = np.array(v["posterior_rank"]) - v["train_rank"]
                ranks, counts = np.unique(v["posterior_rank"], return_counts=True)
                rank = ranks[counts.argsort()[-1]]
                x = i - v["train_rank"]
                y = 1 + i
                lower, upper = min(posterior_diff), max(posterior_diff)
                lower05, upper95 = np.quantile(posterior_diff, (0.05, 0.95))
                ax.plot([lower, upper], 2 * [y], lw=0.3)
                ax.plot([lower05, upper95], 2 * [y], lw=0.8)
                ax.scatter(x, y, s=5, fc="none", ec=colors["edgecolors"], lw=0.5)
                clean_title = re.sub(r"\([^)]*\)", "", v["title"]).strip()
                ax.text(upper + 1, y, clean_title, fontsize="5", va="center")
            ticks = [i for i in list(range(1, 101, 9))]
            ax.set_yticks(ticks)
            ax.set_yticklabels(ticks[::-1], fontsize="5")
            ax.set_xticks([-30, 0, 30])
            ax.set_xticklabels([-30, 0, 30], fontsize="5")
            ax.set_ylabel(r"$R(\hat{\mu})$")
            ax.set_xlabel(r"$R(\mu) - R(\hat{y})$")
            ax.set_title("Top 100 books' posterior rankings", fontsize="10", loc="left")
            plt.savefig(f"../static/top-100-ranges-{background}.png")
            plt.close()

def top_100_scatter():
    style = f"blog.light.mplstyle"
    R = 1
    C = 1
    ticks = [1, 20, 40, 60, 80, 100]
    for background, colors in BACKGROUNDS.items():
        if background.lower() == "dark":
            style = [style, style.replace("light", "dark")]
        with plt.style.context(style, after_reset=True):
            figsize = 6, 4
            fig, ax = plt.subplots(R, C, figsize=figsize)
            ax.grid(linewidth=0.25, linestyle=":")
            ax.errorbar(
                [r["eta_mean"] for r in hierarchical_intercepts.values()],
                [r["train_rank"] for r in hierarchical_intercepts.values()],
                xerr=[r["eta_sd"]*2 for r in hierarchical_intercepts.values()],
                markersize=3,
                markerfacecolor="none",
                lw=0.5,
                fmt="o",
            )
            ax.set_ylabel("train rank")
            ax.set_xlabel(r"$\hat{\mu}$")
            ax.set_yticks(ticks)
            ax.set_yticklabels(ticks[::-1])
            ax.set_title("Top 100 books' latent means by average rating", fontsize="10", loc="left")
            plt.savefig(f"../static/top-100-scatter-{background}.png")
            plt.close()


def plot_book(index: str, name: str):
    grid = np.linspace(-5, 10, 1000)
    xticks = [-5, 1, 2, 3, 4, 5, 10]
    theta = [1.5, 2.5, 3.5, 4.5]
    R = 4
    C = 1
    rc = [(r, c) for r in range(R) for c in range(C)]
    style = f"blog.light.mplstyle"
    for background, colors in BACKGROUNDS.items():
        if background.lower() == "dark":
            style = [style, style.replace("light", "dark")]
        with plt.style.context(style, after_reset=True):
            figsize = 6, 4
            fig, ax = plt.subplots(R, C, figsize=figsize)
            for i, (r, c) in enumerate(rc):
                mean_ranks = np.argsort([v["eta_mean"] for v in models[i].values()])
                model = models[i][index]
                post_rank = 100 - [i for i, r in enumerate(mean_ranks) if str(r + 1) == index][0]
                raw_probs = sorted({rr["rating"]: rr["count"] / model["train_len"] for rr in model["value_counts"]}.items(), key=lambda k: k[0], reverse=False)
                ax[r].bar(*zip(*raw_probs), width=0.2)
                if i in (0, 1):
                    samples = np.asarray([
                        norm(mu, sigma).pdf(grid)
                        for mu, sigma
                        in zip(model["eta_samples"], model["sigma_samples"])
                    ])
                elif i == 2:
                    samples = np.asarray([
                        lognorm(scale=np.exp(mu), s=sigma).pdf(grid)
                        for mu, sigma
                        in zip(model["eta_samples"], model["sigma_samples"])
                    ])
                else:
                    samples = np.asarray([
                        _poisson(np.exp(mu)).pmf(range(1, 11))
                        for mu
                        in model["eta_samples"]
                    ])
                for sample in samples:
                    if i < 3:
                        ax[r].plot(grid, sample, lw=0.1, color=colors["blue"])
                if i == 3:
                    offsets = np.arange(1, 11) - 0.3
                    ax[r].bar(offsets, samples.mean(axis=0), width=0.25, color=colors["blue"])
                pp_probs = np.asarray(model["posterior_predictive_probs"])
                if np.all(pp_probs):
                    pp_probs_mean = pp_probs.mean(axis=0)
                    errors = abs(np.quantile(pp_probs - pp_probs_mean, (0.025, 0.975), axis=0))
                    ax[r].errorbar(
                        [1, 2, 3, 4, 5],
                        pp_probs_mean,
                        yerr=errors,
                        fmt="o",
                        markersize=3,
                        markeredgewidth=0.5,
                        color=colors["highlight"],
                        
                    )
                ax[r].set_yticks([0, 0.2, 0.4, 0.6])
                ax[r].set_yticklabels([0, 0.2, 0.4, 0.6])
                ax[r].set_xticks([-5, 1, 2, 3, 4, 5, 10])
                if r == R - 1:
                    ax[r].set_xticklabels([-5, 1, 2, 3, 4, 5, 10])
                else:
                    ax[r].set_xticklabels([])
                ax[r].text(
                    8, 0.4,
                    "hierarchical ordinal" if not i
                    else "complete-pooling ordinal" if i == 1
                    else "hierarchical lognormal" if i == 2
                    else "hierarchical poisson",
                    fontsize=6,
                    verticalalignment="center",
                )
                if not r:
                    ax[r].text(
                        -5, 0.4,
                        (
                            model["title"] + "\n" +
                            "train sample rank: " + str(model["train_rank"]) + "\n" +
                            "posterior rank: " + str(post_rank) + "\n" +
                            "train N: " + str(model["train_len"]) + "\n" +
                            "lp (train): " + str(round(model["lp_train_sum"], 2)) + "\n" +
                            "lp (test): " + str(round(model["lp_test_sum"], 2))
                        ),
                        fontsize=6,
                        verticalalignment="center",
                        horizontalalignment="left",
                    )
                else:
                    ax[r].text(
                        -5, 0.4,
                        (
                            "posterior rank: " + str(post_rank) + "\n" +
                            "lp (train): " + str(round(model["lp_train_sum"], 2)) + "\n" +
                            "lp (test): " + str(round(model["lp_test_sum"], 2))
                        ),
                        fontsize=6,
                        verticalalignment="center",
                        horizontalalignment="left",
                    )
                ax[r].set_xlim(-6, 11)
            fig.supylabel("p(y)")
            fig.supxlabel(r"$y$")
            plt.savefig(f"../static/{name}-{background}.png")
            plt.close()

def main():
    threshold_example()
    top_100_scatter()
    top_100_ranks()
    book_1_differences()
    plot_book("42", "jane-eyre")
    plot_book("98", "steve-jobs")


main()
