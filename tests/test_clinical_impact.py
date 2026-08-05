from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from phenorelay.cli import app
from phenorelay.clinical_impact import (
    ClinicalImpactError,
    load_clinical_impact_annotations,
    summarize_clinical_impact,
)


def test_load_clinical_impact_annotations_reads_synthetic_example() -> None:
    annotations = load_clinical_impact_annotations(Path("examples/clinical-impact.yaml"))

    assert len(annotations) == 2
    assert annotations[0].subject == "OMIM:154700"
    assert annotations[0].derived_tier == "pregnancy_critical"


def test_summarize_clinical_impact_counts_axes_and_tiers() -> None:
    annotations = load_clinical_impact_annotations(Path("examples/clinical-impact.yaml"))

    summary = summarize_clinical_impact(annotations)

    assert summary["annotation_count"] == 2
    assert summary["reviewed_count"] == 1
    assert summary["axis_counts"] == {
        "neurodevelopmental_impact": 1,
        "pregnancy_maternal_impact": 1,
    }
    assert summary["tier_counts"] == {
        "longitudinal_prognostic_complexity": 1,
        "pregnancy_critical": 1,
    }


def test_load_clinical_impact_annotations_rejects_missing_required_field(tmp_path) -> None:
    path = tmp_path / "impact.yaml"
    path.write_text(
        """
annotations:
  - impact_id: broken
    subject: OMIM:154700
""",
        encoding="utf-8",
    )

    try:
        load_clinical_impact_annotations(path)
    except ClinicalImpactError as exc:
        assert "missing string fields" in str(exc)
    else:
        raise AssertionError("expected ClinicalImpactError")


def test_impact_summary_cli_prints_annotation_summary() -> None:
    result = CliRunner().invoke(
        app,
        [
            "impact-summary",
            "--annotations",
            "examples/clinical-impact.yaml",
        ],
    )

    assert result.exit_code == 0
    assert '"annotation_count": 2' in result.stdout
    assert '"pregnancy_critical": 1' in result.stdout
