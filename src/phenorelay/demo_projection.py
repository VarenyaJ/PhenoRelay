from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from phenorelay.backends import BACKEND_CAPABILITIES
from phenorelay.demo_data import DEFAULT_OUT_DIR
from phenorelay.index import ProjectedRecord, ProjectedTerm

DEFAULT_DEMO_RECORDS = DEFAULT_OUT_DIR / "projected-records.yaml"
DEFAULT_DEMO_MANIFEST = DEFAULT_OUT_DIR / "site-manifest.yaml"
PMID_PATTERN = re.compile(r"PMID[_-](\d+)")


class DemoProjectionError(ValueError):
    pass


@dataclass(frozen=True)
class DemoProjectionSummary:
    source_dir: Path
    manifest_path: Path
    records_path: Path
    record_count: int
    cohort_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_dir": str(self.source_dir),
            "manifest_path": str(self.manifest_path),
            "records_path": str(self.records_path),
            "record_count": self.record_count,
            "cohort_counts": self.cohort_counts,
        }


def build_demo_release(
    *,
    demo_dir: Path = DEFAULT_OUT_DIR,
    records_path: Path = DEFAULT_DEMO_RECORDS,
    manifest_path: Path = DEFAULT_DEMO_MANIFEST,
) -> DemoProjectionSummary:
    source_dir = demo_dir / "source"
    if not source_dir.exists():
        raise DemoProjectionError(
            f"demo source directory does not exist: {source_dir}; run fetch-demo-phenopackets first"
        )

    records: list[ProjectedRecord] = []
    cohort_counts: dict[str, int] = {}
    for cohort_dir in sorted(path for path in source_dir.iterdir() if path.is_dir()):
        cohort_records = [
            project_phenopacket(path, cohort_dir.name)
            for path in sorted(cohort_dir.glob("*.json"))
        ]
        cohort_counts[cohort_dir.name] = len(cohort_records)
        records.extend(cohort_records)

    if not records:
        raise DemoProjectionError(f"no phenopacket JSON files found under {source_dir}")

    records_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    records_path.write_text(
        yaml.safe_dump(
            {"records": [record_to_mapping(record) for record in records]},
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    manifest_path.write_text(
        yaml.safe_dump(build_manifest_mapping(records), sort_keys=False),
        encoding="utf-8",
    )
    return DemoProjectionSummary(
        source_dir=source_dir,
        manifest_path=manifest_path,
        records_path=records_path,
        record_count=len(records),
        cohort_counts=cohort_counts,
    )


def project_phenopacket(path: Path, cohort: str) -> ProjectedRecord:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise DemoProjectionError(f"phenopacket JSON must contain an object: {path}")
    phenopacket_id = data.get("id")
    if not isinstance(phenopacket_id, str) or not phenopacket_id:
        raise DemoProjectionError(f"phenopacket requires a non-empty id: {path}")

    phenotypes = tuple(
        term
        for item in as_list(data.get("phenotypicFeatures"))
        if (term := project_phenotypic_feature(item)) is not None
    )
    diseases = tuple(
        term
        for item in as_list(data.get("diseases"))
        if (term := project_disease(item)) is not None
    )
    medical_actions = tuple(
        action
        for item in as_list(data.get("medicalActions"))
        for action in project_medical_action(item)
    )
    genes, variant_descriptors = project_interpretations(as_list(data.get("interpretations")))

    return ProjectedRecord(
        phenopacket_id=phenopacket_id,
        subject_id_redacted=True,
        phenotypes=phenotypes,
        diseases=diseases,
        medical_actions=dedupe_sorted(medical_actions),
        has_genomic_interpretations=bool(genes or variant_descriptors),
        source_cohort=cohort,
        source_filename=path.name,
        source_pmids=pmids_from_filename(path.name),
        genes=dedupe_sorted(genes),
        variant_descriptors=dedupe_sorted(variant_descriptors),
    )


def project_phenotypic_feature(item: Any) -> ProjectedTerm | None:
    if not isinstance(item, dict):
        return None
    term = ontology_term(item.get("type"))
    if term is None:
        return None
    return ProjectedTerm(
        term=term["id"],
        label=term.get("label"),
        presence="excluded" if item.get("excluded") is True else "present",
    )


def project_disease(item: Any) -> ProjectedTerm | None:
    if not isinstance(item, dict):
        return None
    term = ontology_term(item.get("term") or item.get("disease"))
    if term is None:
        return None
    return ProjectedTerm(term=term["id"], label=term.get("label"), presence="present")


def project_medical_action(item: Any) -> tuple[str, ...]:
    if not isinstance(item, dict):
        return ()
    terms = []
    for key in ("procedure", "treatment", "radiationTherapy", "therapeuticRegimen"):
        projected = ontology_term(item.get(key))
        if projected is not None:
            terms.append(projected["id"])
    return tuple(terms)


def project_interpretations(items: list[Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    genes: list[str] = []
    variants: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        diagnosis = item.get("diagnosis")
        if not isinstance(diagnosis, dict):
            continue
        for interpretation in as_list(diagnosis.get("genomicInterpretations")):
            if not isinstance(interpretation, dict):
                continue
            variant = interpretation.get("variantInterpretation")
            if not isinstance(variant, dict):
                continue
            descriptor = variant.get("variationDescriptor")
            if not isinstance(descriptor, dict):
                continue
            if isinstance(descriptor.get("id"), str):
                variants.append(descriptor["id"])
            gene = descriptor.get("geneContext")
            if isinstance(gene, dict):
                symbol = gene.get("symbol")
                value_id = gene.get("valueId")
                if isinstance(symbol, str):
                    genes.append(symbol)
                elif isinstance(value_id, str):
                    genes.append(value_id)
    return tuple(genes), tuple(variants)


def ontology_term(value: Any) -> dict[str, str] | None:
    if not isinstance(value, dict):
        return None
    term_id = value.get("id")
    label = value.get("label")
    if not isinstance(term_id, str):
        return None
    projected = {"id": term_id}
    if isinstance(label, str):
        projected["label"] = label
    return projected


def as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def pmids_from_filename(filename: str) -> tuple[str, ...]:
    return tuple(f"PMID:{match}" for match in PMID_PATTERN.findall(filename))


def dedupe_sorted(values: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    return tuple(sorted(set(values)))


def record_to_mapping(record: ProjectedRecord) -> dict[str, Any]:
    data: dict[str, Any] = {
        "phenopacket_id": record.phenopacket_id,
        "subject_id_redacted": record.subject_id_redacted,
        "phenotypes": [term_to_mapping(term) for term in record.phenotypes],
        "diseases": [term_to_mapping(term) for term in record.diseases],
        "medical_actions": list(record.medical_actions),
        "has_genomic_interpretations": record.has_genomic_interpretations,
    }
    optional_fields = {
        "source_cohort": record.source_cohort,
        "source_filename": record.source_filename,
        "source_pmids": list(record.source_pmids),
        "genes": list(record.genes),
        "variant_descriptors": list(record.variant_descriptors),
    }
    for key, value in optional_fields.items():
        if value:
            data[key] = value
    return data


def term_to_mapping(term: ProjectedTerm) -> dict[str, str]:
    data = {"term": term.term, "presence": term.presence}
    if term.label is not None:
        data["label"] = term.label
    return data


def build_manifest_mapping(records: list[ProjectedRecord]) -> dict[str, Any]:
    return {
        "site_id": "phenorelay-demo",
        "site_name": "PhenoRelay Public Demo",
        "release_id": f"phenorelay-demo-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
        "phenopacket_schema_version": "2.0",
        "ontology_releases": [
            {"ontology_prefix": "HP", "ontology_version": "local"},
            {"ontology_prefix": "MONDO", "ontology_version": "source"},
            {"ontology_prefix": "OMIM", "ontology_version": "source"},
            {"ontology_prefix": "ORPHA", "ontology_version": "source"},
        ],
        "supported_features": ["phenotype", "disease", "medical_action"],
        "supported_granularities": ["existence", "count"],
        "record_count": len(records),
        "storage_backends": [
            capability.to_dict()
            for capability in BACKEND_CAPABILITIES
            if capability.kind in {"memory", "sqlite", "postgres", "trino"}
        ],
    }
