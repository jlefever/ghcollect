import os
import subprocess as sp
from pathlib import Path

import click
import pandas as pd


def clone(repo_name, output):
    clone_path = Path(output, f"{repo_name}.git")
    if clone_path.exists():
        print("Skipping...")
        return
    print("Cloning...")
    url = "https://github.com/" + repo_name
    cmd = f"git clone --bare {url} {clone_path}"
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0")
    sp.run(cmd, shell=True, env=env)


@click.command()
@click.option("--input", required=True, help="A CSV of GitHub repositories")
@click.option("--output", required=True, help="Path to cloning directory")
@click.option("--skip", default=0, help="Number of repos to skip before starting")
def main(input, output, skip):
    """
    Clone repositories one-by-one in the order that they appear in the CSV.
    """
    df = pd.read_csv(input)
    repo_names = list(df["full_name"])
    for i, repo_name in enumerate(repo_names[skip:]):
        print(f"[{i + skip + 1}/{len(repo_names)}][{repo_name}] ", end="")
        clone(repo_name, output)


if __name__ == "__main__":
    main()
