import numpy as np
from cmdstanpy import CmdStanModel
from collections import namedtuple
import matplotlib.pyplot as plt

SEED = 1234
rng = np.random.default_rng(SEED)

BACKGROUNDS = {
    "light": {
        "background": "#f9f8ef",
    },
    "dark": {
        "background": "#0f141a",
    },
}


MontyHall = namedtuple("MontyHall", ("car", "contestant", "monty", "switch", "correct"))

monty = CmdStanModel(stan_file="monty.stan")


def simulate_monty_hall() -> MontyHall:
    doors = [1, 2, 3]
    car = rng.choice(doors)
    contestant = rng.choice(doors)
    monty = rng.choice(
        [
            d 
            for d 
            in doors 
            if d != contestant and d != car
        ]
    )
    switch = [
        d 
        for d 
        in doors 
        if d != contestant and d != monty
    ][0]
    return MontyHall(car, contestant, monty, switch, switch == car)


def main():
    N = 1000
    sims = [simulate_monty_hall() for _ in range(N)]
    fit = monty.sample(
        data={
            "N": N,
            "contestant": [sim.contestant for sim in sims],
            "monty": [sim.monty for sim in sims],
            "car": [sim.car for sim in sims],
        },
        seed=1234,
    )

    
    style = f"blog.light.mplstyle"
    for background, colors in BACKGROUNDS.items():
        if background.lower() == "dark":
            style = [style, style.replace("light", "dark")]
        with plt.style.context(style, after_reset=True):
            R, C = 4, 4
            figsize = 6, 4
            fig, ax = plt.subplots(R, C, sharex=True, sharey=True, constrained_layout=True, figsize=figsize)
            rc = [(r, c) for r in range(R) for c in range(C)]
            bins = [1, 2, 3, 4]
            for i, (r, c) in enumerate(rc):
                heights, _ = np.histogram(fit.z.T[i], bins=bins)
                ax[r,c].bar(bins[:-1], heights)
                ax[r,c].set_title(f"car = {sims[i].car}\n contestant = {sims[i].contestant}\n monty = {sims[i].monty}", fontsize=8)
            fig.supylabel("Count")
            fig.supxlabel("Doors")
            plt.savefig(f"../static/posterior-z-{background}.png")
            plt.close()

    cars = np.array([sim.car for sim in sims])
    E_correct = np.median(fit.z, axis=0) == cars
    print(E_correct.mean(), np.mean([sim.correct for sim in sims]))


if __name__ == "__main__":
    main()
