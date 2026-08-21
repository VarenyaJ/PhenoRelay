# Table Export

Table export turns projected records into flat files that mirror the serving-index
shape used by SQLite and the PostgreSQL scaffold. This is the dependency-light
bridge toward DuckDB, Parquet, and lakehouse workflows.

Export CSV tables:

```bash
phenorelay export-tables \
  --manifest examples/site-manifest.yaml \
  --records examples/projected-records.yaml \
  --out-dir release-tables
```

Validate HPO terms before export:

```bash
phenorelay export-tables \
  --manifest examples/site-manifest.yaml \
  --records examples/projected-records.yaml \
  --out-dir release-tables \
  --validate-hpo ~/.hpo/hp.json
```

The command writes:

- `release_metadata.csv`;
- `records.csv`;
- `phenotypes.csv`;
- `diseases.csv`;
- `medical_actions.csv`.

The exported shape preserves `phenopacket_id`, ontology terms, labels, presence,
and release metadata. It does not export raw subject identifiers.

Current format support is intentionally narrow:

- `csv` is implemented with the Python standard library;
- `parquet` is planned but not implemented yet;
- DuckDB can query the exported CSV tables directly.

Example DuckDB query:

```sql
CREATE VIEW phenotypes AS
SELECT *
FROM read_csv_auto('release-tables/phenotypes.csv');

SELECT COUNT(DISTINCT phenopacket_id)
FROM phenotypes
WHERE term = 'HP:0001250'
  AND presence = 'present';
```

TODOs before analytical use:

- add Parquet output after choosing the table writer dependency;
- add DuckDB-backed CLI helpers if repeated ad hoc CSV queries become common;
- add partitioned export layout for larger releases;
- include ontology-release metadata in a machine-readable sidecar if table formats
  need more than the current release table;
- keep HPO validation as the release gate before exporting tables for shared use.
