# PostgreSQL Index

PostgreSQL is the planned multi-user relational serving index for PhenoRelay
releases. It sits beside SQLite: SQLite is the local/demo artifact, while
PostgreSQL is the deployment-oriented path for teams that need shared access,
managed backups, read replicas, and operational monitoring.

The current PostgreSQL support is a schema scaffold. It does not connect to a
database, load records, or answer queries yet.

Print the default schema:

```bash
phenorelay postgres-schema
```

Use a specific PostgreSQL schema namespace:

```bash
phenorelay postgres-schema --schema public
```

Print a rebuild script with drop statements:

```bash
phenorelay postgres-schema --schema phenorelay --include-drop
```

The scaffold uses these tables:

- `release_metadata` for site, release, generated-at, and schema-version fields;
- `records` for projected Phenopacket identity and redaction state;
- `phenotypes` for HPO term, label, and presence values;
- `diseases` for disease term, label, and presence values;
- `medical_actions` for procedure/action terms.

The scaffold intentionally stores `phenopacket_id` and `subject_id_redacted`, not
raw subject identifiers. Any future sensitive-identity mode must be explicit.

Indexes cover the first expected query path:

- exact phenotype count and existence queries by `term` and `presence`;
- exact disease count and existence queries by `term` and `presence`;
- exact medical-action count and existence queries by `term`;
- joins from feature tables back to `records`.

TODOs before live PostgreSQL use:

- add connection URL handling without logging credentials;
- add a live loader that consumes HPO-validated projected records;
- add `postgres-build`, `postgres-summary`, and `postgres-query`;
- add CI integration tests with a PostgreSQL service container;
- add migrations or versioned rebuild scripts before schema changes become
  persistent;
- add ontology closure tables or materialized views for descendant expansion;
- evaluate GIN or trigram indexes only after text-search requirements are stable.
