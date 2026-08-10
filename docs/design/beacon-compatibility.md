# Beacon Compatibility

Beacon-style genomic discovery systems provide useful design pressure in this
space. PhenoRelay should preserve the product capabilities where they fit:

- capability discovery;
- filter definitions;
- response granularity;
- federation behavior;
- verifier-backed compatibility checks;
- operational deployment lessons.

PhenoRelay should not require any specific Beacon implementation, database,
deployment layout, or upstream internal schema. The goal is a Phenopacket-native
discovery service that can interoperate through documented adapters.

Beacon compatibility is useful only when it makes PhenoRelay easier to deploy or
interoperate. If a Phenopacket-native contract is clearer, safer, or easier to
validate, document the deviation here and keep the implementation explicit.

The first Beacon-facing HTTP work should be an adapter contract, not server code.
The current plan is documented in [Beacon HTTP Adapter](beacon-http-adapter.md).
Public and federated deployments should use HTTPS; plain HTTP is only appropriate
for localhost development and synthetic verifier tests.
