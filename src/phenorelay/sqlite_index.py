from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from phenorelay.index import (
    IndexError,
    ProjectedRecord,
    matches_presence,
    require_string,
    unsupported,
)
from phenorelay.manifest import SiteManifest

SCHEMA_VERSION = 1


class SQLiteIndexError(IndexError):
    pass


class SQLiteReleaseIndex:
    def __init__(self, path: Path) -> None:
        self.path = path

    @classmethod
    def build(
        cls,
        path: Path,
        manifest: SiteManifest,
        records: Iterable[ProjectedRecord],
    ) -> SQLiteReleaseIndex:
        if path.exists() and path.is_dir():
            raise SQLiteIndexError("SQLite index path points to a directory")
        path.parent.mkdir(parents=True, exist_ok=True)

        connection = sqlite3.connect(path)
        try:
            create_schema(connection)
            replace_release(connection, manifest, tuple(records))
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
        return cls(path)

    def summary(self) -> dict[str, str | int | None]:
        with self.connect() as connection:
            row = connection.execute(
                """
                SELECT site_id, release_id, generated_at, schema_version
                FROM release_metadata
                LIMIT 1
                """
            ).fetchone()
            if row is None:
                raise SQLiteIndexError("SQLite index does not contain release metadata")
            record_count = connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]
            phenotype_count = connection.execute("SELECT COUNT(*) FROM phenotypes").fetchone()[0]
            disease_count = connection.execute("SELECT COUNT(*) FROM diseases").fetchone()[0]
            medical_action_count = connection.execute(
                "SELECT COUNT(*) FROM medical_actions"
            ).fetchone()[0]

        return {
            "site_id": row[0],
            "release_id": row[1],
            "record_count": record_count,
            "phenotype_count": phenotype_count,
            "disease_count": disease_count,
            "medical_action_count": medical_action_count,
            "generated_at": row[2],
            "schema_version": row[3],
        }

    def query(self, request: dict[str, Any]) -> dict[str, Any]:
        query_id = require_string(request, "query_id")
        feature = require_string(request, "feature")
        granularity = request.get("requested_granularity", "count")
        if not isinstance(granularity, str):
            raise SQLiteIndexError("requested_granularity must be a string")

        if granularity == "record":
            return unsupported(query_id, feature)
        if feature not in ("phenotype", "disease", "medical_action"):
            return unsupported(query_id, feature)

        match_mode = request.get("match_mode", "exact")
        if match_mode != "exact":
            return unsupported(query_id, feature)

        term = require_string(request, "term")
        count = self.count_exact(feature, term, request.get("presence", "present"))
        outcome: dict[str, Any] = {
            "query_id": query_id,
            "status": "match",
            "feature": feature,
            "exists": count > 0,
        }
        if granularity == "count":
            outcome["count"] = count
        elif granularity != "existence":
            return unsupported(query_id, feature)
        return outcome

    def count_exact(self, feature: str, term: str, presence: Any) -> int:
        with self.connect() as connection:
            if feature == "phenotype":
                if not isinstance(presence, str):
                    raise SQLiteIndexError("presence must be a string")
                if presence == "any":
                    row = connection.execute(
                        "SELECT COUNT(DISTINCT record_id) FROM phenotypes WHERE term = ?",
                        (term,),
                    ).fetchone()
                else:
                    row = connection.execute(
                        """
                        SELECT COUNT(DISTINCT record_id)
                        FROM phenotypes
                        WHERE term = ? AND presence = ?
                        """,
                        (term, presence),
                    ).fetchone()
                return int(row[0])
            if feature == "disease":
                row = connection.execute(
                    "SELECT COUNT(DISTINCT record_id) FROM diseases WHERE term = ?",
                    (term,),
                ).fetchone()
                return int(row[0])
            if feature == "medical_action":
                row = connection.execute(
                    "SELECT COUNT(DISTINCT record_id) FROM medical_actions WHERE term = ?",
                    (term,),
                ).fetchone()
                return int(row[0])
        raise SQLiteIndexError(f"unsupported query feature: {feature}")

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.execute("PRAGMA foreign_keys = ON")
        return connection


def create_schema(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        DROP TABLE IF EXISTS medical_actions;
        DROP TABLE IF EXISTS diseases;
        DROP TABLE IF EXISTS phenotypes;
        DROP TABLE IF EXISTS records;
        DROP TABLE IF EXISTS release_metadata;

        CREATE TABLE release_metadata (
            site_id TEXT NOT NULL,
            release_id TEXT NOT NULL,
            generated_at TEXT NOT NULL,
            schema_version INTEGER NOT NULL
        );

        CREATE TABLE records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phenopacket_id TEXT NOT NULL UNIQUE,
            subject_id_redacted INTEGER NOT NULL,
            has_genomic_interpretations INTEGER NOT NULL
        );

        CREATE TABLE phenotypes (
            record_id INTEGER NOT NULL REFERENCES records(id) ON DELETE CASCADE,
            term TEXT NOT NULL,
            presence TEXT NOT NULL
        );

        CREATE TABLE diseases (
            record_id INTEGER NOT NULL REFERENCES records(id) ON DELETE CASCADE,
            term TEXT NOT NULL,
            presence TEXT NOT NULL
        );

        CREATE TABLE medical_actions (
            record_id INTEGER NOT NULL REFERENCES records(id) ON DELETE CASCADE,
            term TEXT NOT NULL
        );

        CREATE INDEX idx_phenotypes_term_presence ON phenotypes(term, presence);
        CREATE INDEX idx_diseases_term ON diseases(term);
        CREATE INDEX idx_medical_actions_term ON medical_actions(term);
        """
    )


def replace_release(
    connection: sqlite3.Connection,
    manifest: SiteManifest,
    records: tuple[ProjectedRecord, ...],
) -> None:
    connection.execute(
        """
        INSERT INTO release_metadata (site_id, release_id, generated_at, schema_version)
        VALUES (?, ?, ?, ?)
        """,
        (manifest.site_id, manifest.release_id, datetime.now(UTC).isoformat(), SCHEMA_VERSION),
    )
    for record in records:
        cursor = connection.execute(
            """
            INSERT INTO records (
                phenopacket_id,
                subject_id_redacted,
                has_genomic_interpretations
            )
            VALUES (?, ?, ?)
            """,
            (
                record.phenopacket_id,
                int(record.subject_id_redacted),
                int(record.has_genomic_interpretations),
            ),
        )
        record_id = cursor.lastrowid
        if record_id is None:
            raise SQLiteIndexError("failed to insert projected record")

        connection.executemany(
            "INSERT INTO phenotypes (record_id, term, presence) VALUES (?, ?, ?)",
            (
                (record_id, projected.term, projected.presence)
                for projected in record.phenotypes
                if matches_presence(projected.presence, "any")
            ),
        )
        connection.executemany(
            "INSERT INTO diseases (record_id, term, presence) VALUES (?, ?, ?)",
            ((record_id, projected.term, projected.presence) for projected in record.diseases),
        )
        connection.executemany(
            "INSERT INTO medical_actions (record_id, term) VALUES (?, ?)",
            ((record_id, term) for term in record.medical_actions),
        )
