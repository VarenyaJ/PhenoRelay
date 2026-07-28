from __future__ import annotations

from phenorelay.evidence import check_evidence_snippets
from phenorelay.reference_cache import ReferenceCacheEntry


def test_check_evidence_snippets_matches_cached_text(tmp_path) -> None:
    entry = ReferenceCacheEntry(
        reference="PMID:00000000",
        text="Synthetic placeholder text for schema validation.",
        path=tmp_path / "PMID_00000000.md",
        metadata={"reference": "PMID:00000000"},
    )

    checks = check_evidence_snippets(
        {
            "evidence": [
                {
                    "reference": "PMID:00000000",
                    "snippet": "Synthetic placeholder text for schema validation.",
                    "support": "support",
                }
            ]
        },
        {"PMID:00000000": entry},
    )

    assert len(checks) == 1
    assert checks[0].ok


def test_check_evidence_snippets_reports_missing_cache() -> None:
    checks = check_evidence_snippets(
        {
            "evidence": [
                {
                    "reference": "PMID:00000000",
                    "snippet": "Synthetic placeholder text for schema validation.",
                    "support": "support",
                }
            ]
        },
        {},
    )

    assert not checks[0].reference_cached
    assert not checks[0].ok
