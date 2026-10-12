from argparse import ArgumentParser
from cmdstanpy import CmdStanModel, CmdStanMCMC
import polars as pl

STAN_VARS = {"iter_sampling": 1000, "iter_warmup": 1000, "chains": 4, "inits": 0}

StanData = dict[str, list[float | int] | int | float]


def get_stan_data() -> StanData:
    train = pl.read_csv("train.csv", infer_schema_length=100_000)
    test = pl.read_csv("test.csv", infer_schema_length=100_000)

    return {
        "N": train.shape[0],
        "T": test.shape[0],
        "L": 1.5,
        "U": 4.5,
        "K": 5,
        "M": train["clean_book_id"].unique().len(),
        "P": train["clean_user_id"].unique().len(),
        "p": train["clean_user_id"].to_list(),
        "m": train["clean_book_id"].to_list(),
        "m_test": test["clean_book_id"].to_list(),
        "p_test": test["clean_user_id"].to_list(),
        "y": train["rating"].cast(pl.Int64).to_list(),
        "y_test": test["rating"].cast(pl.Int64).to_list(),
    }


def fit_model(stan_data: StanData, model: CmdStanModel) -> CmdStanMCMC:
    fit: CmdStanMCMC = model.sample(
        data=stan_data,
        **STAN_VARS,
    )
    fit.draws_pd().to_csv(f"posteriors/{model.name}.csv")
    del fit
    del model
    del stan_data


def main(model_name: str) -> None:
    stan_data = get_stan_data()
    model = CmdStanModel(stan_file=model_name)
    fit_model(stan_data, model)
