import os

import click
from datasets import load_dataset


@click.command()
@click.option("--hf-token", required=True, help="Your Hugging Face user access token")
@click.option("--output", required=True, help="Path to output file")
def main(hf_token, output):
    """
    Collect the names of GitHub repositories from The Stack dataset.

    This requires downloading the entire dataset (~400GB) just to get these
    names so don't run this unless absolutely necessary. Will create a new text
    file containing a newline-delimited list of repo names. A repo name has
    exactly one slash. For instance, "apache/deltaspike".

    If you get a ModuleNotFoundError complaining about '_lzma', see
    https://stackoverflow.com/a/69517932
    """
    # Make sure the output doesn't exist yet
    if os.path.exists(output):
        raise FileExistsError(f"'{output}' already exists")

    # Download and open
    print("Downloading and opening The Stack dataset...")
    ds = load_dataset("bigcode/the-stack", data_dir="data/java", token=hf_token)

    # Collect names into the keys of a dictionary. We use a dictionary to
    # preserve the order https://stackoverflow.com/a/17016257
    print("Collecting repo names from dataset...")
    repos = {}

    def insert_repo(row):
        repos[row["max_stars_repo_name"]] = None

    ds["train"].map(insert_repo)

    # Write to output
    print(f"Writing output to '{output}'...")
    with open(output, "x") as f:
        f.writelines(repos)


if __name__ == "__main__":
    main()
