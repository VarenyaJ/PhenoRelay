from __future__ import annotations

from pathlib import Path

import duckdb

from phenorelay.index import load_projected_records
from phenorelay.manifest import load_site_manifest
from phenorelay.sqlite_index import SQLiteReleaseIndex
from phenorelay.table_export import export_release_tables


def test_duckdb_counts_match_sqlite_for_exported_csv_tables(tmp_path) -> None:
    table_dir = tmp_path / "tables"
    sqlite_index = build_sqlite_index(tmp_path)
    export_example_tables(table_dir)

    with duckdb.connect(":memory:") as connection:
        create_views(connection, table_dir)

        assert count_one(connection, "phenotypes", "HP:0001250", "present") == (
            sqlite_index.count_exact("phenotype", "HP:0001250", "present")
        )
        assert count_one(connection, "phenotypes", "HP:0011344", "excluded") == (
            sqlite_index.count_exact("phenotype", "HP:0011344", "excluded")
        )
        assert count_one(connection, "diseases", "MONDO:0000001", "present") == (
            sqlite_index.count_exact("disease", "MONDO:0000001", "present")
        )
        assert count_one(connection, "medical_actions", "MAXO:0000072") == (
            sqlite_index.count_exact("medical_action", "MAXO:0000072", "present")
        )


def test_duckdb_exported_csv_tables_preserve_expected_columns(tmp_path) -> None:
    table_dir = tmp_path / "tables"
    export_example_tables(table_dir)

    with duckdb.connect(":memory:") as connection:
        create_views(connection, table_dir)
        record_columns = {
            row[0]
            for row in connection.execute("DESCRIBE records").fetchall()
        }
        phenotype_columns = {
            row[0]
            for row in connection.execute("DESCRIBE phenotypes").fetchall()
        }

    assert record_columns == {
        "phenopacket_id",
        "subject_id_redacted",
        "has_genomic_interpretations",
    }
    assert "subject_id" not in record_columns
    assert phenotype_columns == {"phenopacket_id", "term", "label", "presence"}


def test_duckdb_can_join_feature_tables_back_to_records(tmp_path) -> None:
    table_dir = tmp_path / "tables"
    export_example_tables(table_dir)

    with duckdb.connect(":memory:") as connection:
        create_views(connection, table_dir)
        rows = connection.execute(
            """
            SELECT records.phenopacket_id, phenotypes.label
            FROM records
            JOIN phenotypes USING (phenopacket_id)
            WHERE phenotypes.term = 'HP:0004322'
            """
        ).fetchall()

    assert rows == [("synthetic-packet-2", "Short stature")]


def test_duckdb_can_convert_exported_csv_tables_to_parquet(tmp_path) -> None:
    table_dir = tmp_path / "tables"
    parquet_dir = tmp_path / "parquet"
    export_example_tables(table_dir)
    parquet_dir.mkdir()

    with duckdb.connect(":memory:") as connection:
        create_views(connection, table_dir)
        for table_name in export_table_names():
            parquet_path = sql_string_literal(parquet_dir / f"{table_name}.parquet")
            connection.execute(
                f"""
                COPY {table_name}
                TO {parquet_path}
                (FORMAT parquet)
                """
            )

        phenotype_count = connection.execute(
            f"""
            SELECT COUNT(*)
            FROM read_parquet({sql_string_literal(parquet_dir / "phenotypes.parquet")})
            WHERE term = 'HP:0001250'
              AND presence = 'present'
            """
        ).fetchone()
        record_columns = {
            row[0]
            for row in connection.execute(
                "DESCRIBE SELECT * "
                f"FROM read_parquet({sql_string_literal(parquet_dir / 'records.parquet')})"
            ).fetchall()
        }

    assert phenotype_count == (1,)
    assert "subject_id" not in record_columns
    assert record_columns == {
        "phenopacket_id",
        "subject_id_redacted",
        "has_genomic_interpretations",
    }


def build_sqlite_index(tmp_path) -> SQLiteReleaseIndex:
    return SQLiteReleaseIndex.build(
        path=tmp_path / "release.sqlite",
        manifest=load_site_manifest(Path("examples/site-manifest.yaml")),
        records=load_projected_records(Path("examples/projected-records.yaml")),
    )


def export_example_tables(table_dir: Path) -> None:
    export_release_tables(
        manifest=load_site_manifest(Path("examples/site-manifest.yaml")),
        records=load_projected_records(Path("examples/projected-records.yaml")),
        out_dir=table_dir,
    )


def create_views(connection: duckdb.DuckDBPyConnection, table_dir: Path) -> None:
    for table_name in export_table_names():
        table_path = sql_string_literal(table_dir / f"{table_name}.csv")
        connection.execute(
            f"""
            CREATE VIEW {table_name} AS
            SELECT *
            FROM read_csv_auto({table_path})
            """
        )


def export_table_names() -> tuple[str, ...]:
    return (
        "records",
        "phenotypes",
        "diseases",
        "medical_actions",
        "release_metadata",
    )


def count_one(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
    term: str,
    presence: str | None = None,
) -> int:
    if presence is None:
        row = connection.execute(
            f"SELECT COUNT(DISTINCT phenopacket_id) FROM {table_name} WHERE term = ?",
            [term],
        ).fetchone()
    else:
        row = connection.execute(
            f"""
            SELECT COUNT(DISTINCT phenopacket_id)
            FROM {table_name}
            WHERE term = ? AND presence = ?
            """,
            [term, presence],
        ).fetchone()
    assert row is not None
    return int(row[0])


def sql_string_literal(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"
