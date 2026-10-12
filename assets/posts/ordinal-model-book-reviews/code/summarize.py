from argparse import ArgumentParser
import json
import polars as pl
import numpy as np
from scipy.special import logsumexp
from sim import kruschke_ordinal_rng
from tqdm import tqdm


def serialize(x: dict):
    serialized = {}
    for k, v in x.items():
        if isinstance(v, dict):
            serialized[k] = serialize(v)
        elif isinstance(v, np.ndarray):
            serialized[k] = v.tolist()
        elif isinstance(v, np.float64):
            serialized[k] = float(v)
        elif isinstance(v, np.int64):
            serialized[k] = int(v)
        else:
            serialized[k] = v
    return serialized


rng = np.random.default_rng(1234)


def main(model_name: str):
    train = pl.read_csv("train.csv")
    test = pl.read_csv("test.csv")
    posterior = pl.read_csv(f"posteriors/{model_name}.csv")
    columns = posterior.columns
    mu = posterior["mu"]
    S = posterior.shape[0]
    if "sigma" in columns:
        sigma = posterior["sigma"].to_numpy()
    else:
        sigma = np.zeros((S,))

    unique_books = (
        train.group_by(
            [
                "book_id",
                "clean_book_id",
                "title",
                "authors",
                "ratings_count",
                "average_rating",
            ],
            maintain_order=True,
        )
        .agg(
            train_len=pl.col("rating").len(),
            value_counts=pl.col("rating").value_counts(),
            rating_mean=pl.col("rating").mean(),
            rating_sd=pl.col("rating").std(),
        )
        .with_row_index()
    )

    book_intercepts = np.asarray([
        mu + (
            0 if f"z_m[{clean_book_id}]" not in posterior.columns else (
                posterior["tau"] * posterior[f"z_m[{clean_book_id}]"]
            )
        )
        for clean_book_id
        in unique_books["clean_book_id"]
    ])

    posterior_ranks = np.argsort(
        np.argsort(book_intercepts, axis=0, stable=True),
        axis=0,
    )
    full_sample_ranks = np.argsort(unique_books["average_rating"]).argsort()
    train_ranks = np.argsort(unique_books["rating_mean"]).argsort()

    results = {}
    samples_idx = rng.choice(range(posterior.shape[0]), size=100, replace=True)
    for i, row in enumerate(tqdm(unique_books.rows(named=True))):
        clean_book_id = row["clean_book_id"]
        train_row_indices = train.filter(pl.col("clean_book_id") == clean_book_id)[
            "index"
        ].to_list()
        test_row_indices = test.filter(pl.col("clean_book_id") == clean_book_id)[
            "index"
        ].to_list()
        lp_train = -np.log(S) + logsumexp(
            posterior[[f"lp[{i + 1}]" for i in train_row_indices]], axis=0
        )
        lp_test = -np.log(S) + logsumexp(
            posterior[[f"lp_test[{i + 1}]" for i in test_row_indices]], axis=0
        )
        eta = book_intercepts[i]
        if "linear" in model_name:
            sims = rng.lognormal(eta, sigma)
            pp = sims[samples_idx]
            pp_probs = None
        elif "poisson" in model_name:
            sims = rng.poisson(np.exp(eta))
            pp = sims[samples_idx]
            pp_probs = None
        else:
            theta_cols = [
                col for col in columns 
                if "theta" in col and "theta_star" not in col
            ]
            theta = posterior[theta_cols].to_numpy()
            pi, sims = zip(
                *[
                    kruschke_ordinal_rng(t, m, s, rng)
                    for t, m, s in zip(theta, eta, sigma)
                ]
            )
            pp = pl.Series(sims).value_counts().to_numpy()
            pp_probs = np.array(pi)
        results[clean_book_id] = {
            **row,
            "eta_samples": eta[samples_idx].tolist(),
            "eta_mean": eta.mean(),
            "eta_sd": eta.std(),
            "sigma_samples": sigma[samples_idx].tolist(),
            "sigma_mean": sigma.mean(),
            "sigma_sd": sigma.std(),
            "posterior_predictive": pp,
            "posterior_predictive_mean": np.mean(sims),
            "posterior_predictive_sd": np.std(sims),
            "posterior_predictive_probs": pp_probs,
            "n_samples": S,
            "lp_train_mean": lp_train.mean(),
            "lp_train_sum": lp_train.sum(),
            "lp_test_mean": lp_test.mean(),
            "lp_test_sum": lp_test.sum(),
            "posterior_rank": posterior_ranks[i],
            "train_rank": train_ranks[i],
            "full_sample_rank": full_sample_ranks[i],
        }

    with open(f"posteriors/{model_name}-summary.json", "w") as f:
        json.dump(serialize(results), f)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--model-names", nargs="+", default=None)
    args = parser.parse_args()
    if args.model_names is None:
        model_names = (
            "hierarchical-intercepts",
            "complete-pooling",
            "linear-hierarchical-intercepts",
            "poisson-hierarchical-intercepts",
        )
    else:
        model_names = args.model_names
    for name in model_names:
        main(name)
