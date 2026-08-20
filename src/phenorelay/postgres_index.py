from __future__ import annotations

import re
from dataclasses import dataclass

from phenorelay.index import IndexError

SCHEMA_VERSION = 1
SCHEMA_NAME_PATTERN = re.compile(r"^[a-z_][a-z0-9_]*$")


class PostgresIndexError(IndexError):
    pass


@dataclass(frozen=True)
class PostgresSchema:
    schema_name: str = "phenorelay"
    schema_version: int = SCHEMA_VERSION
    include_drop: bool = False

    def __post_init__(self) -> None:
        if not SCHEMA_NAME_PATTERN.fullmatch(self.schema_name):
            raise PostgresIndexError(
                "PostgreSQL schema names must use lowercase letters, numbers, and underscores"
            )

    def statements(self) -> tuple[str, ...]:
        qualified = QualifiedNames(self.schema_name)
        statements = [
            f"CREATE SCHEMA IF NOT EXISTS {qualified.schema};",
            f"""
CREATE TABLE {qualified.release_metadata} (
    site_id text NOT NULL,
    release_id text NOT NULL,
    generated_at timestamptz NOT NULL,
    schema_version integer NOT NULL
);
""".strip(),
            f"""
CREATE TABLE {qualified.records} (
    phenopacket_id text PRIMARY KEY,
    subject_id_redacted boolean NOT NULL,
    has_genomic_interpretations boolean NOT NULL
);
""".strip(),
            f"""
CREATE TABLE {qualified.phenotypes} (
    phenopacket_id text NOT NULL
        REFERENCES {qualified.records} (phenopacket_id) ON DELETE CASCADE,
    term text NOT NULL,
    label text,
    presence text NOT NULL
);
""".strip(),
            f"""
CREATE TABLE {qualified.diseases} (
    phenopacket_id text NOT NULL
        REFERENCES {qualified.records} (phenopacket_id) ON DELETE CASCADE,
    term text NOT NULL,
    label text,
    presence text NOT NULL
);
""".strip(),
            f"""
CREATE TABLE {qualified.medical_actions} (
    phenopacket_id text NOT NULL
        REFERENCES {qualified.records} (phenopacket_id) ON DELETE CASCADE,
    term text NOT NULL
);
""".strip(),
            "CREATE INDEX phenotypes_term_presence_idx "
            f"ON {qualified.phenotypes} (term, presence);",
            "CREATE INDEX phenotypes_phenopacket_id_idx "
            f"ON {qualified.phenotypes} (phenopacket_id);",
            f"CREATE INDEX diseases_term_presence_idx ON {qualified.diseases} (term, presence);",
            f"CREATE INDEX diseases_phenopacket_id_idx ON {qualified.diseases} (phenopacket_id);",
            f"CREATE INDEX medical_actions_term_idx ON {qualified.medical_actions} (term);",
            "CREATE INDEX medical_actions_phenopacket_id_idx "
            f"ON {qualified.medical_actions} (phenopacket_id);",
        ]
        if self.include_drop:
            statements = [
                f"DROP TABLE IF EXISTS {qualified.medical_actions};",
                f"DROP TABLE IF EXISTS {qualified.diseases};",
                f"DROP TABLE IF EXISTS {qualified.phenotypes};",
                f"DROP TABLE IF EXISTS {qualified.records};",
                f"DROP TABLE IF EXISTS {qualified.release_metadata};",
                *statements,
            ]
        return tuple(statements)

    def ddl(self) -> str:
        return "\n\n".join(self.statements()) + "\n"


@dataclass(frozen=True)
class QualifiedNames:
    schema_name: str

    @property
    def schema(self) -> str:
        return quote_identifier(self.schema_name)

    @property
    def release_metadata(self) -> str:
        return self.qualified("release_metadata")

    @property
    def records(self) -> str:
        return self.qualified("records")

    @property
    def phenotypes(self) -> str:
        return self.qualified("phenotypes")

    @property
    def diseases(self) -> str:
        return self.qualified("diseases")

    @property
    def medical_actions(self) -> str:
        return self.qualified("medical_actions")

    def qualified(self, table: str) -> str:
        return f"{self.schema}.{quote_identifier(table)}"


@dataclass(frozen=True)
class PostgresReleaseIndex:
    schema: PostgresSchema

    @classmethod
    def scaffold(cls, schema_name: str = "phenorelay") -> PostgresReleaseIndex:
        return cls(schema=PostgresSchema(schema_name=schema_name))

    # TODO: Add a live loader once connection handling and CI service containers are in place.
    def build(self) -> None:
        raise PostgresIndexError("PostgreSQL live build is not implemented yet")

    # TODO: Mirror SQLite exact count and existence queries after the live loader lands.
    def query(self) -> None:
        raise PostgresIndexError("PostgreSQL live query is not implemented yet")


def quote_identifier(value: str) -> str:
    if not SCHEMA_NAME_PATTERN.fullmatch(value):
        raise PostgresIndexError(
            "PostgreSQL identifiers must use lowercase letters, numbers, and underscores"
        )
    return f'"{value}"'
