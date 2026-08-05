# Data Model

The public data model will be defined in LinkML and serialized as JSON or YAML.

Initial model areas:

- site manifest;
- site capabilities;
- query request;
- query outcome;
- projected Phenopacket record;
- evidence snippet;
- clinical impact annotation;
- reference cache metadata;
- validation report.

Rust and Python should both read and write examples for these contracts.

The first schema lives at `src/phenorelay/schema/phenorelay.yaml`. The first
examples live under `examples/` and cover a site manifest, a query request, and a
query outcome with optional evidence. Clinical impact examples are synthetic and
show how evidence-bearing annotations can be represented without restricted
source data.
