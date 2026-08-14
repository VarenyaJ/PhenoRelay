from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from phenorelay.index import ProjectedRecord

HPO_IRI_PREFIX = "http://purl.obolibrary.org/obo/HP_"
VERSION_PREDICATE = "http://www.w3.org/2002/07/owl#versionInfo"


class HpoValidationError(ValueError):
    pass


@dataclass(frozen=True)
class HpoTerm:
    term_id: str
    label: str
    synonyms: tuple[str, ...]

    def accepts_label(self, label: str) -> bool:
        return label == self.label or label in self.synonyms


@dataclass(frozen=True)
class HpoRelease:
    version: str | None
    terms: dict[str, HpoTerm]

    @classmethod
    def from_json_path(cls, path: Path) -> HpoRelease:
        data = json.loads(path.read_text(encoding="utf-8"))
        graphs = data.get("graphs")
        if not isinstance(graphs, list) or not graphs:
            raise HpoValidationError("HPO JSON must contain at least one graph")
        graph = graphs[0]
        if not isinstance(graph, dict):
            raise HpoValidationError("HPO graph must be a mapping")

        version = extract_version(graph)
        nodes = graph.get("nodes")
        if not isinstance(nodes, list):
            raise HpoValidationError("HPO graph must contain a nodes list")

        terms: dict[str, HpoTerm] = {}
        for node in nodes:
            if not isinstance(node, dict):
                continue
            term_id = hpo_curie_from_iri(node.get("id"))
            label = node.get("lbl")
            if term_id is None or not isinstance(label, str):
                continue
            terms[term_id] = HpoTerm(
                term_id=term_id,
                label=label,
                synonyms=tuple(extract_synonyms(node)),
            )
        if not terms:
            raise HpoValidationError("HPO graph did not contain any HP terms")
        return cls(version=version, terms=terms)


@dataclass(frozen=True)
class PhenotypeValidationFinding:
    severity: str
    code: str
    message: str
    phenopacket_id: str
    term: str
    expected_label: str | None = None
    observed_label: str | None = None

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "severity": self.severity,
            "code": self.code,
            "message": self.message,
            "phenopacket_id": self.phenopacket_id,
            "term": self.term,
        }
        if self.expected_label is not None:
            result["expected_label"] = self.expected_label
        if self.observed_label is not None:
            result["observed_label"] = self.observed_label
        return result


@dataclass(frozen=True)
class PhenotypeValidationReport:
    hpo_version: str | None
    checked_term_count: int
    findings: tuple[PhenotypeValidationFinding, ...]

    @property
    def ok(self) -> bool:
        return not self.findings

    def to_dict(self) -> dict[str, Any]:
        return {
            "hpo_version": self.hpo_version,
            "checked_term_count": self.checked_term_count,
            "ok": self.ok,
            "finding_count": len(self.findings),
            "findings": [finding.to_dict() for finding in self.findings],
        }


def validate_projected_phenotypes(
    records: tuple[ProjectedRecord, ...],
    hpo: HpoRelease,
) -> PhenotypeValidationReport:
    findings: list[PhenotypeValidationFinding] = []
    checked = 0
    for record in records:
        for phenotype in record.phenotypes:
            checked += 1
            term = hpo.terms.get(phenotype.term)
            if term is None:
                findings.append(
                    PhenotypeValidationFinding(
                        severity="error",
                        code="HPO001",
                        message="Phenotype term ID is not present in the HPO release",
                        phenopacket_id=record.phenopacket_id,
                        term=phenotype.term,
                        observed_label=phenotype.label,
                    )
                )
                continue
            if phenotype.label is not None and not term.accepts_label(phenotype.label):
                findings.append(
                    PhenotypeValidationFinding(
                        severity="error",
                        code="HPO002",
                        message="Phenotype label does not match the HPO release label or synonym",
                        phenopacket_id=record.phenopacket_id,
                        term=phenotype.term,
                        expected_label=term.label,
                        observed_label=phenotype.label,
                    )
                )
    return PhenotypeValidationReport(
        hpo_version=hpo.version,
        checked_term_count=checked,
        findings=tuple(findings),
    )


def hpo_curie_from_iri(value: Any) -> str | None:
    if not isinstance(value, str) or not value.startswith(HPO_IRI_PREFIX):
        return None
    return "HP:" + value.removeprefix(HPO_IRI_PREFIX)


def extract_version(graph: dict[str, Any]) -> str | None:
    meta = graph.get("meta")
    if not isinstance(meta, dict):
        return None
    version = meta.get("version")
    if isinstance(version, str):
        return version
    for item in meta.get("basicPropertyValues") or []:
        if (
            isinstance(item, dict)
            and item.get("pred") == VERSION_PREDICATE
            and isinstance(item.get("val"), str)
        ):
            return item["val"]
    return None


def extract_synonyms(node: dict[str, Any]) -> list[str]:
    meta = node.get("meta")
    if not isinstance(meta, dict):
        return []
    synonyms = []
    for item in meta.get("synonyms") or []:
        if isinstance(item, dict) and isinstance(item.get("val"), str):
            synonyms.append(item["val"])
    return synonyms
