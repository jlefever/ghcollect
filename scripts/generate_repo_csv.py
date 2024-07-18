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
def main(input: str, output: str):
    """
    Scan through the JSON files downloaded by fetch_repo_details.py and output a CSV.
    """
    load_repo_df(Path(input)).sort_index().to_csv(output)


if __name__ == "__main__":
    main()
