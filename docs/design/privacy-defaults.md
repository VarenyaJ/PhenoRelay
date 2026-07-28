# Privacy Defaults

PhenoRelay defaults should minimize accidental disclosure.

Subject identifiers are redacted from ordinary inspection output because rare
phenotypes, disease terms, and institutional context can make otherwise local
identifiers sensitive.

The default behavior for command-line tools, HTTP responses, logs, and agent
transcripts should be:

- no subject identifiers unless explicitly requested;
- no bearer tokens;
- no raw federated query logs;
- no institutional configuration dumps;
- no full Phenopacket contents in diagnostics.

Explicit flags may expose more detail for synthetic, public, or otherwise
non-sensitive data.

