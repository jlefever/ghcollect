import sqlite3
from pathlib import Path

import click
import pandas as pd
from tqdm import tqdm

SQL_TEST_1 = "SELECT COUNT(*) > 0 FROM changes;"
SQL_TEST_2 = "SELECT COUNT(*) > 0 FROM contents;"
SQL_TEST_3 = "SELECT COUNT(*) > 0 FROM deps;"
SQL_TEST_4 = "SELECT COUNT(*) > 0 FROM entities;"
SQL_TEST_5 = """
    SELECT 
        (SELECT COUNT(*) FROM contents)
        ==
        (SELECT COUNT(*) FROM entities WHERE kind == 'File')
"""
SQL_TESTS = [SQL_TEST_1, SQL_TEST_2, SQL_TEST_3, SQL_TEST_4, SQL_TEST_5]


def passes_sql_test(cur, sql_test) -> bool:
    cur.execute(sql_test)
    return cur.fetchone()[0] == 1


def is_valid(db_path: Path) -> bool:
    try:
        with sqlite3.connect(db_path) as conn:
            cur = conn.cursor()
            return all(passes_sql_test(cur, t) for t in SQL_TESTS)
    except sqlite3.OperationalError:
        return False


@click.command()
@click.option("--input", required=True, help="A CSV of GitHub repositories")
@click.option("--dbs", required=True, help="Path to database directory")
@click.option("--output", required=True, help="Path to output text file")
def main(input: str, dbs: str, output: str):
    """
    Export a list of valid databases.

    Scan through the given repos and checks the validity of thee database
    associated with each one. If it is valid, its path is written to output as a
    new line. "Invalid" databases are those that have noticeable problems,
    indicating a problem during extraction with neodepends.
    """
    df = pd.read_csv(input)
    paths = [Path(dbs, f"{n}.db") for n in df["full_name"]]

    with Path(output).open("w") as f:
        for path in tqdm(paths):
            if is_valid(path):
                f.write(f"{path}\n")


if __name__ == "__main__":
    main()
