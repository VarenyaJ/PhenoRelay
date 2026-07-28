# Bycon And Beacon

Beacon-style genomic discovery systems provide useful design pressure in this
space. PhenoRelay should preserve the useful product capabilities where they fit:

- capability discovery;
- filter definitions;
- response granularity;
- federation behavior;
- operational deployment lessons.

PhenoRelay should not require bycon internals, MongoDB, Progenetix-specific
schemas, or strict Beacon compatibility. The goal is a Phenopacket-native
discovery service that can interoperate later through documented adapters.

Beacon compatibility is useful only when it makes PhenoRelay easier to deploy or
interoperate. If a Phenopacket-native contract is clearer, safer, or easier to
validate, document the deviation here and keep the implementation explicit.
