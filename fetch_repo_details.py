import json
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import click
import requests


@dataclass(frozen=True)
class Repo:
    owner: str
    name: str

    def full_name(self) -> str:
        return f"{self.owner}/{self.name}"

    def path(self) -> str:
        return f"{self.owner}/{self.name}"

    def api_url(self) -> str:
        return f"https://api.github.com/repos/{self.owner}/{self.name}"


@dataclass
class RateLimitInfo:
    remaining: int
    reset: int

    def __init__(self, headers):
        self.remaining = int(headers["X-RateLimit-Remaining"])
        self.reset = int(headers["X-RateLimit-Reset"])

    def pause(self) -> bool:
        if self.remaining != 0:
            return False
        current_time = int(time.time())
        time_to_wait = self.reset - current_time
        if time_to_wait <= 0:
            return False
        timestamp = datetime.fromtimestamp(current_time + time_to_wait).isoformat()
        print(f"Pausing until {timestamp} ({time_to_wait} seconds). ", end="", flush=True)
        time.sleep(time_to_wait)
        return True


def fetch_repo_info(repo: Repo, gh_token: str) -> Any | None:
    headers = {"Authorization": f"token {gh_token}"}
    res = requests.get(repo.api_url(), headers=headers)
    rl_info = RateLimitInfo(res.headers)
    print(f"[{rl_info.remaining} requests remaining]", end="")
    print(f"[{repo.full_name()}] ", end="")
    paused = rl_info.pause()
    if res.ok:
        print("Success!")
        return res.json()
    if res.status_code == 404:
        print("Repo doesn't exist on GitHub. Skipping...")
        return None
    if res.status_code != 403:
        print("Unable to fetch repo details. Skipping...")
        return None
    if paused:
        print("Retrying...")
        return fetch_repo_info(repo)
    print("Unknown issue while fetching repo details. Skipping...")
    return None


def save_repo_info(repo: Repo, output_dir: Path, gh_token: str) -> Any:
    path = Path(output_dir, f"{repo.path()}.json")
    if path.exists():
        print(f"[{repo.full_name()}] Already downloaded! Skipping...")
        return
    repo_info = fetch_repo_info(repo, gh_token)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as f:
        json.dump(repo_info, f, indent=4)


@click.command()
@click.option("--gh-token", required=True, help="Your GitHub user access token")
@click.option("--input", required=True, help="A newline-delimited list of GitHub repos")
@click.option("--output", required=True, help="Path to output directory")
@click.option("--skip", default=0, help="Number of repos to skip before starting")
def main(gh_token: str, input: str, output: str, skip: int):
    """
    Download the details of each repository to a JSON file using the GitHub API.

    Will iterate through the given input file and attempt to download the
    metadata of each one as a JSON file. The JSON files are saved in the
    directory given by --output. If a file already exists in the output
    directory, it will be skipped. This script respects the rate limit of the
    GitHub API.
    """
    # Read input as a list of Repos
    repos: list[Repo] = []

    with open(input) as f:
        for line in f.readlines():
            arr = line.strip().split("/")
            if len(arr) != 2:
                raise ValueError("invalid repo name found")
            repos.append(Repo(*arr))

    print(f"Found {len(repos)} repositories in '{input}'.")

    # Download
    for i, repo in enumerate(repos[skip:]):
        print(f"[{i + skip + 1}/{len(repos)}]", end="")
        save_repo_info(repo, Path(output), gh_token)


if __name__ == "__main__":
    main()
