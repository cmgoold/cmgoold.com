from argparse import ArgumentParser
from typing import Literal, Tuple
import numpy as np
import cmdstanpy as csp

Player = Literal["faithful", "traitor"]

SEED = 1234

PROBS = {"traitor": 0.05, "faithful": 0.25}

rng = np.random.default_rng(SEED)

mixture = csp.CmdStanModel(stan_file="mixture.stan")


def simulate(player: Player) -> Tuple[float, int]:
    v = []
    N = 10
    player = player.lower()
    z = int(player == "traitor")
    v = rng.binomial(n=1, size=N, p=PROBS[player])
    return v, z


def fit_mixture(v):
    fit = mixture.sample(data={"N": len(v), "v": v}, seed=SEED)
    return fit


def main(role: Player):
    v, z = simulate(role)
    fit = fit_mixture(v)
    return fit


if __name__ == "__main__":
    parser = ArgumentParser(description="Faithful or traitor?")
    parser.add_argument(
        "--role",
        type=str,
        default=None,
    )
    parser.add_argument(
        "--test",
        action="store_true",
    )
    args = parser.parse_args()

    if args.role is None and args.test:
        v = [0, 0, 1, 0, 1, 1, 0, 0, 0, 1]
        p_z_t = 3 / len(v) * 0.05 ** sum(v) * (1 - 0.05) ** (len(v) - sum(v))
        p_z_t /= p_z_t + (1 - 3 / len(v)) * 0.25 ** sum(v) * (1 - 0.25) ** (len(v) - sum(v))
        fit = fit_mixture(v)
        print(fit.summary())
        assert np.isclose(fit.p_z.T[0].mean(), p_z_t)
    elif args.role is not None:
        fit = main(args.role.lower())
        print(fit.summary())
