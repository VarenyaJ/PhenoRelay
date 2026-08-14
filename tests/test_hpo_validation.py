from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from phenorelay.cli import app
from phenorelay.hpo_validation import (
    HpoRelease,
    hpo_curie_from_iri,
    validate_projected_phenotypes,
)
from phenorelay.index import ProjectedRecord, ProjectedTerm, load_projected_records


def test_hpo_release_loads_terms_labels_synonyms_and_version() -> None:
    hpo = HpoRelease.from_json_path(Path("tests/fixtures/hp-mini.json"))

    assert hpo.version == "http://purl.obolibrary.org/obo/hp/releases/synthetic/hp.json"
    assert hpo.terms["HP:0001250"].label == "Seizure"
    assert "Epileptic seizure" in hpo.terms["HP:0001250"].synonyms


def test_hpo_curie_from_iri_converts_hp_iris() -> None:
    assert hpo_curie_from_iri("http://purl.obolibrary.org/obo/HP_0001250") == "HP:0001250"
    assert hpo_curie_from_iri("http://purl.obolibrary.org/obo/MONDO_0000001") is None


def test_validate_projected_phenotypes_accepts_matching_labels() -> None:
    hpo = HpoRelease.from_json_path(Path("tests/fixtures/hp-mini.json"))
    records = load_projected_records(Path("examples/projected-records.yaml"))

    report = validate_projected_phenotypes(records, hpo)

    assert report.ok
    assert report.checked_term_count == 3


def test_validate_projected_phenotypes_accepts_synonym_labels() -> None:
    hpo = HpoRelease.from_json_path(Path("tests/fixtures/hp-mini.json"))
    records = (
        ProjectedRecord(
            phenopacket_id="synthetic",
            subject_id_redacted=True,
            phenotypes=(
                ProjectedTerm(
                    term="HP:0001250",
                    label="Epileptic seizure",
                    presence="present",
                ),
            ),
            diseases=(),
            medical_actions=(),
        ),
    )

    report = validate_projected_phenotypes(records, hpo)

    assert report.ok


def test_validate_projected_phenotypes_reports_missing_id() -> None:
    hpo = HpoRelease.from_json_path(Path("tests/fixtures/hp-mini.json"))
    records = (
        ProjectedRecord(
            phenopacket_id="synthetic",
            subject_id_redacted=True,
            phenotypes=(ProjectedTerm(term="HP:9999999", label="Missing", presence="present"),),
            diseases=(),
            medical_actions=(),
        ),
    )

    report = validate_projected_phenotypes(records, hpo)

    assert not report.ok
    assert report.findings[0].code == "HPO001"


def test_validate_projected_phenotypes_reports_label_mismatch() -> None:
    hpo = HpoRelease.from_json_path(Path("tests/fixtures/hp-mini.json"))
    records = (
        ProjectedRecord(
            phenopacket_id="synthetic",
            subject_id_redacted=True,
            phenotypes=(ProjectedTerm(term="HP:0001250", label="Wrong label", presence="present"),),
            diseases=(),
            medical_actions=(),
        ),
    )

    report = validate_projected_phenotypes(records, hpo)

    assert not report.ok
    assert report.findings[0].code == "HPO002"
    assert report.findings[0].expected_label == "Seizure"


def test_validate_phenotypes_cli_exits_zero_for_clean_projected_records() -> None:
    result = CliRunner().invoke(
        app,
        [
            "validate-phenotypes",
            "--records",
            "examples/projected-records.yaml",
            "--hpo",
            "tests/fixtures/hp-mini.json",
        ],
    )

    assert result.exit_code == 0
    assert '"ok": true' in result.stdout
    assert '"checked_term_count": 3' in result.stdout


def test_validate_phenotypes_cli_exits_nonzero_for_bad_projected_records(tmp_path) -> None:
    records = tmp_path / "records.yaml"
    records.write_text(
        """
records:
  - phenopacket_id: synthetic
    subject_id_redacted: true
    phenotypes:
      - term: HP:9999999
        label: Missing
        presence: present
""",
        encoding="utf-8",
    )

    result = CliRunner().invoke(
        app,
        [
            "validate-phenotypes",
            "--records",
            str(records),
            "--hpo",
            "tests/fixtures/hp-mini.json",
        ],
    )

    assert result.exit_code == 1
    assert "HPO001" in result.stdout
