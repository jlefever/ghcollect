import subprocess as sp
from pathlib import Path

import click
import pandas as pd


def extract(repo_name, clones_dir, output_dir):
    output_path = Path(output_dir, f"{repo_name}.db").absolute()
    clone_path = Path(clones_dir, f"{repo_name}.git").absolute()
    if output_path.exists():
        print("Has already been extracted. Skipping...")
        return
    if not clone_path.exists():
        print("Has not been cloned. Skipping...")
        return
    print("Extracting...")

    # Create a text file with the commits. This is to get around /bin/sh
    # complaining that the argument list is too long for some projects.
    commits = sp.run(
        ["git", "rev-list", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
        cwd=clone_path,
    ).stdout
    revlist_path = Path(output_dir, f"{repo_name}.rev-list").absolute()
    revlist_path.parent.mkdir(parents=True, exist_ok=True)
    with revlist_path.open("w") as f:
        f.write(commits)

    # Now run neodepends
    neodepends_args = [
        "neodepends",
        f"--output={output_path}",
        "-D",
        "-ljava",
        "--depends-xmx=12G",
        revlist_path,
    ]
    sp.run(neodepends_args, check=True, cwd=clone_path)


@click.command()
@click.option("--input", required=True, help="A CSV of GitHub repositories")
@click.option("--clones", required=True, help="Path of cloned repositories")
@click.option("--output", required=True, help="Path to database directory")
@click.option("--skip", default=0, help="Number of repos to skip before starting")
def main(input, clones, output, skip):
    """
    Extract dbs from repositories one-by-one in the order that they appear in the CSV.
    """
    df = pd.read_csv(input)
    repo_names = list(df["full_name"])
    for i, repo_name in enumerate(repo_names[skip:]):
        print(f"[{i + skip + 1}/{len(repo_names)}][{repo_name}] ", end="")
        extract(repo_name, clones, output)


if __name__ == "__main__":
    main()
