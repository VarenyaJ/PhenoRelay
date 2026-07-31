from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from phenorelay.backends import BackendCapabilities


class ManifestError(ValueError):
    pass


@dataclass(frozen=True)
class SiteManifest:
    site_id: str
    release_id: str
    storage_backends: tuple[BackendCapabilities, ...]

    @classmethod
    def from_mapping(cls, data: dict[str, Any]) -> SiteManifest:
        site_id = data.get("site_id")
        release_id = data.get("release_id")
        if not isinstance(site_id, str) or not isinstance(release_id, str):
            raise ManifestError("site manifest requires site_id and release_id")

        raw_backends = data.get("storage_backends") or []
        if not isinstance(raw_backends, list):
            raise ManifestError("storage_backends must be a list")

        try:
            storage_backends = tuple(
                BackendCapabilities.from_mapping(item)
                for item in raw_backends
                if isinstance(item, dict)
            )
        except ValueError as exc:
            raise ManifestError(str(exc)) from exc
        if len(storage_backends) != len(raw_backends):
            raise ManifestError("storage_backends entries must be mappings")

        return cls(
            site_id=site_id,
            release_id=release_id,
            storage_backends=storage_backends,
        )


def load_site_manifest(path: Path) -> SiteManifest:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ManifestError("site manifest must contain a YAML mapping")
    return SiteManifest.from_mapping(data)
