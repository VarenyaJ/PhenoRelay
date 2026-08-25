from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from phenorelay.index import LocalReleaseIndex, ProjectedRecord, ProjectedTerm


@dataclass(frozen=True)
class FilteringTerm:
    feature: str
    term: str
    label: str | None
    presence: str | None
    count: int

    def to_dict(self) -> dict[str, str | int | None]:
        return {
            "feature": self.feature,
            "term": self.term,
            "label": self.label,
            "presence": self.presence,
            "count": self.count,
        }


class QueryService:
    def __init__(self, index: LocalReleaseIndex) -> None:
        self.index = index

    def release_metadata(self) -> dict[str, str | int]:
        return self.index.summary()

    def pheno_info(self) -> dict[str, Any]:
        return {
            "service": "PhenoRelay",
            "api": "pheno",
            "release": self.release_metadata(),
            "supported_features": ["phenotype", "disease", "medical_action"],
            "supported_granularities": ["existence", "count"],
            "record_detail_default": "disabled",
        }

    def query(self, request: dict[str, Any]) -> dict[str, Any]:
        return {
            "release": self.release_metadata(),
            "outcome": self.index.query(request),
        }

    def filtering_terms(self) -> list[dict[str, str | int | None]]:
        return [term.to_dict() for term in build_filtering_terms(self.index.records)]

    def record_summaries(self) -> list[dict[str, str | bool | int]]:
        return [
            {
                "phenopacket_id": record.phenopacket_id,
                "subject_id_redacted": record.subject_id_redacted,
                "phenotype_count": len(record.phenotypes),
                "disease_count": len(record.diseases),
                "medical_action_count": len(record.medical_actions),
                "has_genomic_interpretations": record.has_genomic_interpretations,
            }
            for record in self.index.records
        ]


def build_filtering_terms(records: tuple[ProjectedRecord, ...]) -> list[FilteringTerm]:
    phenotype_counts: dict[tuple[str, str | None, str], int] = {}
    disease_counts: dict[tuple[str, str | None, str], int] = {}
    action_counts: dict[str, int] = {}

    for record in records:
        add_projected_terms(phenotype_counts, record.phenotypes)
        add_projected_terms(disease_counts, record.diseases)
        for action in set(record.medical_actions):
            action_counts[action] = action_counts.get(action, 0) + 1

    terms = [
        FilteringTerm("phenotype", term, label, presence, count)
        for (term, label, presence), count in phenotype_counts.items()
    ]
    terms.extend(
        FilteringTerm("disease", term, label, presence, count)
        for (term, label, presence), count in disease_counts.items()
    )
    terms.extend(
        FilteringTerm("medical_action", term, None, None, count)
        for term, count in action_counts.items()
    )
    return sorted(terms, key=lambda item: (item.feature, item.term, item.presence or ""))


def add_projected_terms(
    counts: dict[tuple[str, str | None, str], int],
    terms: tuple[ProjectedTerm, ...],
) -> None:
    seen = {(term.term, term.label, term.presence) for term in terms}
    for key in seen:
        counts[key] = counts.get(key, 0) + 1
