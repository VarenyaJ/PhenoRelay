# Design Decisions

## Rust And Python Are Both First-Class

PhenoRelay deliberately keeps both Rust and Python surfaces.

Rust is the better fit for a small deployable engine: parsing Phenopackets,
projecting records, local indexing, policy evaluation, and eventually a server or
CLI that institutions can run without a Python stack.

Python is the better fit for developer features: LinkML schemas, schema
documentation, evidence snippets, PubMed/reference-cache validation, ontology
validation tools, notebooks, and agent workflows. Those tools already exist in
the Python ecosystem, so reimplementing them in Rust first would slow the project
without improving the first user-facing result.

The shared contract is JSON shaped by LinkML. Rust and Python should both be able
to read and write that contract. Neither language should be required just to use
the other for its natural job.

## Subject Identifiers Are Redacted By Default

Commands that inspect Phenopackets should be useful for debugging without
printing subject identifiers by default. Subject IDs can be local identifiers,
study identifiers, or other values that become sensitive when paired with rare
phenotypes or institutional context.

The Python `phenorelay inspect` command therefore reports counts and record-level
shape while redacting `subject.id` unless the caller passes `--show-subject-id`.
The explicit flag is intended for synthetic, public, or otherwise non-sensitive
data.

The same rule applies to future Rust, Python, HTTP, and agent surfaces: do not
print subject identifiers, bearer tokens, raw federated queries, institutional
configuration, or full Phenopacket contents unless the user explicitly asks for
that detail in a context where it is appropriate.

## Unsupported Is Not Zero

When a site cannot evaluate a query feature, PhenoRelay should return an
unsupported status rather than a false zero-match result. This matters for
federation: a remote site with no genomic index is different from a remote site
that searched genomic findings and found no matches.
