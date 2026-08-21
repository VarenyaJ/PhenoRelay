from __future__ import annotations

import csv
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from phenorelay.index import ProjectedRecord
from phenorelay.manifest import SiteManifest

TABLE_NAMES = (
    "release_metadata",
    "records",
    "phenotypes",
    "diseases",
    "medical_actions",
)


class TableExportError(ValueError):
    pass


@dataclass(frozen=True)
class TableExportSummary:
    out_dir: Path
    format: str
    table_counts: dict[str, int]

    def to_dict(self) -> dict[str, str | dict[str, int]]:
        return {
            "out_dir": str(self.out_dir),
            "format": self.format,
            "table_counts": self.table_counts,
        }


def export_release_tables(
    *,
    manifest: SiteManifest,
    records: Iterable[ProjectedRecord],
    out_dir: Path,
    export_format: str = "csv",
) -> TableExportSummary:
    if export_format != "csv":
        # TODO: Add Parquet once the project settles on pyarrow, polars, or DuckDB as a dependency.
        raise TableExportError("only csv table export is implemented")
    if out_dir.exists() and not out_dir.is_dir():
        raise TableExportError("table export output path must be a directory")

    projected_records = tuple(records)
    out_dir.mkdir(parents=True, exist_ok=True)
    tables = build_release_tables(manifest, projected_records)
    for table_name, rows in tables.items():
        write_csv_table(out_dir / f"{table_name}.csv", rows)

    return TableExportSummary(
        out_dir=out_dir,
        format=export_format,
        table_counts={table_name: len(rows) for table_name, rows in tables.items()},
    )


def build_release_tables(
    manifest: SiteManifest,
    records: tuple[ProjectedRecord, ...],
) -> dict[str, list[dict[str, str | bool | int]]]:
    return {
        "release_metadata": [
            {
                "site_id": manifest.site_id,
                "release_id": manifest.release_id,
                "generated_at": datetime.now(UTC).isoformat(),
                "schema_version": 1,
            }
        ],
        "records": [
            {
                "phenopacket_id": record.phenopacket_id,
                "subject_id_redacted": record.subject_id_redacted,
                "has_genomic_interpretations": record.has_genomic_interpretations,
            }
            for record in records
        ],
        "phenotypes": [
            {
                "phenopacket_id": record.phenopacket_id,
                "term": phenotype.term,
                "label": phenotype.label or "",
                "presence": phenotype.presence,
            }
            for record in records
            for phenotype in record.phenotypes
        ],
        "diseases": [
            {
                "phenopacket_id": record.phenopacket_id,
                "term": disease.term,
                "label": disease.label or "",
                "presence": disease.presence,
            }
            for record in records
            for disease in record.diseases
        ],
        "medical_actions": [
            {
                "phenopacket_id": record.phenopacket_id,
                "term": term,
            }
            for record in records
            for term in record.medical_actions
        ],
    }


def write_csv_table(path: Path, rows: list[dict[str, str | bool | int]]) -> None:
    fieldnames = csv_fieldnames(path.stem)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def csv_fieldnames(table_name: str) -> tuple[str, ...]:
    if table_name == "release_metadata":
        return ("site_id", "release_id", "generated_at", "schema_version")
    if table_name == "records":
        return ("phenopacket_id", "subject_id_redacted", "has_genomic_interpretations")
    if table_name in ("phenotypes", "diseases"):
        return ("phenopacket_id", "term", "label", "presence")
    if table_name == "medical_actions":
        return ("phenopacket_id", "term")
    raise TableExportError(f"unknown export table: {table_name}")
