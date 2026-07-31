from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from typing import Any, Literal

BackendStatus = Literal["implemented", "scaffolded"]


@dataclass(frozen=True)
class BackendCapabilities:
    kind: str
    role: str
    status: BackendStatus
    supports_release_activation: bool = False
    supports_existence: bool = False
    supports_counts: bool = False
    supports_records: bool = False
    supports_phenotype_filters: bool = False
    supports_disease_filters: bool = False
    supports_medical_action_filters: bool = False
    supports_gene_filters: bool = False
    supports_variant_filters: bool = False
    supports_descendant_expansion: bool = False
    supports_full_text: bool = False
    beacon_compatible_adapter_target: bool = True

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any]) -> BackendCapabilities:
        kind = data.get("kind", data.get("backend_kind"))
        role = data.get("role", data.get("backend_role"))
        status = data.get("status", data.get("backend_status"))
        if not isinstance(kind, str) or not isinstance(role, str) or status not in (
            "implemented",
            "scaffolded",
        ):
            raise ValueError("backend capability entries require kind, role, and status")
        return cls(
            kind=kind,
            role=role,
            status=status,
            supports_release_activation=bool(data.get("supports_release_activation", False)),
            supports_existence=bool(data.get("supports_existence", False)),
            supports_counts=bool(data.get("supports_counts", False)),
            supports_records=bool(data.get("supports_records", False)),
            supports_phenotype_filters=bool(data.get("supports_phenotype_filters", False)),
            supports_disease_filters=bool(data.get("supports_disease_filters", False)),
            supports_medical_action_filters=bool(
                data.get("supports_medical_action_filters", False)
            ),
            supports_gene_filters=bool(data.get("supports_gene_filters", False)),
            supports_variant_filters=bool(data.get("supports_variant_filters", False)),
            supports_descendant_expansion=bool(data.get("supports_descendant_expansion", False)),
            supports_full_text=bool(data.get("supports_full_text", False)),
            beacon_compatible_adapter_target=bool(
                data.get("beacon_compatible_adapter_target", True)
            ),
        )

    def to_dict(self) -> dict[str, str | bool]:
        return asdict(self)


BACKEND_CAPABILITIES: tuple[BackendCapabilities, ...] = (
    BackendCapabilities(
        "memory",
        "serving_index",
        "implemented",
        supports_release_activation=True,
        supports_existence=True,
        supports_counts=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_medical_action_filters=True,
    ),
    BackendCapabilities(
        "sqlite",
        "serving_index",
        "scaffolded",
        supports_release_activation=True,
        supports_existence=True,
        supports_counts=True,
        supports_records=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_medical_action_filters=True,
    ),
    BackendCapabilities(
        "postgres",
        "serving_index",
        "scaffolded",
        supports_release_activation=True,
        supports_existence=True,
        supports_counts=True,
        supports_records=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_medical_action_filters=True,
        supports_gene_filters=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "mongodb",
        "serving_index",
        "scaffolded",
        supports_existence=True,
        supports_counts=True,
        supports_records=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_medical_action_filters=True,
        supports_variant_filters=True,
        supports_descendant_expansion=True,
    ),
    BackendCapabilities(
        "clickhouse",
        "serving_index",
        "scaffolded",
        supports_existence=True,
        supports_counts=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_gene_filters=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "duckdb",
        "analytics",
        "scaffolded",
        supports_counts=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_gene_filters=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "snowflake",
        "warehouse",
        "scaffolded",
        supports_counts=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_gene_filters=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "redshift",
        "warehouse",
        "scaffolded",
        supports_counts=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_gene_filters=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "databricks_sql",
        "warehouse",
        "scaffolded",
        supports_counts=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_gene_filters=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "bigquery",
        "analytics",
        "scaffolded",
        supports_counts=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_gene_filters=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "trino",
        "analytics",
        "scaffolded",
        supports_counts=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_gene_filters=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "iceberg",
        "analytics",
        "scaffolded",
        supports_release_activation=True,
        supports_counts=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_gene_filters=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "parquet",
        "analytics",
        "scaffolded",
        supports_release_activation=True,
        supports_counts=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_gene_filters=True,
        supports_variant_filters=True,
        beacon_compatible_adapter_target=False,
    ),
    BackendCapabilities("arrow", "table_format", "scaffolded", supports_counts=True),
    BackendCapabilities(
        "avro",
        "table_format",
        "scaffolded",
        supports_release_activation=True,
        beacon_compatible_adapter_target=False,
    ),
    BackendCapabilities(
        "delta_lake",
        "table_format",
        "scaffolded",
        supports_release_activation=True,
        supports_counts=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_gene_filters=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "hudi",
        "table_format",
        "scaffolded",
        supports_release_activation=True,
        supports_counts=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_gene_filters=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "polaris",
        "table_format",
        "scaffolded",
        supports_release_activation=True,
        beacon_compatible_adapter_target=False,
    ),
    BackendCapabilities(
        "apache_doris",
        "warehouse",
        "scaffolded",
        supports_counts=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_gene_filters=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "opensearch",
        "search",
        "scaffolded",
        supports_existence=True,
        supports_counts=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_full_text=True,
    ),
    BackendCapabilities(
        "elasticsearch",
        "search",
        "scaffolded",
        supports_existence=True,
        supports_counts=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_full_text=True,
    ),
    BackendCapabilities(
        "hail",
        "genomics_engine",
        "scaffolded",
        supports_counts=True,
        supports_gene_filters=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "spark",
        "compute_engine",
        "scaffolded",
        supports_counts=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_gene_filters=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "sail",
        "compute_engine",
        "scaffolded",
        supports_counts=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_gene_filters=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "velox",
        "compute_engine",
        "scaffolded",
        supports_counts=True,
        beacon_compatible_adapter_target=False,
    ),
    BackendCapabilities(
        "lakehouse",
        "analytics",
        "scaffolded",
        supports_release_activation=True,
        supports_counts=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_gene_filters=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "terra",
        "deployment_platform",
        "scaffolded",
        supports_counts=True,
        supports_gene_filters=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "anvil",
        "deployment_platform",
        "scaffolded",
        supports_counts=True,
        supports_gene_filters=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "gnomad",
        "reference_resource",
        "scaffolded",
        supports_gene_filters=True,
        supports_variant_filters=True,
        beacon_compatible_adapter_target=False,
    ),
    BackendCapabilities(
        "hdf5",
        "table_format",
        "scaffolded",
        supports_counts=True,
        beacon_compatible_adapter_target=False,
    ),
    BackendCapabilities(
        "genomicsdb",
        "genomics_engine",
        "scaffolded",
        supports_existence=True,
        supports_counts=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "tiledb",
        "genomics_engine",
        "scaffolded",
        supports_existence=True,
        supports_counts=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "tiledb_vcf",
        "genomics_engine",
        "scaffolded",
        supports_existence=True,
        supports_counts=True,
        supports_variant_filters=True,
    ),
    BackendCapabilities(
        "fhir",
        "clinical_interoperability",
        "scaffolded",
        supports_records=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_medical_action_filters=True,
    ),
    BackendCapabilities(
        "omop",
        "clinical_interoperability",
        "scaffolded",
        supports_counts=True,
        supports_phenotype_filters=True,
        supports_disease_filters=True,
        supports_medical_action_filters=True,
    ),
    BackendCapabilities(
        "redis_valkey",
        "cache",
        "scaffolded",
        beacon_compatible_adapter_target=False,
    ),
)


def backend_capabilities() -> list[dict[str, str | bool]]:
    return [capabilities.to_dict() for capabilities in BACKEND_CAPABILITIES]


def filter_backend_capabilities(
    capabilities: Iterable[BackendCapabilities],
    *,
    role: str | None = None,
    status: BackendStatus | None = None,
    supports: str | None = None,
) -> list[BackendCapabilities]:
    capability_name = normalise_supports_filter(supports) if supports is not None else None
    if status is not None and status not in ("implemented", "scaffolded"):
        raise ValueError(f"unknown backend status: {status}")
    filtered = []
    for capability in capabilities:
        if role is not None and capability.role != role:
            continue
        if status is not None and capability.status != status:
            continue
        if capability_name is not None and not bool(getattr(capability, capability_name)):
            continue
        filtered.append(capability)
    return filtered


def normalise_supports_filter(value: str) -> str:
    field = value if value.startswith("supports_") else f"supports_{value}"
    if field not in BackendCapabilities.__dataclass_fields__:
        raise ValueError(f"unknown backend capability: {value}")
    return field
