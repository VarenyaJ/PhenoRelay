# Agent Workflows

Agent workflows are optional development aids. They should help create examples,
check references, inspect ontology terms, and prepare reviewable pull requests.

Rules for agent workflows:

- use synthetic or public data unless the user explicitly authorizes otherwise;
- do not print subject identifiers, bearer tokens, raw federated queries, or full
  Phenopacket contents by default;
- run schema, ontology, and reference checks through explicit commands;
- keep generated research artifacts out of commits until reviewed;
- record design decisions in docs when they affect public behavior.

Claude-specific commands may live under `.claude/`, but public docs should explain
the workflow in terms that other coding agents can follow.

