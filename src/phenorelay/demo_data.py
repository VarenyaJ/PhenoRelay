from __future__ import annotations

import hashlib
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

DEFAULT_COHORTS = ("PTPN11", "KRAS", "ABCA4")
DEFAULT_STORE = Path("phenopacket-store")
DEFAULT_OUT_DIR = Path(".phenorelay-demo/phenopacket-store-sample")
UPSTREAM_REPOSITORY = "https://github.com/monarch-initiative/phenopacket-store"


class DemoDataError(ValueError):
    pass


@dataclass(frozen=True)
class DemoFetchSummary:
    source: Path
    out_dir: Path
    cohort_counts: dict[str, int]
    manifest_path: Path

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": str(self.source),
            "out_dir": str(self.out_dir),
            "cohort_counts": self.cohort_counts,
            "manifest_path": str(self.manifest_path),
        }


def fetch_demo_phenopackets(
    *,
    source: Path = DEFAULT_STORE,
    out_dir: Path = DEFAULT_OUT_DIR,
    cohorts: tuple[str, ...] = DEFAULT_COHORTS,
) -> DemoFetchSummary:
    if not source.exists():
        raise DemoDataError(f"Phenopacket Store clone does not exist: {source}")
    source_commit = read_git_commit(source)
    license_text = read_license(source)
    copied_files: list[dict[str, str | int]] = []
    cohort_counts: dict[str, int] = {}
    source_root = out_dir / "source"
    source_root.mkdir(parents=True, exist_ok=True)

    for cohort in cohorts:
        cohort_source = source / "notebooks" / cohort / "phenopackets"
        if not cohort_source.exists():
            raise DemoDataError(f"cohort phenopacket directory does not exist: {cohort_source}")
        cohort_target = source_root / cohort
        cohort_target.mkdir(parents=True, exist_ok=True)
        records = sorted(cohort_source.glob("*.json"))
        cohort_counts[cohort] = len(records)
        for record in records:
            target = cohort_target / record.name
            shutil.copyfile(record, target)
            copied_files.append(
                {
                    "cohort": cohort,
                    "source_path": str(record.relative_to(source)),
                    "copied_path": str(target.relative_to(out_dir)),
                    "sha256": sha256_file(target),
                    "size_bytes": target.stat().st_size,
                }
            )

    manifest = {
        "upstream_repository": UPSTREAM_REPOSITORY,
        "source_commit": source_commit,
        "source_license": license_text,
        "source": str(source),
        "cohorts": list(cohorts),
        "cohort_counts": cohort_counts,
        "files": copied_files,
    }
    manifest_path = out_dir / "source-manifest.yaml"
    manifest_path.write_text(yaml.safe_dump(manifest, sort_keys=False), encoding="utf-8")
    return DemoFetchSummary(
        source=source,
        out_dir=out_dir,
        cohort_counts=cohort_counts,
        manifest_path=manifest_path,
    )


def read_git_commit(path: Path) -> str:
    head_path = path / ".git" / "HEAD"
    if not head_path.exists():
        return "unknown"
    head = head_path.read_text(encoding="utf-8").strip()
    if head.startswith("ref: "):
        ref_path = path / ".git" / head.removeprefix("ref: ")
        if ref_path.exists():
            return ref_path.read_text(encoding="utf-8").strip()
    return head


def read_license(path: Path) -> str:
    license_path = path / "LICENSE"
    if not license_path.exists():
        return "unknown"
    first_line = license_path.read_text(encoding="utf-8").splitlines()[0]
    return first_line.strip()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
