from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from phenorelay.reference_cache import ReferenceCacheEntry


@dataclass(frozen=True)
class EvidenceCheck:
    reference: str
    support: str
    snippet: str
    reference_cached: bool
    snippet_found: bool

    @property
    def ok(self) -> bool:
        return self.reference_cached and self.snippet_found

    def to_dict(self) -> dict[str, Any]:
        return {
            "reference": self.reference,
            "support": self.support,
            "reference_cached": self.reference_cached,
            "snippet_found": self.snippet_found,
            "ok": self.ok,
        }


def check_evidence_snippets(
    outcome: Mapping[str, Any],
    cache: Mapping[str, ReferenceCacheEntry],
) -> list[EvidenceCheck]:
    checks: list[EvidenceCheck] = []
    for item in outcome.get("evidence") or []:
        if not isinstance(item, Mapping):
            continue
        reference = item.get("reference")
        snippet = item.get("snippet")
        support = item.get("support")
        if not isinstance(reference, str) or not isinstance(snippet, str):
            continue
        entry = cache.get(reference)
        checks.append(
            EvidenceCheck(
                reference=reference,
                support=support if isinstance(support, str) else "",
                snippet=snippet,
                reference_cached=entry is not None,
                snippet_found=entry.contains(snippet) if entry is not None else False,
            )
        )
    return checks
