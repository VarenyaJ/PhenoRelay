# Local Browser and API

PhenoRelay can serve a local release index through HTTP for browser inspection,
Beacon-compatible checks, and PhenoRelay-native query testing.

Start the synthetic example release:

```bash
phenorelay serve \
  --manifest examples/site-manifest.yaml \
  --records examples/projected-records.yaml \
  --demo
```

Open <http://127.0.0.1:8000/> for the browser scaffold.

The first server slice exposes two API surfaces:

- `/api/*` for Beacon-compatible endpoint shapes;
- `/api/pheno/*` for PhenoRelay-native browser and debugging responses.

Useful PhenoRelay-native routes:

```text
GET  /api/pheno/info
GET  /api/pheno/releases/current
GET  /api/pheno/filtering_terms
POST /api/pheno/query
GET  /api/pheno/records
```

Initial Beacon-compatible routes:

```text
GET  /api/info
GET  /api/service-info
GET  /api/filtering_terms
POST /api/individuals
POST /api/g_variants
```

The genomic-variant route intentionally returns an unsupported PhenoRelay status
until variant indexing exists.

## Public Demo Source Cache

Use the demo fetch command to copy selected public Phenopacket examples from a
local Phenopacket Store clone into a gitignored cache:

```bash
phenorelay fetch-demo-phenopackets \
  --source /path/to/phenopacket-store
```

The command writes to `.phenorelay-demo/phenopacket-store-sample/` by default.
That directory is ignored by git. The generated `source-manifest.yaml` records:

- source repository;
- source commit;
- source license;
- cohort counts;
- copied paths;
- SHA256 checksums;
- file sizes.

The first configured demo cohorts are `PTPN11`, `KRAS`, and `ABCA4`.

Project the fetched JSON files into a local release:

```bash
phenorelay build-demo-release
```

This writes `site-manifest.yaml` and `projected-records.yaml` under the ignored
demo cache. With those files present, `phenorelay serve --demo` serves the
generated public demo release by default.

Raw source examples are suitable for public demo mode because they are public
example data and the manifest records their provenance. Private or institutional
releases should continue to serve aggregate and projected views by default.
