# Clinical Impact Annotations

Clinical impact annotations describe why a disease, gene, variant, Phenopacket,
or query target may matter for review. They are evidence-bearing labels for
search and triage, not clinical conclusions.

PhenoRelay stores the underlying signals as separate axes:

- pregnancy and maternal impact;
- fetal or neonatal urgency;
- major health-management risk;
- neurodevelopmental impact;
- mortality timing;
- hospitalization burden;
- penetrance;
- expressivity;
- evidence quality.

Derived tiers can be used for filtering and user interfaces:

- `pregnancy_critical`;
- `major_health_management`;
- `longitudinal_prognostic_complexity`.

The axis-level labels remain visible so a derived tier can be explained. For
example, a disease can have a longitudinal neurodevelopmental signal and a
separate major-health-management signal without flattening both into one score.

Each annotation should retain its source identifier, source version, snippet,
extraction method, confidence, and review status. Deployments should use
authorized local caches for restricted sources and avoid committing credentials,
restricted cache contents, patient-specific evidence, or institutional notes.

The initial example lives at `examples/clinical-impact.yaml`. The scaffold
supports loading and summarizing annotations, but it does not yet classify new
records.
