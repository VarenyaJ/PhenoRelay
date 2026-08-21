from __future__ import annotations

import csv
import json
from pathlib import Path
from textwrap import dedent

import pytest
from typer.testing import CliRunner

from phenorelay.cli import app
from phenorelay.index import load_projected_records
from phenorelay.manifest import load_site_manifest
from phenorelay.table_export import (
    TABLE_NAMES,
    TableExportError,
    TableExportSummary,
    build_release_tables,
    export_release_tables,
)


def test_build_release_tables_matches_projected_record_counts() -> None:
    tables = example_tables()

    assert set(tables) == set(TABLE_NAMES)
    assert len(tables["release_metadata"]) == 1
    assert len(tables["records"]) == 2
    assert len(tables["phenotypes"]) == 3
    assert len(tables["diseases"]) == 2
    assert len(tables["medical_actions"]) == 2


def test_build_release_tables_preserves_labels_and_presence() -> None:
    tables = example_tables()

    assert {
        (row["term"], row["label"], row["presence"]) for row in tables["phenotypes"]
    } == {
        ("HP:0001250", "Seizure", "present"),
        ("HP:0011344", "Severe global developmental delay", "excluded"),
        ("HP:0004322", "Short stature", "present"),
    }


def test_build_release_tables_omits_raw_subject_identifiers() -> None:
    tables = example_tables()

    record = tables["records"][0]
    assert "subject_id" not in record
    assert record["subject_id_redacted"] is True


def test_export_release_tables_writes_csv_files(tmp_path) -> None:
    summary = export_example_tables(tmp_path)

    assert summary.table_counts == {
        "release_metadata": 1,
        "records": 2,
        "phenotypes": 3,
        "diseases": 2,
        "medical_actions": 2,
    }
    for table_name in TABLE_NAMES:
        assert (tmp_path / f"{table_name}.csv").exists()

    phenotype_rows = read_csv_rows(tmp_path / "phenotypes.csv")
    assert phenotype_rows[0] == {
        "phenopacket_id": "synthetic-packet-1",
        "term": "HP:0001250",
        "label": "Seizure",
        "presence": "present",
    }


def test_export_release_tables_rejects_unsupported_format(tmp_path) -> None:
    with pytest.raises(TableExportError, match="only csv"):
        export_release_tables(
            manifest=load_site_manifest(Path("examples/site-manifest.yaml")),
            records=load_projected_records(Path("examples/projected-records.yaml")),
            out_dir=tmp_path,
            export_format="parquet",
        )


def test_export_tables_cli_writes_csv_files_and_summary(tmp_path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "export-tables",
            "--manifest",
            "examples/site-manifest.yaml",
            "--records",
            "examples/projected-records.yaml",
            "--out-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0
    output = json.loads(result.stdout)
    assert output["export"]["format"] == "csv"
    assert output["export"]["table_counts"]["phenotypes"] == 3
    assert (tmp_path / "records.csv").exists()


def test_export_tables_cli_with_hpo_validation_reports_clean_validation(tmp_path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "export-tables",
            "--manifest",
            "examples/site-manifest.yaml",
            "--records",
            "examples/projected-records.yaml",
            "--out-dir",
            str(tmp_path),
            "--validate-hpo",
            "tests/fixtures/hp-mini.json",
        ],
    )

    assert result.exit_code == 0
    output = json.loads(result.stdout)
    assert output["validation"]["ok"] is True
    assert output["validation"]["checked_term_count"] == 3
    assert output["export"]["table_counts"]["records"] == 2


def test_export_tables_cli_validation_failure_does_not_write_files(tmp_path) -> None:
    records = tmp_path / "bad-records.yaml"
    records.write_text(
        dedent(
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
            """
        ),
        encoding="utf-8",
    )
    out_dir = tmp_path / "tables"

    result = CliRunner().invoke(
        app,
        [
            "export-tables",
            "--manifest",
            "examples/site-manifest.yaml",
            "--records",
            str(records),
            "--out-dir",
            str(out_dir),
            "--validate-hpo",
            "tests/fixtures/hp-mini.json",
        ],
    )

    assert result.exit_code == 1
    assert not out_dir.exists()
    output = json.loads(result.stdout)
    assert output["validation"]["findings"][0]["code"] == "HPO001"


def test_export_tables_cli_rejects_unsupported_format(tmp_path) -> None:
    result = CliRunner().invoke(
        app,
        [
            "export-tables",
            "--manifest",
            "examples/site-manifest.yaml",
            "--records",
            "examples/projected-records.yaml",
            "--out-dir",
            str(tmp_path),
            "--format",
            "parquet",
        ],
    )

    assert result.exit_code != 0
    assert "only csv table export is implemented" in result.output


def example_tables() -> dict[str, list[dict[str, str | bool | int]]]:
    return build_release_tables(
        load_site_manifest(Path("examples/site-manifest.yaml")),
        load_projected_records(Path("examples/projected-records.yaml")),
    )


def export_example_tables(tmp_path) -> TableExportSummary:
    return export_release_tables(
        manifest=load_site_manifest(Path("examples/site-manifest.yaml")),
        records=load_projected_records(Path("examples/projected-records.yaml")),
        out_dir=tmp_path,
    )


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))
