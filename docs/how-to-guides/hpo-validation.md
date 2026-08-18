# HPO Validation

Projected phenotype terms should be checked against a local HPO OBOGraph JSON
release before a release index is activated. The expected local file is usually
`~/.hpo/hp.json`.

Run validation:

```bash
phenorelay validate-phenotypes \
  --records examples/projected-records.yaml \
  --hpo ~/.hpo/hp.json
```

The validator checks:

- every projected phenotype ID exists in the HPO release;
- labels match the HPO release label or a synonym when labels are present;
- the validation report includes the HPO release version.

Missing IDs and label mismatches produce structured findings and a non-zero exit.
Storage adapters should consume validated projected records rather than performing
hidden ontology validation during database writes.

SQLite builds can run the same check as a release gate:

```bash
phenorelay sqlite-build \
  --manifest examples/site-manifest.yaml \
  --records examples/projected-records.yaml \
  --db release.sqlite \
  --validate-hpo ~/.hpo/hp.json
```

The gate runs before SQLite tables are created or replaced. A failed report leaves
any existing database file unchanged.
