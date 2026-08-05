from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ClinicalImpactError(ValueError):
    pass


@dataclass(frozen=True)
class ClinicalImpactAnnotation:
    impact_id: str
    subject: str
    subject_kind: str
    axis: str
    predicate: str
    source_id: str
    extraction_method: str
    review_status: str
    derived_tier: str | None = None
    confidence: float | None = None
    snippet: str | None = None

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> ClinicalImpactAnnotation:
        required = [
            "impact_id",
            "subject",
            "subject_kind",
            "axis",
            "predicate",
            "source_id",
            "extraction_method",
            "review_status",
        ]
        missing = [key for key in required if not isinstance(data.get(key), str)]
        if missing:
            raise ClinicalImpactError(
                "clinical impact annotation is missing string fields: " + ", ".join(missing)
            )

        confidence = data.get("confidence")
        if confidence is not None and not isinstance(confidence, int | float):
            raise ClinicalImpactError("clinical impact confidence must be numeric when present")

        snippet = data.get("snippet")
        if snippet is not None and not isinstance(snippet, str):
            raise ClinicalImpactError("clinical impact snippet must be a string when present")

        derived_tier = data.get("derived_tier")
        if derived_tier is not None and not isinstance(derived_tier, str):
            raise ClinicalImpactError("clinical impact derived_tier must be a string when present")

        return cls(
            impact_id=data["impact_id"],
            subject=data["subject"],
            subject_kind=data["subject_kind"],
            axis=data["axis"],
            predicate=data["predicate"],
            source_id=data["source_id"],
            extraction_method=data["extraction_method"],
            review_status=data["review_status"],
            derived_tier=derived_tier,
            confidence=float(confidence) if confidence is not None else None,
            snippet=snippet,
        )


def load_clinical_impact_annotations(path: Path) -> list[ClinicalImpactAnnotation]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping):
        raise ClinicalImpactError("clinical impact file must contain a YAML mapping")
    annotations = data.get("annotations")
    if not isinstance(annotations, list):
        raise ClinicalImpactError("clinical impact file must contain an annotations list")
    return [ClinicalImpactAnnotation.from_mapping(_require_mapping(item)) for item in annotations]


def summarize_clinical_impact(
    annotations: list[ClinicalImpactAnnotation],
) -> dict[str, Any]:
    axis_counts = Counter(annotation.axis for annotation in annotations)
    tier_counts = Counter(
        annotation.derived_tier for annotation in annotations if annotation.derived_tier
    )
    predicate_counts = Counter(annotation.predicate for annotation in annotations)
    source_counts = Counter(annotation.source_id for annotation in annotations)
    reviewed_count = sum(1 for annotation in annotations if annotation.review_status == "reviewed")

    return {
        "annotation_count": len(annotations),
        "reviewed_count": reviewed_count,
        "axis_counts": dict(sorted(axis_counts.items())),
        "tier_counts": dict(sorted(tier_counts.items())),
        "predicate_counts": dict(sorted(predicate_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
    }


def _require_mapping(item: Any) -> Mapping[str, Any]:
    if not isinstance(item, Mapping):
        raise ClinicalImpactError("clinical impact annotation entries must be mappings")
    return item
