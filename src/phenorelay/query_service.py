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
            "supported_features": [
                "cohort",
                "phenotype",
                "disease",
                "medical_action",
                "gene",
                "source_pmid",
                "genomic_interpretation",
            ],
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

    def record_summaries(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        records = filter_records(self.index.records, filters or {})
        return [
            {
                "phenopacket_id": record.phenopacket_id,
                "subject_id_redacted": record.subject_id_redacted,
                "source_cohort": record.source_cohort,
                "source_filename": record.source_filename,
                "source_pmids": ", ".join(record.source_pmids),
                "phenotype_count": len(record.phenotypes),
                "disease_count": len(record.diseases),
                "medical_action_count": len(record.medical_actions),
                "has_genomic_interpretations": record.has_genomic_interpretations,
                "gene_count": len(record.genes),
                "variant_descriptor_count": len(record.variant_descriptors),
            }
            for record in records
        ]

    def record_detail(self, phenopacket_id: str) -> dict[str, Any] | None:
        record = self.find_record(phenopacket_id)
        if record is None:
            return None
        return {
            "phenopacket_id": record.phenopacket_id,
            "subject_id_redacted": record.subject_id_redacted,
            "source_cohort": record.source_cohort,
            "source_filename": record.source_filename,
            "source_pmids": list(record.source_pmids),
            "phenotypes": [term_to_dict(term) for term in record.phenotypes],
            "diseases": [term_to_dict(term) for term in record.diseases],
            "medical_actions": list(record.medical_actions),
            "has_genomic_interpretations": record.has_genomic_interpretations,
            "genes": list(record.genes),
            "variant_descriptors": list(record.variant_descriptors),
        }

    def find_record(self, phenopacket_id: str) -> ProjectedRecord | None:
        for record in self.index.records:
            if record.phenopacket_id == phenopacket_id:
                return record
        return None


def build_filtering_terms(records: tuple[ProjectedRecord, ...]) -> list[FilteringTerm]:
    cohort_counts: dict[str, int] = {}
    phenotype_counts: dict[tuple[str, str | None, str], int] = {}
    disease_counts: dict[tuple[str, str | None, str], int] = {}
    action_counts: dict[str, int] = {}
    gene_counts: dict[str, int] = {}
    pmid_counts: dict[str, int] = {}
    genomic_counts: dict[str, int] = {}

    for record in records:
        if record.source_cohort:
            cohort_counts[record.source_cohort] = cohort_counts.get(record.source_cohort, 0) + 1
        add_projected_terms(phenotype_counts, record.phenotypes)
        add_projected_terms(disease_counts, record.diseases)
        for action in set(record.medical_actions):
            action_counts[action] = action_counts.get(action, 0) + 1
        for gene in set(record.genes):
            gene_counts[gene] = gene_counts.get(gene, 0) + 1
        for pmid in set(record.source_pmids):
            pmid_counts[pmid] = pmid_counts.get(pmid, 0) + 1
        genomic_key = "true" if record.has_genomic_interpretations else "false"
        genomic_counts[genomic_key] = genomic_counts.get(genomic_key, 0) + 1

    terms = [
        FilteringTerm("phenotype", term, label, presence, count)
        for (term, label, presence), count in phenotype_counts.items()
    ]
    terms.extend(
        FilteringTerm("cohort", term, None, None, count)
        for term, count in cohort_counts.items()
    )
    terms.extend(
        FilteringTerm("disease", term, label, presence, count)
        for (term, label, presence), count in disease_counts.items()
    )
    terms.extend(
        FilteringTerm("medical_action", term, None, None, count)
        for term, count in action_counts.items()
    )
    terms.extend(
        FilteringTerm("gene", term, None, None, count) for term, count in gene_counts.items()
    )
    terms.extend(
        FilteringTerm("source_pmid", term, None, None, count) for term, count in pmid_counts.items()
    )
    terms.extend(
        FilteringTerm("genomic_interpretation", term, None, None, count)
        for term, count in genomic_counts.items()
    )
    return sorted(terms, key=lambda item: (item.feature, item.term, item.presence or ""))


def filter_records(
    records: tuple[ProjectedRecord, ...],
    filters: dict[str, Any],
) -> tuple[ProjectedRecord, ...]:
    return tuple(record for record in records if record_matches_filters(record, filters))


def record_matches_filters(record: ProjectedRecord, filters: dict[str, Any]) -> bool:
    cohort = normalized_filter(filters.get("cohort"))
    if cohort and record.source_cohort != cohort:
        return False

    phenotype = normalized_filter(filters.get("phenotype"))
    if phenotype:
        presence = normalized_filter(filters.get("phenotype_presence")) or "present"
        if not any(
            term.term == phenotype and term.presence == presence for term in record.phenotypes
        ):
            return False

    disease = normalized_filter(filters.get("disease"))
    if disease and not any(term.term == disease for term in record.diseases):
        return False

    gene = normalized_filter(filters.get("gene"))
    if gene and gene not in record.genes:
        return False

    source_pmid = normalized_filter(filters.get("source_pmid"))
    if source_pmid and source_pmid not in record.source_pmids:
        return False

    has_genomics = normalized_filter(filters.get("has_genomic_interpretations"))
    if has_genomics:
        requested = has_genomics.lower()
        if requested in {"true", "yes", "1"} and not record.has_genomic_interpretations:
            return False
        if requested in {"false", "no", "0"} and record.has_genomic_interpretations:
            return False

    text = normalized_filter(filters.get("text"))
    if text and text.lower() not in searchable_record_text(record).lower():
        return False

    return True


def normalized_filter(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def searchable_record_text(record: ProjectedRecord) -> str:
    values = [
        record.phenopacket_id,
        record.source_cohort or "",
        record.source_filename or "",
        *record.source_pmids,
        *record.genes,
        *record.variant_descriptors,
    ]
    values.extend(term.term for term in record.phenotypes)
    values.extend(term.label or "" for term in record.phenotypes)
    values.extend(term.term for term in record.diseases)
    values.extend(term.label or "" for term in record.diseases)
    return " ".join(values)


def term_to_dict(term: ProjectedTerm) -> dict[str, str | None]:
    return {
        "term": term.term,
        "label": term.label,
        "presence": term.presence,
    }


def add_projected_terms(
    counts: dict[tuple[str, str | None, str], int],
    terms: tuple[ProjectedTerm, ...],
) -> None:
    seen = {(term.term, term.label, term.presence) for term in terms}
    for key in seen:
        counts[key] = counts.get(key, 0) + 1
