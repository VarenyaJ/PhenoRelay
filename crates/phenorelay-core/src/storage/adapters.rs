use super::{BackendCapabilities, BackendKind, BackendRole};

pub mod sqlite {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_release_activation: true,
            supports_existence: true,
            supports_counts: true,
            supports_records: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_medical_action_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::Sqlite, BackendRole::ServingIndex)
        }
    }
}

pub mod postgres {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_release_activation: true,
            supports_existence: true,
            supports_counts: true,
            supports_records: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_medical_action_filters: true,
            supports_gene_filters: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::Postgres, BackendRole::ServingIndex)
        }
    }
}

pub mod mongodb {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_existence: true,
            supports_counts: true,
            supports_records: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_medical_action_filters: true,
            supports_variant_filters: true,
            supports_descendant_expansion: true,
            ..BackendCapabilities::scaffolded(BackendKind::MongoDb, BackendRole::ServingIndex)
        }
    }
}

pub mod clickhouse {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_existence: true,
            supports_counts: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_gene_filters: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::ClickHouse, BackendRole::ServingIndex)
        }
    }
}

pub mod duckdb {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_counts: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_gene_filters: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::DuckDb, BackendRole::Analytics)
        }
    }
}

pub mod snowflake {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_counts: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_gene_filters: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::Snowflake, BackendRole::Warehouse)
        }
    }
}

pub mod redshift {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_counts: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_gene_filters: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::Redshift, BackendRole::Warehouse)
        }
    }
}

pub mod databricks_sql {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_counts: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_gene_filters: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::DatabricksSql, BackendRole::Warehouse)
        }
    }
}

pub mod parquet {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_release_activation: true,
            supports_counts: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_gene_filters: true,
            supports_variant_filters: true,
            beacon_compatible_adapter_target: false,
            ..BackendCapabilities::scaffolded(BackendKind::Parquet, BackendRole::Analytics)
        }
    }
}

pub mod arrow {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_counts: true,
            beacon_compatible_adapter_target: false,
            ..BackendCapabilities::scaffolded(BackendKind::Arrow, BackendRole::TableFormat)
        }
    }
}

pub mod avro {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_release_activation: true,
            beacon_compatible_adapter_target: false,
            ..BackendCapabilities::scaffolded(BackendKind::Avro, BackendRole::TableFormat)
        }
    }
}

pub mod delta_lake {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_release_activation: true,
            supports_counts: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_gene_filters: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::DeltaLake, BackendRole::TableFormat)
        }
    }
}

pub mod hudi {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_release_activation: true,
            supports_counts: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_gene_filters: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::Hudi, BackendRole::TableFormat)
        }
    }
}

pub mod iceberg {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_release_activation: true,
            supports_counts: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_gene_filters: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::Iceberg, BackendRole::Analytics)
        }
    }
}

pub mod polaris {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_release_activation: true,
            beacon_compatible_adapter_target: false,
            ..BackendCapabilities::scaffolded(BackendKind::Polaris, BackendRole::TableFormat)
        }
    }
}

pub mod trino {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_counts: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_gene_filters: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::Trino, BackendRole::Analytics)
        }
    }
}

pub mod bigquery {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_counts: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_gene_filters: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::BigQuery, BackendRole::Analytics)
        }
    }
}

pub mod apache_doris {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_counts: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_gene_filters: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::ApacheDoris, BackendRole::Warehouse)
        }
    }
}

pub mod opensearch {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_existence: true,
            supports_counts: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_full_text: true,
            ..BackendCapabilities::scaffolded(BackendKind::OpenSearch, BackendRole::Search)
        }
    }
}

pub mod elasticsearch {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_existence: true,
            supports_counts: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_full_text: true,
            ..BackendCapabilities::scaffolded(BackendKind::Elasticsearch, BackendRole::Search)
        }
    }
}

pub mod hail {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_counts: true,
            supports_gene_filters: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::Hail, BackendRole::GenomicsEngine)
        }
    }
}

pub mod spark {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_counts: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_gene_filters: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::Spark, BackendRole::ComputeEngine)
        }
    }
}

pub mod sail {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_counts: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_gene_filters: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::Sail, BackendRole::ComputeEngine)
        }
    }
}

pub mod velox {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_counts: true,
            beacon_compatible_adapter_target: false,
            ..BackendCapabilities::scaffolded(BackendKind::Velox, BackendRole::ComputeEngine)
        }
    }
}

pub mod lakehouse {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_release_activation: true,
            supports_counts: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_gene_filters: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::Lakehouse, BackendRole::Analytics)
        }
    }
}

pub mod terra {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_counts: true,
            supports_gene_filters: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::Terra, BackendRole::DeploymentPlatform)
        }
    }
}

pub mod anvil {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_counts: true,
            supports_gene_filters: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::Anvil, BackendRole::DeploymentPlatform)
        }
    }
}

pub mod gnomad {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_gene_filters: true,
            supports_variant_filters: true,
            beacon_compatible_adapter_target: false,
            ..BackendCapabilities::scaffolded(BackendKind::Gnomad, BackendRole::ReferenceResource)
        }
    }
}

pub mod hdf5 {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_counts: true,
            beacon_compatible_adapter_target: false,
            ..BackendCapabilities::scaffolded(BackendKind::Hdf5, BackendRole::TableFormat)
        }
    }
}

pub mod genomicsdb {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_existence: true,
            supports_counts: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::GenomicsDb, BackendRole::GenomicsEngine)
        }
    }
}

pub mod tiledb {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_existence: true,
            supports_counts: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::TileDb, BackendRole::GenomicsEngine)
        }
    }
}

pub mod tiledb_vcf {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_existence: true,
            supports_counts: true,
            supports_variant_filters: true,
            ..BackendCapabilities::scaffolded(BackendKind::TileDbVcf, BackendRole::GenomicsEngine)
        }
    }
}

pub mod fhir {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_records: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_medical_action_filters: true,
            ..BackendCapabilities::scaffolded(
                BackendKind::Fhir,
                BackendRole::ClinicalInteroperability,
            )
        }
    }
}

pub mod omop {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            supports_counts: true,
            supports_phenotype_filters: true,
            supports_disease_filters: true,
            supports_medical_action_filters: true,
            ..BackendCapabilities::scaffolded(
                BackendKind::Omop,
                BackendRole::ClinicalInteroperability,
            )
        }
    }
}

pub mod redis_valkey {
    use super::*;

    pub fn capabilities() -> BackendCapabilities {
        BackendCapabilities {
            beacon_compatible_adapter_target: false,
            ..BackendCapabilities::scaffolded(BackendKind::RedisValkey, BackendRole::Cache)
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn cache_adapter_is_not_an_analytical_backend() {
        let capabilities = redis_valkey::capabilities();

        assert_eq!(capabilities.role, BackendRole::Cache);
        assert!(!capabilities.supports_counts);
        assert!(!capabilities.beacon_compatible_adapter_target);
    }

    #[test]
    fn sqlite_is_scaffolded_as_a_peer_adapter() {
        let capabilities = sqlite::capabilities();

        assert_eq!(capabilities.kind, BackendKind::Sqlite);
        assert!(capabilities.supports_release_activation);
        assert!(capabilities.supports_counts);
    }
}
