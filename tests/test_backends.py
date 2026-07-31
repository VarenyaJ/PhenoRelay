from __future__ import annotations

from typer.testing import CliRunner

from phenorelay.backends import backend_capabilities
from phenorelay.cli import app


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
