# Quality Control

Quality control should cover code, schemas, examples, references, and generated
artifacts.

Remote checks should include:

- Rust format, lint, tests, docs, and audit;
- Python lint and tests;
- MkDocs strict build;
- LinkML schema lint and example validation;
- reference-cache and evidence-snippet checks once evidence examples are tracked.

Security review should happen whenever dependencies, imports, workflows, agent
hooks, generated files, caches, or imported external material change.
