from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from phenorelay.cli import app
from phenorelay.index import LocalReleaseIndex, load_projected_records
from phenorelay.manifest import load_site_manifest


def test_load_projected_records_reads_synthetic_records() -> None:
    records = load_projected_records(Path("examples/projected-records.yaml"))

    assert len(records) == 2
    assert records[0].phenopacket_id == "synthetic-packet-1"
    assert records[0].subject_id_redacted


def test_local_index_counts_exact_phenotype_matches() -> None:
    index = example_index()

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

    assert outcome["status"] == "match"
    assert outcome["exists"]
    assert outcome["count"] == 1


def test_local_index_counts_exact_disease_matches() -> None:
    index = example_index()

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


def test_local_index_counts_exact_medical_action_matches() -> None:
    index = example_index()

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


def test_local_index_preserves_zero_match_as_match_status() -> None:
    index = example_index()

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


def test_local_index_preserves_unsupported_as_distinct_from_zero_match() -> None:
    index = example_index()

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


def test_local_index_reports_gene_query_as_unsupported() -> None:
    index = example_index()

    outcome = index.query(
        {
            "query_id": "q1",
            "feature": "gene",
            "term": "HGNC:1100",
            "requested_granularity": "count",
        }
    )

    assert outcome["status"] == "unsupported"


def test_local_index_reports_record_granularity_as_unsupported() -> None:
    index = example_index()

    outcome = index.query(
        {
            "query_id": "q1",
            "feature": "phenotype",
            "term": "HP:0001250",
            "match_mode": "exact",
            "presence": "present",
            "requested_granularity": "record",
        }
    )

    assert outcome["status"] == "unsupported"


def test_index_summary_cli_prints_release_summary() -> None:
    result = CliRunner().invoke(
        app,
        [
            "index-summary",
            "--manifest",
            "examples/site-manifest.yaml",
            "--records",
            "examples/projected-records.yaml",
        ],
    )

    assert result.exit_code == 0
    assert '"site_id": "synthetic-site"' in result.stdout
    assert '"record_count": 2' in result.stdout
    assert '"backend_count": 4' in result.stdout


def test_query_local_cli_emits_query_outcome() -> None:
    result = CliRunner().invoke(
        app,
        [
            "query-local",
            "--manifest",
            "examples/site-manifest.yaml",
            "--records",
            "examples/projected-records.yaml",
            "--request",
            "examples/query-request.yaml",
        ],
    )

    assert result.exit_code == 0
    assert '"status": "unsupported"' in result.stdout


def test_index_summary_cli_rejects_malformed_projected_records(tmp_path) -> None:
    records = tmp_path / "records.yaml"
    records.write_text("records:\n  - not-a-mapping\n", encoding="utf-8")

    result = CliRunner().invoke(
        app,
        [
            "index-summary",
            "--manifest",
            "examples/site-manifest.yaml",
            "--records",
            str(records),
        ],
    )

    assert result.exit_code != 0
    assert "projected record entries must be mappings" in result.output


def example_index() -> LocalReleaseIndex:
    return LocalReleaseIndex.build(
        manifest=load_site_manifest(Path("examples/site-manifest.yaml")),
        records=load_projected_records(Path("examples/projected-records.yaml")),
    )
