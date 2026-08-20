from __future__ import annotations

import pytest
from typer.testing import CliRunner

from phenorelay.backends import BACKEND_CAPABILITIES
from phenorelay.cli import app
from phenorelay.postgres_index import (
    PostgresIndexError,
    PostgresReleaseIndex,
    PostgresSchema,
)


def test_postgres_schema_includes_release_tables_and_indexes() -> None:
    ddl = PostgresSchema().ddl()

    assert 'CREATE SCHEMA IF NOT EXISTS "phenorelay";' in ddl
    assert 'CREATE TABLE "phenorelay"."release_metadata"' in ddl
    assert 'CREATE TABLE "phenorelay"."records"' in ddl
    assert 'CREATE TABLE "phenorelay"."phenotypes"' in ddl
    assert 'CREATE TABLE "phenorelay"."diseases"' in ddl
    assert 'CREATE TABLE "phenorelay"."medical_actions"' in ddl
    assert "phenotypes_term_presence_idx" in ddl
    assert "diseases_term_presence_idx" in ddl
    assert "medical_actions_term_idx" in ddl


def test_postgres_schema_preserves_redacted_subject_identity_shape() -> None:
    ddl = PostgresSchema().ddl()

    assert "subject_id_redacted boolean NOT NULL" in ddl
    assert "subject_id text" not in ddl
    assert "phenopacket_id text PRIMARY KEY" in ddl


def test_postgres_schema_foreign_keys_point_to_records() -> None:
    ddl = PostgresSchema().ddl()

    assert 'REFERENCES "phenorelay"."records" (phenopacket_id) ON DELETE CASCADE' in ddl
    assert (
        'CREATE INDEX phenotypes_phenopacket_id_idx ON "phenorelay"."phenotypes"' in ddl
    )
    assert 'CREATE INDEX diseases_phenopacket_id_idx ON "phenorelay"."diseases"' in ddl
    assert (
        'CREATE INDEX medical_actions_phenopacket_id_idx ON "phenorelay"."medical_actions"'
        in ddl
    )


def test_postgres_schema_can_include_drop_statements() -> None:
    statements = PostgresSchema(include_drop=True).statements()

    assert statements[0] == 'DROP TABLE IF EXISTS "phenorelay"."medical_actions";'
    assert statements[1] == 'DROP TABLE IF EXISTS "phenorelay"."diseases";'
    assert statements[2] == 'DROP TABLE IF EXISTS "phenorelay"."phenotypes";'
    assert statements[3] == 'DROP TABLE IF EXISTS "phenorelay"."records";'
    assert statements[4] == 'DROP TABLE IF EXISTS "phenorelay"."release_metadata";'


def test_postgres_schema_accepts_public_schema_name() -> None:
    ddl = PostgresSchema(schema_name="public").ddl()

    assert 'CREATE SCHEMA IF NOT EXISTS "public";' in ddl
    assert 'CREATE TABLE "public"."records"' in ddl


@pytest.mark.parametrize(
    "schema_name",
    ["Phenorelay", "pheno-relay", "phenorelay.public", "1phenorelay"],
)
def test_postgres_schema_rejects_unsafe_schema_names(schema_name: str) -> None:
    with pytest.raises(PostgresIndexError):
        PostgresSchema(schema_name=schema_name)


def test_postgres_release_index_live_methods_are_explicitly_scaffolded() -> None:
    index = PostgresReleaseIndex.scaffold()

    with pytest.raises(PostgresIndexError, match="live build is not implemented"):
        index.build()
    with pytest.raises(PostgresIndexError, match="live query is not implemented"):
        index.query()


def test_postgres_schema_cli_prints_default_schema() -> None:
    result = CliRunner().invoke(app, ["postgres-schema"])

    assert result.exit_code == 0
    assert 'CREATE SCHEMA IF NOT EXISTS "phenorelay";' in result.stdout
    assert 'CREATE TABLE "phenorelay"."records"' in result.stdout


def test_postgres_schema_cli_supports_schema_and_drop_options() -> None:
    result = CliRunner().invoke(app, ["postgres-schema", "--schema", "public", "--include-drop"])

    assert result.exit_code == 0
    assert 'DROP TABLE IF EXISTS "public"."records";' in result.stdout
    assert 'CREATE TABLE "public"."records"' in result.stdout


def test_postgres_schema_cli_rejects_unsafe_schema_name() -> None:
    result = CliRunner().invoke(app, ["postgres-schema", "--schema", "pheno-relay"])

    assert result.exit_code != 0
    assert "PostgreSQL schema names" in result.output


def test_postgres_backend_capabilities_describe_scaffolded_serving_index() -> None:
    postgres = next(item for item in BACKEND_CAPABILITIES if item.kind == "postgres")

    assert postgres.status == "scaffolded"
    assert postgres.role == "serving_index"
    assert postgres.supports_release_activation
    assert postgres.supports_counts
    assert postgres.supports_existence
    assert postgres.supports_records
    assert postgres.supports_phenotype_filters
    assert postgres.supports_disease_filters
    assert postgres.supports_medical_action_filters
