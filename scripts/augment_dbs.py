import sqlite3
from pathlib import Path

import click
from tqdm import tqdm

SQL = """
    CREATE INDEX IF NOT EXISTS idx_entities_name ON entities(name);
    CREATE INDEX IF NOT EXISTS idx_entities_parent_id ON entities(parent_id);
    CREATE INDEX IF NOT EXISTS idx_deps_src_tgt ON deps(src, tgt);
    CREATE INDEX IF NOT EXISTS idx_changes_simple_commit ON changes(simple_id, commit_id);

    CREATE TABLE IF NOT EXISTS ancestors AS
    WITH RECURSIVE ancestors (entity_id, ancestor_id) AS
    (
        SELECT E.id AS entity_id, E.id AS ancestor_id
        FROM entities E

        UNION

        SELECT E.id AS entity_id, A.ancestor_id
        FROM ancestors A
        JOIN entities E ON E.parent_id = A.entity_id
    )
    SELECT * FROM ancestors;

    CREATE INDEX IF NOT EXISTS idx_ancestors_entity_id ON ancestors(entity_id);
    CREATE INDEX IF NOT EXISTS idx_ancestors_ancestor_id ON ancestors(ancestor_id);

    CREATE TABLE IF NOT EXISTS filenames AS
    SELECT
        E.id AS entity_id,
        E.simple_id AS simple_id,
        FE.id AS file_id,
        FE.content_id AS content_id,
        FE.name AS filename
    FROM entities E
    JOIN ancestors A ON A.entity_id = E.id
    JOIN entities FE ON FE.id = A.ancestor_id
    WHERE FE.parent_id IS NULL;

    CREATE INDEX IF NOT EXISTS idx_filenames_entity_id ON filenames(entity_id);
    CREATE INDEX IF NOT EXISTS idx_filenames_simple_id ON filenames(simple_id);
    CREATE INDEX IF NOT EXISTS idx_filenames_content_id ON filenames(content_id);

    VACUUM;
"""


@click.command()
@click.option("--input", required=True, help="A text file of paths to dbs")
def main(input: str):
    """Augment the created dbs with two new tables and some indices."""
    dbs_file = Path(input).resolve()
    dbs_root = dbs_file.parent
    for db_path in tqdm(dbs_file.read_text().splitlines()):
        db_path = Path(dbs_root, db_path)
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.executescript(SQL)
                conn.commit()
        except sqlite3.OperationalError as e:
            print(f"Failed on {db_path}")
            print(e)
            print()


if __name__ == "__main__":
    main()
