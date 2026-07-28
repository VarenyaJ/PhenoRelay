# Rust And Python Tradeoffs

PhenoRelay starts with both Rust and Python because the project has two different
kinds of work.

Rust should absorb code that benefits from a small deployable binary, predictable
performance, strong types, and minimal runtime dependencies. Good candidates:

- Phenopacket projection;
- local indexing;
- query evaluation;
- response-policy enforcement;
- HTTP service and federation primitives.

Python should own tooling where the ecosystem is already mature. Good candidates:

- LinkML schema generation;
- PubMed and reference-cache validation;
- ontology validation wrappers;
- MkDocs documentation;
- notebooks;
- Claude and other agent workflows.

Migration decisions should be made per capability. A Python capability can move
to Rust when it becomes part of the runtime path, needs deployment without Python,
or is stable enough that reimplementation will not churn. Until then, Python
tooling can generate artifacts and contracts that Rust consumes.

