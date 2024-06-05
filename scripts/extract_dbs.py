import subprocess as sp
from pathlib import Path

import click
import pandas as pd
from rich.progress import Progress


def extract(neodepends, repo_name, clones_dir, output_dir):
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
        str(Path(neodepends).absolute()),
        f"--output={output_path}",
        "-D",
        "-ljava",
        "--depends-xmx=12G",
        str(revlist_path),
    ]

    with sp.Popen(
        neodepends_args,
        stdout=sp.PIPE,
        stderr=sp.STDOUT,
        cwd=clone_path,
        universal_newlines=True,
    ) as process:
        for line in process.stdout:
            print(line, end="")


@click.command()
@click.option(
    "--neodepends", default="neodepends", help="Command to run for neodepends"
)
@click.option("--input", required=True, help="A CSV of GitHub repositories")
@click.option("--clones", required=True, help="Path of cloned repositories")
@click.option("--output", required=True, help="Path to database directory")
@click.option("--skip", default=0, help="Number of repos to skip before starting")
@click.option("--step", default=1, help="Step size between repos")
def main(neodepends, input, clones, output, skip, step):
    """
    Extract dbs from repositories one-by-one in the order that they appear in the CSV.
    """
    df = pd.read_csv(input)
    repo_names = list(df["full_name"])
    indices = list(range(skip, len(repo_names), step))

    with Progress() as progress:
        task = progress.add_task("", total=len(indices))
        for local_i, global_i in enumerate(indices):
            repo_name = repo_names[global_i]
            desc = f"[green][{local_i}/{len(indices)}][{global_i}/{len(repo_names)}] Working on {repo_name}"
            progress.update(task, advance=1, description=desc)
            extract(neodepends, repo_name, clones, output)


if __name__ == "__main__":
    main()
