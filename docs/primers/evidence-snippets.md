# Evidence Snippets

Evidence snippets are short quoted passages attached to a claim or example so a
reviewer can check why the claim exists.

The intended contract:

- each snippet cites a structured reference identifier;
- quoted text should match the fetched reference content when a validator can
  check it;
- generated or cached reference files must remain reviewable;
- validation should run through explicit commands and CI, not on package import.

Evidence support is optional for core discovery, but useful for examples, query
interpretation notes, and agent-assisted review.

The first command is:

```bash
uv run phenorelay validate-evidence examples/query-outcome.yaml --cache-dir examples/reference-cache
```

It reports one JSON object per snippet and exits non-zero when a reference is
missing from the reviewed cache or the quoted text is not found.
