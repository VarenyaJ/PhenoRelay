# SQLite Index

SQLite is the first persistent serving index for local PhenoRelay releases. It is
a rebuildable artifact derived from a site manifest and projected records.
Phenopacket JSON and release metadata remain the source of truth.

Build an index:

```bash
phenorelay sqlite-build \
  --manifest examples/site-manifest.yaml \
  --records examples/projected-records.yaml \
  --db release.sqlite
```

For release activation, validate projected phenotype IDs and labels against the
local HPO release before writing the index:

```bash
phenorelay sqlite-build \
  --manifest examples/site-manifest.yaml \
  --records examples/projected-records.yaml \
  --db release.sqlite \
  --validate-hpo ~/.hpo/hp.json
```

If validation fails, the command prints a structured validation report, exits
non-zero, and does not create or replace the SQLite database.

Inspect the release:

```bash
phenorelay sqlite-summary --db release.sqlite
```

Run a local query:

```bash
phenorelay sqlite-query \
  --db release.sqlite \
  --request examples/query-request.yaml
```

The SQLite adapter supports exact existence and count queries for phenotypes,
diseases, and medical actions. Descendant matching, gene queries, variant queries,
and record-level responses are still reported as `unsupported`.
