# Capability-Aware Federation

Federated discovery needs capability reporting before query aggregation. A site
that cannot evaluate a feature must not look the same as a site that evaluated
the feature and found zero matches.

PhenoRelay responses should preserve these states:

- match or no match;
- unsupported feature;
- forbidden by policy;
- unavailable peer or index.

Future relay nodes must never increase the detail returned by a data-owning site.

Beacon-facing adapters must preserve the same distinctions. A query feature that
is not implemented should remain unsupported, even if the Beacon-facing response
shape differs from the native PhenoRelay response.
