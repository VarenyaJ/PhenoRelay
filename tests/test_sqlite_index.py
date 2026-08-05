from __future__ import annotations

import sqlite3
from pathlib import Path

from typer.testing import CliRunner

from phenorelay.cli import app
from phenorelay.index import load_projected_records
from phenorelay.manifest import load_site_manifest
from phenorelay.sqlite_index import SQLiteReleaseIndex


def test_sqlite_build_creates_expected_tables_and_counts(tmp_path) -> None:
    db = build_example_sqlite_index(tmp_path)

    with sqlite3.connect(db.path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }
        record_count = connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]
        phenotype_count = connection.execute("SELECT COUNT(*) FROM phenotypes").fetchone()[0]

    assert {
        "release_metadata",
        "records",
        "phenotypes",
        "diseases",
        "medical_actions",
    }.issubset(tables)
    assert record_count == 2
    assert phenotype_count == 3


def test_sqlite_summary_reports_release_metadata(tmp_path) -> None:
    index = build_example_sqlite_index(tmp_path)

    summary = index.summary()

    assert summary["site_id"] == "synthetic-site"
    assert summary["release_id"] == "synthetic-release-1"
    assert summary["record_count"] == 2
    assert summary["phenotype_count"] == 3
    assert summary["disease_count"] == 2
    assert summary["medical_action_count"] == 2


def test_sqlite_query_counts_exact_phenotype_matches(tmp_path) -> None:
    index = build_example_sqlite_index(tmp_path)

    outcome = index.query(
        {
            "query_id": "q1",
            "feature": "phenotype",
            "term": "HP:0001250",
            "match_mode": "exact",
            "presence": "present",
            "requested_granularity": "count",
        }
    )

    assert outcome == {
        "query_id": "q1",
        "status": "match",
        "feature": "phenotype",
        "exists": True,
        "count": 1,
    }


def test_sqlite_query_counts_exact_disease_matches(tmp_path) -> None:
    index = build_example_sqlite_index(tmp_path)

    outcome = index.query(
        {
            "query_id": "q1",
            "feature": "disease",
            "term": "MONDO:0000001",
            "match_mode": "exact",
            "requested_granularity": "count",
        }
    )

    assert outcome["count"] == 1


def test_sqlite_query_counts_exact_medical_action_matches(tmp_path) -> None:
    index = build_example_sqlite_index(tmp_path)

    outcome = index.query(
        {
            "query_id": "q1",
            "feature": "medical_action",
            "term": "MAXO:0000072",
            "match_mode": "exact",
            "requested_granularity": "count",
        }
    )

    assert outcome["count"] == 1


def test_sqlite_query_preserves_zero_match_as_match_status(tmp_path) -> None:
    index = build_example_sqlite_index(tmp_path)

    outcome = index.query(
        {
            "query_id": "q1",
            "feature": "phenotype",
            "term": "HP:9999999",
            "match_mode": "exact",
            "presence": "present",
            "requested_granularity": "count",
        }
    )

    assert outcome == {
        "query_id": "q1",
        "status": "match",
        "feature": "phenotype",
        "exists": False,
        "count": 0,
    }


def test_sqlite_query_preserves_unsupported_as_distinct_from_zero_match(tmp_path) -> None:
    index = build_example_sqlite_index(tmp_path)

    outcome = index.query(
        {
            "query_id": "q1",
            "feature": "phenotype",
            "term": "HP:0001250",
            "match_mode": "descendants",
            "presence": "present",
            "requested_granularity": "count",
        }
    )

    assert outcome == {
        "query_id": "q1",
        "status": "unsupported",
        "feature": "phenotype",
    }


def test_sqlite_cli_build_summary_and_query(tmp_path) -> None:
    db = tmp_path / "release.sqlite"
    runner = CliRunner()

    build_result = runner.invoke(
        app,
        [
            "sqlite-build",
            "--manifest",
            "examples/site-manifest.yaml",
            "--records",
            "examples/projected-records.yaml",
            "--db",
            str(db),
        ],
    )
    summary_result = runner.invoke(app, ["sqlite-summary", "--db", str(db)])
    query_result = runner.invoke(
        app,
        [
            "sqlite-query",
            "--db",
            str(db),
            "--request",
            "examples/query-request.yaml",
        ],
    )

    assert build_result.exit_code == 0
    assert summary_result.exit_code == 0
    assert query_result.exit_code == 0
    assert '"record_count": 2' in build_result.stdout
    assert '"phenotype_count": 3' in summary_result.stdout
    assert '"status": "unsupported"' in query_result.stdout


def build_example_sqlite_index(tmp_path) -> SQLiteReleaseIndex:
    return SQLiteReleaseIndex.build(
        path=tmp_path / "release.sqlite",
        manifest=load_site_manifest(Path("examples/site-manifest.yaml")),
        records=load_projected_records(Path("examples/projected-records.yaml")),
    )
