from argparse import ArgumentParser
import fit


def main(model_names: list[str]):
    for model_name in model_names:
        fit.main(model_name)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("--model-names", nargs="+")
    args = parser.parse_args()
    main(args.model_names)
