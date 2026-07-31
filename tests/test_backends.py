from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from phenorelay.backends import (
    BACKEND_CAPABILITIES,
    backend_capabilities,
    filter_backend_capabilities,
)
from phenorelay.cli import app
from phenorelay.manifest import load_site_manifest


def test_backend_capability_catalog_includes_implemented_memory_backend() -> None:
    memory = next(item for item in backend_capabilities() if item["kind"] == "memory")

    assert memory["status"] == "implemented"
    assert memory["supports_counts"]
    assert memory["supports_phenotype_filters"]


def test_backend_capability_catalog_includes_documented_backend_families() -> None:
    kinds = {item["kind"] for item in backend_capabilities()}

    assert "snowflake" in kinds
    assert "delta_lake" in kinds
    assert "apache_doris" in kinds
    assert "tiledb" in kinds


def test_backends_cli_prints_catalog() -> None:
    result = CliRunner().invoke(app, ["backends"])

    assert result.exit_code == 0
    assert '"kind": "postgres"' in result.stdout
    assert '"kind": "redis_valkey"' in result.stdout


def test_backend_capability_filter_supports_role_and_capability() -> None:
    filtered = filter_backend_capabilities(
        BACKEND_CAPABILITIES,
        role="genomics_engine",
        supports="variant_filters",
    )

    assert {item.kind for item in filtered} == {"hail", "genomicsdb", "tiledb", "tiledb_vcf"}


def test_site_manifest_loader_reads_storage_backend_capabilities() -> None:
    manifest = load_site_manifest(Path("examples/site-manifest.yaml"))

    assert manifest.site_id == "synthetic-site"
    assert {backend.kind for backend in manifest.storage_backends} == {
        "memory",
        "postgres",
        "trino",
        "redis_valkey",
    }


def test_backends_cli_filters_manifest_backends() -> None:
    result = CliRunner().invoke(
        app,
        [
            "backends",
            "--manifest",
            "examples/site-manifest.yaml",
            "--role",
            "serving_index",
            "--supports",
            "variant_filters",
        ],
    )

    assert result.exit_code == 0
    assert '"kind": "postgres"' in result.stdout
    assert '"kind": "memory"' not in result.stdout


def test_backends_cli_rejects_unknown_capability_filter() -> None:
    result = CliRunner().invoke(app, ["backends", "--supports", "not_real"])

    assert result.exit_code != 0
    assert "unknown backend capability" in result.output
