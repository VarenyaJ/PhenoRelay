from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


class ReferenceCacheError(ValueError):
    """Raised when a reviewed reference cache file cannot be used."""


@dataclass(frozen=True)
class ReferenceCacheEntry:
    reference: str
    text: str
    path: Path
    metadata: dict[str, Any]

    @classmethod
    def from_markdown(cls, path: Path) -> ReferenceCacheEntry:
        content = path.read_text(encoding="utf-8")
        metadata, text = _split_frontmatter(content, path)
        reference = metadata.get("reference")
        if not isinstance(reference, str) or not reference:
            raise ReferenceCacheError(f"{path} is missing a non-empty reference field")
        return cls(reference=reference, text=text, path=path, metadata=metadata)

    def contains(self, snippet: str) -> bool:
        return " ".join(snippet.split()) in " ".join(self.text.split())


def load_reference_cache(cache_dir: Path) -> dict[str, ReferenceCacheEntry]:
    if not cache_dir.exists():
        raise ReferenceCacheError(f"{cache_dir} does not exist")
    if not cache_dir.is_dir():
        raise ReferenceCacheError(f"{cache_dir} is not a directory")

    entries: dict[str, ReferenceCacheEntry] = {}
    for path in sorted(cache_dir.glob("*.md")):
        entry = ReferenceCacheEntry.from_markdown(path)
        if entry.reference in entries:
            first_path = entries[entry.reference].path
            raise ReferenceCacheError(
                f"duplicate reference {entry.reference} in {first_path} and {path}"
            )
        entries[entry.reference] = entry
    return entries


def _split_frontmatter(content: str, path: Path) -> tuple[dict[str, Any], str]:
    if not content.startswith("---\n"):
        raise ReferenceCacheError(f"{path} is missing YAML frontmatter")
    try:
        _, frontmatter, body = content.split("---\n", 2)
    except ValueError as exc:
        raise ReferenceCacheError(f"{path} has incomplete YAML frontmatter") from exc

    metadata = yaml.safe_load(frontmatter)
    if not isinstance(metadata, dict):
        raise ReferenceCacheError(f"{path} frontmatter must be a mapping")
    return metadata, body.strip()
