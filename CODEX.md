# CODEX.md - PhenoRelay

Instructions for Codex working in this repository.

---

## What this repo is

**PhenoRelay** is a lightweight federated discovery network for institutions that
hold GA4GH Phenopacket v2 data.

Each site keeps its Phenopackets locally and controls what it shares. Initial query
scope includes:

- cohort statistics
- phenotypes (HPO)
- genotypes
- diseases (MONDO)
- medical actions (MAXO and maxodiff)

PhenoRelay is not a strict GA4GH Beacon implementation. Do not introduce Beacon
compatibility as a requirement unless it is explicitly requested.

---

## Architecture

- Keep Phenopackets at the originating site.
- Enforce disclosure policy at the site that owns the data.
- Authentication proves identity. Authorization determines what that identity may
  query and what response detail it may receive.
- Model response detail explicitly. At minimum, preserve the distinction between
  existence, aggregate count, and record-level results.
- A relay or coordinating node must not increase the detail returned by a remote
  site.
- Separate query models, policy decisions, storage adapters, transport, and
  federation.
- Keep query semantics independent of storage so a site can use files or a database
  without changing the public protocol.
- Use service interfaces between API handlers and storage implementations.
- Treat ontology identifiers and genomic expressions as parsed domain values, not
  unchecked strings.
- Version the inter-site protocol from the beginning.
- Prefer "parse, don't validate" at module boundaries.

---

## Site storage contract

Every participating site must maintain a versioned, cohort-organized collection of
GA4GH Phenopacket v2 JSON, following the released-data pattern of Phenopacket Store
or mgd-ppkt.

- Store one Phenopacket per JSON file.
- Group Phenopackets into stable cohort directories or provide equivalent cohort
  metadata in a manifest.
- Give every Phenopacket and subject a stable identifier within the site.
- Record the collection release, Phenopacket schema version, cohort identifier, and
  source-file checksum during indexing.
- Validate every Phenopacket before it enters the searchable index. Reject invalid
  files rather than partially indexing them.
- Treat notebooks, source tables, ETL configuration, and vendor exports as upstream
  material. PhenoRelay consumes the released Phenopacket JSON, not those source
  formats.
- Keep the source collection authoritative. The local database is a rebuildable
  search index, not the system of record.
- Support re-indexing a complete immutable release and atomically activating it.
  Do not expose a half-indexed release.
- Do not require sites to publish their collections or use GitHub. Private
  institutional storage may follow the same contract.

PhenoRelay may support directory trees, release archives, and manifests through
separate storage adapters. Do not couple query behavior to one repository layout.

---

## Security and privacy

- Never commit PHI, credentials, tokens, private keys, real patient Phenopackets,
  access logs, or institutional configuration.
- Use clearly labeled synthetic fixtures.
- Default to least privilege and the least informative response.
- Do not implement custom cryptography or a custom identity provider.
- Forward the minimum query information required by a remote site.
- Do not place sensitive query or patient content in logs, caches, traces, metrics,
  or error messages.
- Threat-model changes involving authentication, authorization, forwarding,
  aggregation, caching, auditing, or record-level responses before implementation.

---

## Development

PhenoRelay uses one authoritative Rust implementation with an official Python
interface.

- Use Cargo for Rust crates and keep `Cargo.lock` committed.
- Build Python bindings with PyO3 and maturin.
- Use `uv` for Python environments, dependencies, tests, and publishing commands.
- Use `uv sync --frozen` in CI and deployments.
- Run Python project commands through `uv run`.
- Do not use `pip install`, maintain `requirements.txt`, or create an unmanaged
  virtual environment.
- Document the exact test, lint, format, type-check, and run commands once their
  tools are added.

Rust owns parsing, projections, query semantics, indexing, policy types,
federation types, and the standalone service. Python bindings expose coarse local
operations rather than mirroring every Rust type. Keep the HTTP protocol
language-neutral.

Build Linux AppImages on a pinned Ubuntu runner or container, never directly on
Arch. Also release ordinary CLI/server archives, Python wheels, and OCI images.
Do not add Tauri or GUI dependencies unless a desktop application is explicitly
requested.

Before adding a dependency:

1. Confirm it is needed at the chosen boundary.
2. Check its license and maintenance status.
3. Pin it in the selected lockfile.
4. Add focused tests for the behavior it enables.

---

## Code and prose

- Prefer small modules with explicit domain boundaries.
- Do not add annotations, docstrings, comments, or defensive handling to code you
  did not touch.
- Do not add error handling for scenarios excluded by internal guarantees.
- Use one ASCII dash for prose punctuation, never a double dash or Unicode em dash.
  CLI flags are the exception.
- Do not add agent boilerplate such as `Document Version`, `Last Updated`,
  `Maintained By`, `Purpose`, `Owner`, `Status: Draft`, or `Author:`.
- Open documentation with its actual content.

---

## Testing

- Test every supported disclosure level for anonymous, authenticated, allowed, and
  forbidden callers.
- Run the same query contract against local and forwarded execution.
- Prove that aggregation and forwarding cannot reveal more than each site's policy
  permits.
- Cover malformed identifiers, ontology edge cases, unavailable peers, timeouts,
  partial results, and duplicates.
- Use public ontology concepts and synthetic Phenopackets.
- Every commit must leave the relevant test suite green.

---

## Git workflow

- `main` is stable.
- Keep commits small and limited to one logical change.
- Before every commit, show the diff and proposed terse commit message, then wait
  for confirmation.
- Do not use `--no-verify`.
- If a hook fails, fix the issue and create a new commit. Do not amend to bypass it.
- Do not add `Co-Authored-By` lines.
- Never stage secrets, PHI, real patient data, or local-only notes.

---

## Working agreement

For non-trivial changes:

1. Inspect current code and relevant references.
2. Discuss the design, uncertainty, privacy implications, and rejected options.
3. Restate the agreed decisions in simple language with a file-by-file change list.
4. Implement in small reviewable commits, pausing before each commit.
5. Keep each pull request focused on one concern and preferably below 500 net
   lines.

Do not silently expand work into deployment, external communication, data
migration, or protocol compatibility.

---

## Maintaining these files

`CLAUDE.md`, `AGENTS.md`, and `CODEX.md` must contain the same instruction body.
Edit `CLAUDE.md`, then regenerate the other two with only the title and introductory
sentence changed.
