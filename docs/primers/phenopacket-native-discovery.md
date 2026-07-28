# Phenopacket-Native Discovery

PhenoRelay treats released GA4GH Phenopacket JSON as the source data. Indexes,
reports, and caches are derived artifacts.

The discovery model starts with a small projection:

- record identifier;
- subject identifier, redacted from ordinary command output;
- HPO phenotype terms with present or excluded state;
- disease terms;
- medical action terms;
- genomic interpretation hints.

The projection is intentionally smaller than the full Phenopacket. Query code
should index the fields it supports and report unsupported features explicitly.

