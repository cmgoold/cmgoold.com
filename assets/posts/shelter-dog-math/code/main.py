import cmdstanpy as csp
import matplotlib.pyplot as plt
import pymc as pm

BACKGROUNDS = {
    "light": {
        "background": "#f9f8ef",
    },
    "dark": {
        "background": "#0f141a",
    },
}


severity_fixed = csp.CmdStanModel(stan_file="latent-severity.stan")
severity_continuous = csp.CmdStanModel(stan_file="continuous-severity.stan")

def fixed_severity():
    fit = severity_fixed.sample(
        data={"n": 1, "k": 1, "pi_": 0.85, "gamma": 0.85, "mu": 0.16, "nu": 10},
        seed=1234,
    )
    style = f"blog.light.mplstyle"
    ylim = (0, 6)
    for background, colors in BACKGROUNDS.items():
        if background.lower() == "dark":
            style = [style, style.replace("light", "dark")]
        with plt.style.context(style, after_reset=True):
            fig, ax = plt.subplots(1, 2, sharey=True, constrained_layout=True)
            z = fit.p_z.T[0]
            theta = fit.theta
            mean = z.mean()
            hdi_z = pm.hdi(z, 0.95)
            hdi_theta = pm.hdi(theta, 0.95)
            ax[0].hist(z, bins=20, density=True)
            ax[0].plot(
                hdi_z,
                [0.1, 0.1],
                lw=2,
                color="blue",
                label="95% HDI",
            )
            ax[0].set_ylabel("density")
            ax[0].set_xlabel(r"$p(z \mid n, k)$")
            ax[0].legend(frameon=False)
            ax[1].hist(theta, bins=20, density=True)
            ax[1].plot(
                hdi_theta,
                [0.1, 0.1],
                lw=2,
                color="blue",
                label="95% HDI",
            )
            ax[1].set_xlabel(r"$\theta$")
            plt.savefig(
                f"../static/fixed-severity-{background}.png",
            )
            plt.close()
    print("latent fixed severity: ", mean, hdi_z)

def continuous_severity():
    fit = severity_continuous.sample(
        data={"n": 1, "k": 1, "pi_": 0.85, "gamma": 0.85, "mu": 0.16, "nu": 10},
        seed=1234,
    )
    style = f"blog.light.mplstyle"
    ylim = (0, 6)
    for background, colors in BACKGROUNDS.items():
        if background.lower() == "dark":
            style = [style, style.replace("light", "dark")]
        with plt.style.context(style, after_reset=True):
            fig, ax = plt.subplots(1, 2, sharey=True, constrained_layout=True)
            z = fit.p_z
            z_star = fit.z_star
            mean = z.mean()
            hdi_z = pm.hdi(z, 0.95)
            hdi_z_star = pm.hdi(z_star, 0.95)
            ax[0].hist(z, bins=20, density=True)
            ax[0].plot(
                hdi_z,
                [0.1, 0.1],
                lw=2,
                color="blue",
                label="95% HDI",
            )
            ax[0].set_ylabel("density")
            ax[0].set_xlabel(r"$p(z \mid n, k)$")

            ax[1].hist(z_star, bins=20, density=True)
            ax[1].plot(
                hdi_z_star,
                [0.1, 0.1],
                lw=2,
                color="blue",
                label="95% HDI",
            )
            ax[1].set_xlabel(r"$z^{*}$")
            ax[0].legend(frameon=False)
            plt.savefig(
                f"../static/continuous-severity-{background}.png",
            )
            plt.close()
    print("latent continuous severity: ", mean, hdi_z)


def main():
    fixed_severity()
    continuous_severity()


if __name__ == "__main__":
    main()
