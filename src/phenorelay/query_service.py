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
                "variant_descriptor",
            ],
            "supported_granularities": ["existence", "count"],
            "record_detail_default": "disabled",
        }

    def query(self, request: dict[str, Any]) -> dict[str, Any]:
        return {
            "release": self.release_metadata(),
            "outcome": self.query_outcome(request),
        }

    def query_outcome(self, request: dict[str, Any]) -> dict[str, Any]:
        query_id = required_query_string(request, "query_id")
        feature = required_query_string(request, "feature")
        granularity = request.get("requested_granularity", "count")
        if granularity not in {"existence", "count", "record"}:
            return unsupported(query_id, feature)

        match_mode = request.get("match_mode", "exact")
        if match_mode != "exact":
            return unsupported(query_id, feature)

        filters = query_filters(request)
        if filters is None:
            return unsupported(query_id, feature)
        records = filter_records(self.index.records, filters)
        outcome: dict[str, Any] = {
            "query_id": query_id,
            "status": "match",
            "feature": feature,
            "exists": bool(records),
        }
        if granularity in {"count", "record"}:
            outcome["count"] = len(records)
        if granularity == "record":
            outcome["records"] = [self.projected_record(record) for record in records]
        return outcome

    def filtering_terms(self) -> list[dict[str, str | int | None]]:
        return [term.to_dict() for term in build_filtering_terms(self.index.records)]

    def record_summaries(self, filters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        records = filter_records(self.index.records, filters or {})
        return [self.record_summary(record) for record in records]

    def record_summary(self, record: ProjectedRecord) -> dict[str, Any]:
        return {
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

    def record_detail(self, phenopacket_id: str) -> dict[str, Any] | None:
        record = self.find_record(phenopacket_id)
        if record is None:
            return None
        return self.projected_record(record)

    def projected_record(self, record: ProjectedRecord) -> dict[str, Any]:
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

    medical_action = normalized_filter(filters.get("medical_action"))
    if medical_action and medical_action not in record.medical_actions:
        return False

    gene = normalized_filter(filters.get("gene"))
    if gene and gene not in record.genes:
        return False

    variant_descriptor = normalized_filter(filters.get("variant_descriptor"))
    if variant_descriptor and variant_descriptor not in record.variant_descriptors:
        return False

    source_pmid = normalized_filter(filters.get("source_pmid"))
    if source_pmid and source_pmid not in record.source_pmids:
        return False

    requested_genomics = normalized_bool_filter(filters.get("has_genomic_interpretations"))
    if requested_genomics is not None and record.has_genomic_interpretations != requested_genomics:
        return False

    text = normalized_filter(filters.get("text"))
    if text and text.lower() not in searchable_record_text(record).lower():
        return False

    return True


def query_filters(request: dict[str, Any]) -> dict[str, Any] | None:
    feature = required_query_string(request, "feature")
    filters: dict[str, Any] = {
        "cohort": request.get("cohort"),
        "gene": request.get("gene"),
        "source_pmid": request.get("source_pmid"),
        "has_genomic_interpretations": request.get("has_genomic_interpretations"),
        "variant_descriptor": request.get("variant_descriptor"),
        "text": request.get("text"),
    }
    if feature == "phenotype":
        filters["phenotype"] = required_query_string(request, "term")
        filters["phenotype_presence"] = request.get("presence", "present")
    elif feature == "disease":
        filters["disease"] = required_query_string(request, "term")
    elif feature == "medical_action":
        filters["medical_action"] = required_query_string(request, "term")
    elif feature == "gene":
        filters["gene"] = required_query_string(request, "term")
    elif feature == "cohort":
        filters["cohort"] = required_query_string(request, "term")
    elif feature == "source_pmid":
        filters["source_pmid"] = required_query_string(request, "term")
    elif feature == "genomic_interpretation":
        filters["has_genomic_interpretations"] = required_query_string(request, "term")
    elif feature == "variant_descriptor":
        filters["variant_descriptor"] = required_query_string(request, "term")
    else:
        return None
    return filters


def required_query_string(data: dict[str, Any], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str):
        raise ValueError(f"{field} must be a string")
    return value


def unsupported(query_id: str, feature: str) -> dict[str, Any]:
    return {
        "query_id": query_id,
        "status": "unsupported",
        "feature": feature,
    }


def normalized_filter(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


def normalized_bool_filter(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if not isinstance(value, str):
        return None
    stripped = value.strip().lower()
    if stripped in {"true", "yes", "1"}:
        return True
    if stripped in {"false", "no", "0"}:
        return False
    return None


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
