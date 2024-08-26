import sqlite3
import subprocess as sp
import tempfile
import uuid
from io import StringIO
from pathlib import Path

import click
import pandas as pd
from rich.progress import Progress

from datetime import datetime

SELECT_CONTENTS = """
    SELECT E.name AS filename, C.content
    FROM entities E
    JOIN contents C ON C.content_id = E.content_id
    WHERE E.kind = 'File'
    ORDER BY E.name
"""

ADD_COLUMN_LOC = """
    ALTER TABLE contents ADD COLUMN loc INTEGER
"""

ADD_COLUMN_LLOC = """
    ALTER TABLE contents ADD COLUMN lloc INTEGER
"""

UPDATE_CONTENTS = """
    UPDATE contents
    SET loc = ?, lloc = ?
    WHERE content_id = (
        SELECT content_id
        FROM entities
        WHERE kind = 'File' AND name = ?
    );
"""


# def isotimestamp() -> str:
#     return datetime.now().isoformat()


def run_scc(cursor: sqlite3.Cursor, *, chunk_size: int = 128) -> pd.DataFrame:
    # Our filesystem may not be case-sensitive, but git is. So we map to a
    # proxy filename before writing to disk.
    proxy_to_filename = {}
    with tempfile.TemporaryDirectory() as temp_dir:
        # print(f"[{isotimestamp()}] Selecting contents...")
        cursor.execute(SELECT_CONTENTS)
        # print(f"[{isotimestamp()}] Writing contents to disk in chunks...")
        while True:
            rows = cursor.fetchmany(chunk_size)
            if not rows:
                break
            for filename, content in rows:
                segments = str(filename).split(".")
                ext = "" if len(segments) == 0 else "." + segments[-1]
                proxy = str(uuid.uuid4()) + ext.lower()
                proxy_to_filename[proxy] = filename
                path = Path(temp_dir, proxy)
                path.write_text(content)
        args = ["scc", "--by-file", "--format=csv"]
        # print(f"[{isotimestamp()}] Reading in SCC output...")
        csv = sp.run(args, capture_output=True, cwd=temp_dir).stdout.decode()
        scc_df = pd.read_csv(StringIO(csv))
        # SCC use has two columns for filename. We consolidate into one. By
        # "Filename", we are referring to the complete path relative to the root
        # of the repository.
        scc_df.drop(columns=["Filename"], inplace=True)
        scc_df.rename(columns={"Provider": "Filename"}, inplace=True)
        scc_df["Filename"] = [proxy_to_filename[x] for x in scc_df["Filename"]]
        scc_df.set_index("Filename", inplace=True)
        return scc_df


def is_processed(cursor: sqlite3.Cursor) -> bool:
    try:
        cursor.execute("SELECT COUNT(*) FROM contents WHERE loc IS NULL")
        has_locs = cursor.fetchone()[0] == 0
        cursor.execute("SELECT COUNT(*) FROM contents WHERE lloc IS NULL")
        has_llocs = cursor.fetchone()[0] == 0
        return has_locs and has_llocs
    except sqlite3.OperationalError:
        return False


def process_db(db_root, db_path):
    # print(f"[{isotimestamp()}] Trying {db_path}... ")
    print(f"Trying {db_path}... ", end="")
    db_path = Path(db_root, db_path)
    try:
        with sqlite3.connect(db_path) as conn:
            if is_processed(conn.cursor()):
                # print(f"[{isotimestamp()}] Skipped\n")
                print("Skipped")
                return
            scc_df = run_scc(conn.cursor())
            try:
                conn.execute(ADD_COLUMN_LOC)
            except sqlite3.OperationalError:
                pass
            try:
                conn.execute(ADD_COLUMN_LLOC)
            except sqlite3.OperationalError:
                pass
            conn.commit()
            # print(f"[{isotimestamp()}] Updating database...")
            triples = ((r["Lines"], r["Code"], f) for f, r in scc_df.iterrows())
            conn.executemany(UPDATE_CONTENTS, triples)
            conn.commit()
        print("Succeeded")
        # print(f"[{isotimestamp()}] Succeeded\n")
    except sqlite3.OperationalError as e:
        # print(f"[{isotimestamp()}] Failed\n")
        print("Failed")
        print(e)
        print()


@click.command()
@click.option("--input", required=True, help="A text file of paths to dbs")
@click.option("--skip", default=0, help="Number of db_paths to skip before starting")
@click.option("--step", default=1, help="Step size between db_paths")
def main(input, skip, step):
    """Augment the created dbs with two new tables and some indices."""
    dbs_file = Path(input).resolve()
    db_root = dbs_file.parent
    db_paths = dbs_file.read_text().splitlines()
    indices = list(range(skip, len(db_paths), step))

    with Progress() as progress:
        task = progress.add_task("", total=len(indices))
        for local_i, global_i in enumerate(indices):
            db_path = db_paths[global_i]
            desc = f"[green][{local_i}/{len(indices)}][{global_i}/{len(db_paths)}] Working on {db_path}"
            progress.update(task, advance=1, description=desc)
            process_db(db_root, db_path)


if __name__ == "__main__":
    main()
