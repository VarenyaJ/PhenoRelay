# Storage Backends

Beacon compatibility is an API contract, not a database requirement. PhenoRelay
keeps storage behind adapter boundaries so a site can use the backend that fits
its data, scale, and operational constraints.

The first scaffold defines:

- shared backend capability metadata;
- a storage backend trait for local query execution;
- an in-memory adapter for tests;
- scaffolded adapter modules for SQLite, PostgreSQL, MongoDB, ClickHouse, DuckDB,
  Snowflake, Redshift, Databricks SQL, Parquet, Arrow, Avro, Delta Lake, Hudi,
  Iceberg, Polaris, Trino, BigQuery, Apache Doris, OpenSearch, Elasticsearch,
  Hail, GenomicsDB, TileDB, TileDB-VCF, Spark, Sail, Velox, lakehouse-style
  deployments, Terra, AnVIL, gnomAD, HDF5, FHIR, OMOP, and Redis/Valkey.

Only the in-memory adapter and SQLite adapter have behavior at this stage. The
other adapters declare intended capabilities without adding database client
dependencies. SQLite is a local/demo adapter, not a Beacon requirement.
PostgreSQL is scaffolded as the multi-user relational serving-index path: it has
a printable schema, but no live loader or query execution yet.
Table export provides CSV files with the same projected table shape as the
serving indexes. That export is the first step toward DuckDB, Parquet, and
lakehouse-style analytical workflows without adding those dependencies to the
core CLI yet.

Every backend must preserve these semantics:

- unsupported features are not zero matches;
- forbidden responses are distinct from unavailable peers;
- release activation is explicit;
- ontology release metadata stays visible;
- subject identifiers are not disclosed by default;
- Beacon-facing responses are produced by the HTTP adapter, not by database shape.
