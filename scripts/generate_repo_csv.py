import json
from pathlib import Path
from typing import Any

import click
import pandas as pd
from tqdm import tqdm

OUTPUT_KEYS = [
    "id",
    "full_name",
    "html_url",
    "size",
    "language",
    "created_at",
    "updated_at",
    "pushed_at",
    "stargazers_count",
    "forks_count",
    "open_issues_count",
]
EXCLUDE_IF_TRUE = ["private", "is_template", "archived", "disabled"]


def find_root(repo_obj: Any) -> Any:
    if repo_obj.get("parent") is None:
        return repo_obj
    return find_root(repo_obj["parent"])


def load_repo_details(path: Path) -> Any:
    try:
        obj = json.loads(path.read_text())
    except json.decoder.JSONDecodeError as e:
        print(f"\nWarning: Failed to decode {path}")
        print(e)
        print("Tip: Delete this file so it can be re-downloaded")
        return None
    if obj is None:
        return None
    obj = find_root(obj)
    for key in EXCLUDE_IF_TRUE:
        if obj[key]:
            return None
    row = {}
    for key in OUTPUT_KEYS:
        row[key] = obj[key]
    return row


def load_repo_df(root: Path) -> pd.DataFrame:
    repos = {}
    files = list(root.glob("**/*.json"))
    print(f"Found {len(files)} JSON files.")
    for file in tqdm(files):
        repo = load_repo_details(file)
        if repo is not None:
            repos[repo["id"]] = repo
    print(f"Found {len(repos)} repos across {len(files)} JSON files.")
    return pd.DataFrame.from_records(list(repos.values()), index="id")


@click.command()
@click.option("--input", required=True, help="A directory of repo JSON files")
@click.option("--output", required=True, help="Path to output CSV file")
@click.option("--no-filtering", is_flag=True, help="Do not apply any filters")
@click.option("--languages", default="Java", help="Comma-separated list of languages")
@click.option("--max-size", default=2.0, help="Max size a repo can be (in GB)")
@click.option("--min-stars", default=64, help="Min number of stars a repo must have")
@click.option("--min-forks", default=64, help="Min number of forks a repo must have")
@click.option(
    "--min-open-issues", default=16, help="Min number of open issues a repo must have"
)
def main(
    input: str,
    output: str,
    no_filtering: bool,
    languages: str,
    max_size: int,
    min_stars: int,
    min_forks: int,
    min_open_issues: int,
):
    """
    Scan through the JSON files downloaded by fetch_repo_details.py and output a CSV.
    """
    df = load_repo_df(Path(input))
    df = df.sort_values(
        ["stargazers_count", "forks_count", "open_issues_count"], ascending=False
    )
    if no_filtering:
        df.to_csv(output)
        return
    languages = set(languages.split(","))
    df = df[df["language"].isin(languages)]
    df = df[df["size"] <= max_size * 1_000_000]
    df = df[df["stargazers_count"] >= min_stars]
    df = df[df["forks_count"] >= min_forks]
    df = df[df["open_issues_count"] >= min_open_issues]
    df.to_csv(output)


if __name__ == "__main__":
    main()
