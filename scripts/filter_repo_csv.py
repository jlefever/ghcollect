import itertools as it
from pathlib import Path
from typing import Any

import click
import pandas as pd


def join_singles(terms: list[str]) -> list[str]:
    ret = []
    joined_term = []
    for t in terms:
        if len(t) == 1:
            joined_term.append(t[0])
        elif len(t) > 1:
            if len(joined_term) > 0:
                ret.append("".join(joined_term))
                joined_term = []
            ret.append(t)
    if len(joined_term) > 0:
        ret.append("".join(joined_term))
    return ret


def split_camel(name: str) -> list[str]:
    if name.isupper():
        return [name.lower()]
    indices = [i for i, x in enumerate(name) if x.isupper() or x.isnumeric()]
    indices = [0] + indices + [len(name)]
    return join_singles([name[a:b].lower() for a, b in it.pairwise(indices)])


def split_identifier(name: str) -> set[str]:
    by_spaces = name.split(" ")
    by_forward_slashes = it.chain(*(z.split("/") for z in by_spaces))
    by_backward_slashes = it.chain(*(z.split("\\") for z in by_forward_slashes))
    by_dashes = it.chain(*(z.split("-") for z in by_backward_slashes))
    by_underscores = it.chain(*(z.split("_") for z in by_dashes))
    by_camel = it.chain(*(split_camel(z) for z in by_underscores))
    return set(by_camel)


@click.command()
@click.option("--input", required=True, help="A an existing repo CSV file")
@click.option("--output", required=True, help="Path to output CSV file")
@click.option("--languages", default="Java", help="Comma-separated list of languages")
@click.option("--max-size", default=2.0, help="Max size a repo can be (in GB)")
@click.option("--min-stars", default=64, help="Min number of stars")
@click.option("--min-forks", default=64, help="Min number of forks")
@click.option("--min-open-issues", default=16, help="Min number of open issues")
@click.option("--keywords", help="Text file with a newline-delimited list of keywords.")
def main(
    input: str,
    output: str,
    languages: str,
    max_size: int,
    min_stars: int,
    min_forks: int,
    min_open_issues: int,
    keywords: str,
):
    """
    Produce a new CSV file given the output of generate_repo_csv.py.

    See the options for what filters can be set. If a repo name includes any
    keywords in the --keywords file, that repo will be omitted.
    """
    df = pd.read_csv(input, index_col="id")
    languages = set(languages.split(","))
    df = df[df["language"].isin(languages)]
    df = df[df["size"] <= max_size * 1_000_000]
    df = df[df["stargazers_count"] >= min_stars]
    df = df[df["forks_count"] >= min_forks]
    df = df[df["open_issues_count"] >= min_open_issues]

    if keywords is not None:
        excluded = set((k.lower() for k in Path(keywords).read_text().splitlines()))
        df = df[[len(split_identifier(n) & excluded) == 0 for n in df["full_name"]]]

    df = df.sort_values(
        ["stargazers_count", "forks_count", "open_issues_count"], ascending=False
    )
    df.to_csv(output)


if __name__ == "__main__":
    main()
