# Beacon HTTP Adapter

Beacon v2 is an interoperability surface for PhenoRelay, not the internal data
model. PhenoRelay stores and queries Phenopacket-native release projections; a
Beacon-facing server should translate supported requests into PhenoRelay queries
and translate PhenoRelay outcomes back into Beacon-compatible responses.

HTTP describes the request/response API contract here. Any public, institutional,
or federated deployment should be served over HTTPS with TLS termination at the
service or a trusted reverse proxy. Plain HTTP should be limited to localhost
development, synthetic CI tests, or an internal hop that is protected by the
deployment environment.

The first Beacon-facing work should define the adapter contract before adding a
server. That keeps storage, query semantics, and privacy behavior clear before
HTTP details become load-bearing.

## Boundary

The adapter should own:

- Beacon endpoint paths and response envelopes;
- Beacon request parsing;
- mapping Beacon filters to PhenoRelay query features;
- mapping PhenoRelay outcomes to Beacon-visible responses;
- verifier-facing metadata;
- extension endpoint declarations;
- HTTPS deployment requirements and proxy assumptions.

The core model should own:

- release manifests;
- projected Phenopacket records;
- query features and match modes;
- local index behavior;
- storage adapter semantics;
- evidence and clinical impact annotations.

Storage backends should not produce Beacon response envelopes directly.

## First Endpoint Subset

The first implementation should expose only endpoints PhenoRelay can answer
truthfully from a synthetic or local release index:

- `GET /api/info` - service metadata, release identifier, supported features,
  supported granularities, and policy summary.
- `GET /api/service-info` - GA4GH service-info compatible metadata where the
  required fields are known.
- `GET /api/filtering_terms` - supported phenotype, disease, and medical-action
  terms from the activated release index.
- `POST /api/individuals` - exact existence and count queries for supported
  phenotype, disease, and medical-action filters.
- `POST /api/g_variants` - explicit unsupported response until variant indexing
  exists.

Record-level responses should stay disabled until policy and audit support exist.

PhenoRelay-native extensions can come later for clinical impact annotations,
evidence snippets, and prenatal-specific query axes. Extension endpoints should be
declared explicitly so standard Beacon clients are not misled.

## Transport Security

Deployments should assume HTTPS by default:

- terminate TLS at the PhenoRelay service or at a managed reverse proxy;
- set HSTS and secure-cookie headers when browser-facing authentication is added;
- reject bearer tokens over plaintext transports outside localhost tests;
- preserve original scheme and client metadata through trusted proxy headers only;
- document whether a deployment is public, private-network only, or verifier-only.

Local CI can still start a plain loopback server for the Beacon Verifier when no
credentials or private data are present. That is a test harness exception, not the
deployment model.

## Status Mapping

PhenoRelay statuses must not collapse into a single no-result state.

| PhenoRelay status | Beacon-facing behavior |
| --- | --- |
| `match`, `exists: true` | successful response with existence and count when permitted |
| `match`, `exists: false` | successful response with no match and count `0` when permitted |
| `unsupported` | unsupported query/filter/granularity response, not no match |
| `forbidden` | policy denial without leaking count or existence |
| `unavailable` | temporary backend, site, or peer failure without implying match state |

Before implementing this mapping, verify exact field names and error envelopes
against the Beacon v2 schemas.

## Capability Mapping

Capability responses should be derived from the manifest, activated index, and
adapter configuration:

- supported query features;
- supported response granularities;
- supported match modes;
- available filtering terms;
- ontology releases;
- Phenopacket schema version;
- active storage adapter;
- record-level response policy;
- unsupported gene, variant, descendant, and record-level query behavior.

Backend details should be disclosed only when the deployment policy allows it.

## Verifier Plan

Once HTTP endpoints exist, CI should start a synthetic local server and run the
Beacon Verifier against the standard endpoint subset.

Verifier errors should block. Verifier warnings should be captured and triaged as:

- implementation bug;
- ambiguous specification behavior;
- verifier behavior;
- intentionally unsupported endpoint or feature.

Each verifier finding that represents a real implementation bug should become a
regression fixture.

## Implementation Split

1. Design docs only.
2. HTTP skeleton with `GET /api/info` and `GET /api/service-info`.
3. Filtering terms endpoint over an activated local index.
4. Exact existence/count query mapping for supported filters.
5. Beacon Verifier CI over synthetic data.
6. Peer forwarding and partial-result behavior after local semantics are stable.

This sequence keeps the adapter reviewable and avoids mixing protocol decisions
with storage or policy work.
