use crate::{MatchMode, Query, QueryFeature, QueryOutcome, RecordProjection, TermPresence};

pub mod adapters;

#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum BackendKind {
    Memory,
    Sqlite,
    Postgres,
    MongoDb,
    ClickHouse,
    DuckDb,
    Snowflake,
    Redshift,
    DatabricksSql,
    Parquet,
    Arrow,
    Avro,
    DeltaLake,
    Hudi,
    Iceberg,
    Polaris,
    Trino,
    BigQuery,
    ApacheDoris,
    OpenSearch,
    Elasticsearch,
    Hail,
    GenomicsDb,
    TileDb,
    TileDbVcf,
    Spark,
    Sail,
    Velox,
    Lakehouse,
    Terra,
    Anvil,
    Gnomad,
    Hdf5,
    Fhir,
    Omop,
    RedisValkey,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum BackendRole {
    ServingIndex,
    Analytics,
    GenomicsEngine,
    ClinicalInteroperability,
    Search,
    Warehouse,
    TableFormat,
    ComputeEngine,
    DeploymentPlatform,
    ReferenceResource,
    Cache,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum BackendStatus {
    Implemented,
    Scaffolded,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BackendCapabilities {
    pub kind: BackendKind,
    pub role: BackendRole,
    pub status: BackendStatus,
    pub supports_release_activation: bool,
    pub supports_existence: bool,
    pub supports_counts: bool,
    pub supports_records: bool,
    pub supports_phenotype_filters: bool,
    pub supports_disease_filters: bool,
    pub supports_medical_action_filters: bool,
    pub supports_gene_filters: bool,
    pub supports_variant_filters: bool,
    pub supports_descendant_expansion: bool,
    pub supports_full_text: bool,
    pub beacon_compatible_adapter_target: bool,
}

impl BackendCapabilities {
    pub const fn scaffolded(kind: BackendKind, role: BackendRole) -> Self {
        Self {
            kind,
            role,
            status: BackendStatus::Scaffolded,
            supports_release_activation: false,
            supports_existence: false,
            supports_counts: false,
            supports_records: false,
            supports_phenotype_filters: false,
            supports_disease_filters: false,
            supports_medical_action_filters: false,
            supports_gene_filters: false,
            supports_variant_filters: false,
            supports_descendant_expansion: false,
            supports_full_text: false,
            beacon_compatible_adapter_target: true,
        }
    }

    pub const fn implemented(kind: BackendKind, role: BackendRole) -> Self {
        Self {
            status: BackendStatus::Implemented,
            ..Self::scaffolded(kind, role)
        }
    }
}

pub trait StorageBackend {
    fn capabilities(&self) -> BackendCapabilities;
    fn query(&self, query: &Query) -> QueryOutcome;
}

#[derive(Clone, Debug, Default)]
pub struct MemoryBackend {
    records: Vec<RecordProjection>,
}

impl MemoryBackend {
    pub fn new(records: Vec<RecordProjection>) -> Self {
        Self { records }
    }
}

impl StorageBackend for MemoryBackend {
    fn capabilities(&self) -> BackendCapabilities {
        BackendCapabilities {
            supports_release_activation: true,
            supports_existence: true,
            supports_counts: true,
            supports_records: false,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_medical_action_filters: true,
            supports_gene_filters: false,
            supports_variant_filters: false,
            supports_descendant_expansion: false,
            supports_full_text: false,
            ..BackendCapabilities::implemented(BackendKind::Memory, BackendRole::ServingIndex)
        }
    }

    fn query(&self, query: &Query) -> QueryOutcome {
        if matches!(
            query,
            Query::Phenotype {
                match_mode: MatchMode::Descendants,
                ..
            } | Query::Disease {
                match_mode: MatchMode::Descendants,
                ..
            } | Query::MedicalAction {
                match_mode: MatchMode::Descendants,
                ..
            }
        ) {
            return QueryOutcome::Unsupported {
                feature: query.feature(),
            };
        }

        match query {
            Query::Phenotype { term, presence, .. } => {
                let count = self
                    .records
                    .iter()
                    .filter(|record| {
                        record.phenotypes().iter().any(|phenotype| {
                            phenotype.term() == term
                                && matches_presence(phenotype.presence(), *presence)
                        })
                    })
                    .count() as u64;
                matched_count(count)
            }
            Query::Disease { term, .. } => {
                let count = self
                    .records
                    .iter()
                    .filter(|record| {
                        record
                            .diseases()
                            .iter()
                            .any(|disease| disease.term() == term)
                    })
                    .count() as u64;
                matched_count(count)
            }
            Query::MedicalAction { term, .. } => {
                let count = self
                    .records
                    .iter()
                    .filter(|record| {
                        record
                            .recorded_medical_actions()
                            .iter()
                            .any(|action| action == term)
                    })
                    .count() as u64;
                matched_count(count)
            }
            Query::Gene { .. } => QueryOutcome::Unsupported {
                feature: QueryFeature::Gene,
            },
        }
    }
}

fn matches_presence(candidate: TermPresence, requested: TermPresence) -> bool {
    requested == TermPresence::Any || candidate == requested
}

fn matched_count(count: u64) -> QueryOutcome {
    QueryOutcome::Match {
        exists: count > 0,
        count: Some(count),
    }
}

#[cfg(test)]
mod tests {
    use crate::{OntologyTermId, ProjectedDisease, ProjectedPhenotype};

    use super::*;

    #[test]
    fn memory_backend_counts_exact_phenotype_matches() {
        let backend =
            MemoryBackend::new(vec![record("HP:0001250", "MONDO:0000001", "MAXO:0000072")]);
        let query = Query::Phenotype {
            term: "HP:0001250".parse().unwrap(),
            match_mode: MatchMode::Exact,
            presence: TermPresence::Present,
        };

        assert_eq!(
            backend.query(&query),
            QueryOutcome::Match {
                exists: true,
                count: Some(1)
            }
        );
    }

    #[test]
    fn memory_backend_keeps_descendant_queries_distinct_from_zero_matches() {
        let backend =
            MemoryBackend::new(vec![record("HP:0001250", "MONDO:0000001", "MAXO:0000072")]);
        let query = Query::Phenotype {
            term: "HP:0001250".parse().unwrap(),
            match_mode: MatchMode::Descendants,
            presence: TermPresence::Present,
        };

        assert_eq!(
            backend.query(&query),
            QueryOutcome::Unsupported {
                feature: QueryFeature::Phenotype
            }
        );
    }

    fn record(phenotype: &str, disease: &str, medical_action: &str) -> RecordProjection {
        RecordProjection::new(
            "synthetic-packet-1".to_owned(),
            "synthetic-subject-1".to_owned(),
            vec![ProjectedPhenotype::new(
                phenotype.parse::<OntologyTermId>().unwrap(),
                TermPresence::Present,
            )],
            vec![ProjectedDisease::new(
                disease.parse::<OntologyTermId>().unwrap(),
                TermPresence::Present,
            )],
            vec![medical_action.parse::<OntologyTermId>().unwrap()],
            false,
        )
    }
}
