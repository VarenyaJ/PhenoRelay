from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from phenorelay.manifest import SiteManifest


class IndexError(ValueError):
    pass


@dataclass(frozen=True)
class ProjectedTerm:
    term: str
    label: str | None = None
    presence: str = "present"

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> ProjectedTerm:
        term = data.get("term")
        label = data.get("label")
        presence = data.get("presence", "present")
        if not isinstance(term, str) or not isinstance(presence, str):
            raise IndexError("projected terms require term and presence strings")
        if label is not None and not isinstance(label, str):
            raise IndexError("projected term labels must be strings when present")
        return cls(term=term, label=label, presence=presence)


@dataclass(frozen=True)
class ProjectedRecord:
    phenopacket_id: str
    subject_id_redacted: bool
    phenotypes: tuple[ProjectedTerm, ...]
    diseases: tuple[ProjectedTerm, ...]
    medical_actions: tuple[str, ...]
    has_genomic_interpretations: bool = False
    source_cohort: str | None = None
    source_filename: str | None = None
    source_pmids: tuple[str, ...] = ()
    genes: tuple[str, ...] = ()
    variant_descriptors: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> ProjectedRecord:
        phenopacket_id = data.get("phenopacket_id")
        subject_id_redacted = data.get("subject_id_redacted")
        if not isinstance(phenopacket_id, str) or not isinstance(subject_id_redacted, bool):
            raise IndexError("projected records require phenopacket_id and subject_id_redacted")

        return cls(
            phenopacket_id=phenopacket_id,
            subject_id_redacted=subject_id_redacted,
            phenotypes=parse_projected_terms(data.get("phenotypes") or []),
            diseases=parse_projected_terms(data.get("diseases") or []),
            medical_actions=parse_string_list(data.get("medical_actions") or [], "medical_actions"),
            has_genomic_interpretations=bool(data.get("has_genomic_interpretations", False)),
            source_cohort=parse_optional_string(data.get("source_cohort"), "source_cohort"),
            source_filename=parse_optional_string(data.get("source_filename"), "source_filename"),
            source_pmids=parse_string_list(data.get("source_pmids") or [], "source_pmids"),
            genes=parse_string_list(data.get("genes") or [], "genes"),
            variant_descriptors=parse_string_list(
                data.get("variant_descriptors") or [], "variant_descriptors"
            ),
        )


@dataclass(frozen=True)
class LocalReleaseIndex:
    manifest: SiteManifest
    records: tuple[ProjectedRecord, ...]
    generated_at: datetime

    @classmethod
    def build(
        cls,
        manifest: SiteManifest,
        records: tuple[ProjectedRecord, ...],
    ) -> LocalReleaseIndex:
        return cls(manifest=manifest, records=records, generated_at=datetime.now(UTC))

    def summary(self) -> dict[str, str | int]:
        return {
            "site_id": self.manifest.site_id,
            "release_id": self.manifest.release_id,
            "record_count": len(self.records),
            "backend_count": len(self.manifest.storage_backends),
            "generated_at": self.generated_at.isoformat(),
        }

    def query(self, request: dict[str, Any]) -> dict[str, Any]:
        query_id = require_string(request, "query_id")
        feature = require_string(request, "feature")
        granularity = request.get("requested_granularity", "count")
        if not isinstance(granularity, str):
            raise IndexError("requested_granularity must be a string")

        if granularity == "record":
            return unsupported(query_id, feature)
        if feature not in ("phenotype", "disease", "medical_action"):
            return unsupported(query_id, feature)

        match_mode = request.get("match_mode", "exact")
        if match_mode != "exact":
            return unsupported(query_id, feature)

        term = require_string(request, "term")
        count = self.count_exact(feature, term, request.get("presence", "present"))
        outcome: dict[str, Any] = {
            "query_id": query_id,
            "status": "match",
            "feature": feature,
            "exists": count > 0,
        }
        if granularity == "count":
            outcome["count"] = count
        elif granularity != "existence":
            return unsupported(query_id, feature)
        return outcome

    def count_exact(self, feature: str, term: str, presence: Any) -> int:
        if feature == "phenotype":
            return sum(
                any(
                    projected.term == term and matches_presence(projected.presence, presence)
                    for projected in record.phenotypes
                )
                for record in self.records
            )
        if feature == "disease":
            return sum(
                any(projected.term == term for projected in record.diseases)
                for record in self.records
            )
        if feature == "medical_action":
            return sum(term in record.medical_actions for record in self.records)
        raise IndexError(f"unsupported query feature: {feature}")


def load_projected_records(path: Path) -> tuple[ProjectedRecord, ...]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise IndexError("projected records file must contain a YAML mapping")
    raw_records = data.get("records")
    if not isinstance(raw_records, list):
        raise IndexError("projected records file requires a records list")
    records = []
    for item in raw_records:
        if not isinstance(item, dict):
            raise IndexError("projected record entries must be mappings")
        records.append(ProjectedRecord.from_mapping(item))
    return tuple(records)


def load_query_request(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise IndexError("query request must contain a YAML mapping")
    return data


def parse_projected_terms(value: Any) -> tuple[ProjectedTerm, ...]:
    if not isinstance(value, list):
        raise IndexError("projected term fields must be lists")
    terms = []
    for item in value:
        if not isinstance(item, dict):
            raise IndexError("projected term entries must be mappings")
        terms.append(ProjectedTerm.from_mapping(item))
    return tuple(terms)


def parse_string_list(value: Any, field: str) -> tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise IndexError(f"{field} must be a list of strings")
    return tuple(value)


def parse_optional_string(value: Any, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise IndexError(f"{field} must be a string when present")
    return value


def matches_presence(candidate: str, requested: Any) -> bool:
    return requested == "any" or candidate == requested


def require_string(data: dict[str, Any], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str):
        raise IndexError(f"{field} must be a string")
    return value


def unsupported(query_id: str, feature: str) -> dict[str, Any]:
    return {
        "query_id": query_id,
        "status": "unsupported",
        "feature": feature,
    }
