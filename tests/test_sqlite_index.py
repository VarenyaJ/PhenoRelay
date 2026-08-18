from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from textwrap import dedent

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


def test_sqlite_cli_build_with_hpo_validation_reports_clean_validation(tmp_path) -> None:
    db = tmp_path / "release.sqlite"
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "sqlite-build",
            "--manifest",
            "examples/site-manifest.yaml",
            "--records",
            "examples/projected-records.yaml",
            "--db",
            str(db),
            "--validate-hpo",
            "tests/fixtures/hp-mini.json",
        ],
    )

    assert result.exit_code == 0
    assert db.exists()
    output = json.loads(result.stdout)
    assert output["build"]["record_count"] == 2
    assert output["validation"]["ok"] is True
    assert output["validation"]["checked_term_count"] == 3
    assert (
        output["validation"]["hpo_version"]
        == "http://purl.obolibrary.org/obo/hp/releases/synthetic/hp.json"
    )


def test_sqlite_cli_build_with_hpo_validation_rejects_missing_id_before_create(
    tmp_path,
) -> None:
    records = write_projected_records(
        tmp_path,
        """
        records:
          - phenopacket_id: bad-packet
            subject_id_redacted: true
            phenotypes:
              - term: HP:9999999
                label: Missing term
                presence: present
            diseases: []
            medical_actions: []
            has_genomic_interpretations: false
        """,
    )
    db = tmp_path / "release.sqlite"
    runner = CliRunner()

    result = runner.invoke(
        app,
        [
            "sqlite-build",
            "--manifest",
            "examples/site-manifest.yaml",
            "--records",
            str(records),
            "--db",
            str(db),
            "--validate-hpo",
            "tests/fixtures/hp-mini.json",
        ],
    )

    assert result.exit_code == 1
    assert not db.exists()
    output = json.loads(result.stdout)
    assert output["validation"]["ok"] is False
    assert output["validation"]["findings"][0]["code"] == "HPO001"


def test_sqlite_cli_validation_failure_does_not_replace_existing_db(tmp_path) -> None:
    db = tmp_path / "release.sqlite"
    bad_records = write_projected_records(
        tmp_path,
        """
        records:
          - phenopacket_id: bad-packet
            subject_id_redacted: true
            phenotypes:
              - term: HP:0001250
                label: Wrong label
                presence: present
            diseases: []
            medical_actions: []
            has_genomic_interpretations: false
        """,
    )
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

    failed_rebuild = runner.invoke(
        app,
        [
            "sqlite-build",
            "--manifest",
            "examples/site-manifest.yaml",
            "--records",
            str(bad_records),
            "--db",
            str(db),
            "--validate-hpo",
            "tests/fixtures/hp-mini.json",
        ],
    )
    summary_result = runner.invoke(app, ["sqlite-summary", "--db", str(db)])

    assert build_result.exit_code == 0
    assert failed_rebuild.exit_code == 1
    assert summary_result.exit_code == 0
    assert json.loads(failed_rebuild.stdout)["validation"]["findings"][0]["code"] == "HPO002"
    assert json.loads(summary_result.stdout)["record_count"] == 2


def build_example_sqlite_index(tmp_path) -> SQLiteReleaseIndex:
    return SQLiteReleaseIndex.build(
        path=tmp_path / "release.sqlite",
        manifest=load_site_manifest(Path("examples/site-manifest.yaml")),
        records=load_projected_records(Path("examples/projected-records.yaml")),
    )


def write_projected_records(tmp_path, text: str) -> Path:
    path = tmp_path / "projected-records.yaml"
    path.write_text(dedent(text), encoding="utf-8")
    return path
