from __future__ import annotations

import pytest

from phenorelay.reference_cache import (
    ReferenceCacheEntry,
    ReferenceCacheError,
    load_reference_cache,
)


def test_reference_cache_entry_reads_frontmatter(tmp_path) -> None:
    path = tmp_path / "PMID_00000000.md"
    path.write_text(
        "---\nreference: PMID:00000000\ntitle: Synthetic\n---\n\nQuoted evidence text.\n",
        encoding="utf-8",
    )

    entry = ReferenceCacheEntry.from_markdown(path)

    assert entry.reference == "PMID:00000000"
    assert entry.contains("Quoted evidence text.")


def test_load_reference_cache_rejects_duplicate_references(tmp_path) -> None:
    for name in ("a.md", "b.md"):
        (tmp_path / name).write_text(
            "---\nreference: PMID:00000000\n---\n\nText.\n",
            encoding="utf-8",
        )

    with pytest.raises(ReferenceCacheError, match="duplicate reference"):
        load_reference_cache(tmp_path)
