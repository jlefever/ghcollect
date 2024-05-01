# GitHub Collect

This is a set of scripts for collecting repository data from GitHub.

## Scripts

To use the scripts, first create a virtual environment, activate it, and install the required packages.

```bash
python -m venv .venv
source .venv/bin/activate.sh
python -m pip install -r requirements.txt
```

Use the `--help` option on each script to get details on how to use it. These scripts were created with Python 3.11.1 in mind, but this exact version shouldn't be required.

## Usage

The scripts are intended to be run in the following order.

##### 1. Collect repository names

Create a text file with a GitHub repository name on each line. These are collected from [The Stack](https://huggingface.co/datasets/bigcode/the-stack) dataset. This is incredibly expensive to run so you almost certainly just want to use the supplied `artifacts/repo_names.txt`.

```bash
python scripts/fetch_repo_names.py --hf-token <HF_TOKEN> --output repo_names.txt
```

##### 2. Download metadata

Download the metadata from each GitHub repository.

```bash
python scripts/fetch_repo_details.py --gh-token <GH_TOKEN> --input repo_names.txt --output repo_details
```

##### 3. Generate a single CSV

Summarize the repository data into a single CSV.

```bash
python scripts/generate_repo_csv.py --input repo_details --output repos.csv
```

##### 4. Clone repositories

Clone the repositories from the CSV one-by-one in order.

```bash
python scripts/clone_repos.py --input repos.csv --output clones
```

##### 5. Extract data using Neodepends

Export entities, deps, changes, and contents from the repository into a SQLite database using [Neodepends](https://github.com/jlefever/neodepends).

```bash
python scripts/extract_dbs.py --input repos.csv --clones clones --output dbs
```
