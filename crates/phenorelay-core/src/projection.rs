use phenopackets::schema::v2::Phenopacket;
use phenopackets::schema::v2::core::medical_action;
use phenopackets::schema::v2::core::{MedicalAction, OntologyClass};
use thiserror::Error;
use tracing::{debug, warn};

use crate::{IdentifierError, OntologyTermId, TermPresence};

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct RecordProjection {
    phenopacket_id: String,
    subject_id: String,
    phenotypes: Vec<ProjectedPhenotype>,
    diseases: Vec<ProjectedDisease>,
    recorded_medical_actions: Vec<OntologyTermId>,
    has_genomic_interpretations: bool,
}

impl RecordProjection {
    pub fn new(
        phenopacket_id: String,
        subject_id: String,
        phenotypes: Vec<ProjectedPhenotype>,
        diseases: Vec<ProjectedDisease>,
        recorded_medical_actions: Vec<OntologyTermId>,
        has_genomic_interpretations: bool,
    ) -> Self {
        Self {
            phenopacket_id,
            subject_id,
            phenotypes,
            diseases,
            recorded_medical_actions,
            has_genomic_interpretations,
        }
    }

    pub fn phenopacket_id(&self) -> &str {
        &self.phenopacket_id
    }

    pub fn subject_id(&self) -> &str {
        &self.subject_id
    }

    pub fn phenotypes(&self) -> &[ProjectedPhenotype] {
        &self.phenotypes
    }

    pub fn diseases(&self) -> &[ProjectedDisease] {
        &self.diseases
    }

    pub fn recorded_medical_actions(&self) -> &[OntologyTermId] {
        &self.recorded_medical_actions
    }

    pub fn has_genomic_interpretations(&self) -> bool {
        self.has_genomic_interpretations
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ProjectedPhenotype {
    term: OntologyTermId,
    presence: TermPresence,
}

impl ProjectedPhenotype {
    pub fn new(term: OntologyTermId, presence: TermPresence) -> Self {
        Self { term, presence }
    }

    pub fn term(&self) -> &OntologyTermId {
        &self.term
    }

    pub fn presence(&self) -> TermPresence {
        self.presence
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ProjectedDisease {
    term: OntologyTermId,
    presence: TermPresence,
}

impl ProjectedDisease {
    pub fn new(term: OntologyTermId, presence: TermPresence) -> Self {
        Self { term, presence }
    }

    pub fn term(&self) -> &OntologyTermId {
        &self.term
    }

    pub fn presence(&self) -> TermPresence {
        self.presence
    }
}

#[derive(Debug, Error)]
pub enum ProjectionError {
    #[error("phenopacket JSON could not be parsed")]
    Json {
        #[from]
        source: serde_json::Error,
    },
    #[error("phenopacket.id is required")]
    MissingPhenopacketId,
    #[error("subject.id is required")]
    MissingSubjectId,
    #[error("ontology class is required at {field}")]
    MissingOntologyClass { field: String },
    #[error("ontology identifier is invalid at {field}: {source}")]
    InvalidOntologyIdentifier {
        field: String,
        value: String,
        #[source]
        source: IdentifierError,
    },
    #[error("medical action is required at {field}")]
    MissingMedicalAction { field: String },
    #[error("unsupported medical action at {field}: {action}")]
    UnsupportedMedicalAction { field: String, action: String },
}

pub fn parse_phenopacket_json(bytes: &[u8]) -> Result<Phenopacket, ProjectionError> {
    serde_json::from_slice(bytes).map_err(ProjectionError::from)
}

pub fn project_phenopacket(phenopacket: &Phenopacket) -> Result<RecordProjection, ProjectionError> {
    debug!("projecting phenopacket");
    let projection = project_phenopacket_inner(phenopacket);

    match &projection {
        Ok(projection) => {
            debug!(
                phenotypes = projection.phenotypes.len(),
                diseases = projection.diseases.len(),
                recorded_medical_actions = projection.recorded_medical_actions.len(),
                has_genomic_interpretations = projection.has_genomic_interpretations,
                "projected phenopacket"
            );
        }
        Err(error) => {
            warn!(error = %error, "phenopacket projection failed");
        }
    }

    projection
}

fn project_phenopacket_inner(
    phenopacket: &Phenopacket,
) -> Result<RecordProjection, ProjectionError> {
    let phenopacket_id =
        required_non_empty(&phenopacket.id, ProjectionError::MissingPhenopacketId)?;
    let subject = phenopacket
        .subject
        .as_ref()
        .ok_or(ProjectionError::MissingSubjectId)?;
    let subject_id = required_non_empty(&subject.id, ProjectionError::MissingSubjectId)?;

    let mut phenotypes = phenopacket
        .phenotypic_features
        .iter()
        .enumerate()
        .map(|(index, feature)| {
            let field = format!("phenotypicFeatures[{index}].type");
            let term = parse_required_ontology_class(feature.r#type.as_ref(), &field)?;
            let presence = if feature.excluded {
                TermPresence::Excluded
            } else {
                TermPresence::Present
            };
            Ok(ProjectedPhenotype::new(term, presence))
        })
        .collect::<Result<Vec<_>, ProjectionError>>()?;

    let mut diseases = Vec::new();
    for (index, disease) in phenopacket.diseases.iter().enumerate() {
        let field = format!("diseases[{index}].term");
        let term = parse_required_ontology_class(disease.term.as_ref(), &field)?;
        let presence = if disease.excluded {
            TermPresence::Excluded
        } else {
            TermPresence::Present
        };
        diseases.push(ProjectedDisease::new(term, presence));
    }
    for (index, interpretation) in phenopacket.interpretations.iter().enumerate() {
        if let Some(diagnosis) = &interpretation.diagnosis {
            let field = format!("interpretations[{index}].diagnosis.disease");
            let term = parse_required_ontology_class(diagnosis.disease.as_ref(), &field)?;
            diseases.push(ProjectedDisease::new(term, TermPresence::Present));
        }
    }

    let mut recorded_medical_actions = phenopacket
        .medical_actions
        .iter()
        .enumerate()
        .map(project_recorded_medical_action)
        .collect::<Result<Vec<_>, ProjectionError>>()?;

    let has_genomic_interpretations = phenopacket
        .interpretations
        .iter()
        .filter_map(|interpretation| interpretation.diagnosis.as_ref())
        .any(|diagnosis| !diagnosis.genomic_interpretations.is_empty());

    // Keep projection output stable for tests and later indexing. We intentionally
    // do not deduplicate yet: repeated HPO or MAXO assertions may carry meaning,
    // and the indexing policy needs to decide that explicitly.
    phenotypes.sort_by(|left, right| {
        left.term
            .cmp(&right.term)
            .then(left.presence.cmp(&right.presence))
    });
    diseases.sort_by(|left, right| {
        left.term
            .cmp(&right.term)
            .then(left.presence.cmp(&right.presence))
    });
    recorded_medical_actions.sort();

    Ok(RecordProjection::new(
        phenopacket_id.to_owned(),
        subject_id.to_owned(),
        phenotypes,
        diseases,
        recorded_medical_actions,
        has_genomic_interpretations,
    ))
}

fn project_recorded_medical_action(
    (index, medical_action): (usize, &MedicalAction),
) -> Result<OntologyTermId, ProjectionError> {
    let field = format!("medicalActions[{index}].procedure");
    match medical_action.action.as_ref() {
        Some(medical_action::Action::Procedure(procedure)) => {
            parse_required_ontology_class(procedure.code.as_ref(), &format!("{field}.code"))
        }
        Some(medical_action::Action::Treatment(_)) => {
            unsupported_medical_action(field, "treatment")
        }
        Some(medical_action::Action::RadiationTherapy(_)) => {
            unsupported_medical_action(field, "radiation_therapy")
        }
        Some(medical_action::Action::TherapeuticRegimen(_)) => {
            unsupported_medical_action(field, "therapeutic_regimen")
        }
        None => Err(ProjectionError::MissingMedicalAction { field }),
    }
}

fn unsupported_medical_action(
    field: String,
    action: &str,
) -> Result<OntologyTermId, ProjectionError> {
    debug!(
        field = field,
        action = action,
        "unsupported medical action during projection"
    );
    // TODO: Decide how treatment, radiation therapy, and therapeutic regimen
    // records should be represented before indexing them as queryable actions.
    Err(ProjectionError::UnsupportedMedicalAction {
        field,
        action: action.to_owned(),
    })
}

fn parse_required_ontology_class(
    ontology_class: Option<&OntologyClass>,
    field: &str,
) -> Result<OntologyTermId, ProjectionError> {
    let ontology_class = ontology_class.ok_or_else(|| ProjectionError::MissingOntologyClass {
        field: field.to_owned(),
    })?;

    ontology_class
        .id
        .parse()
        .map_err(|source| ProjectionError::InvalidOntologyIdentifier {
            field: format!("{field}.id"),
            value: ontology_class.id.clone(),
            source,
        })
}

fn required_non_empty(value: &str, error: ProjectionError) -> Result<&str, ProjectionError> {
    if value.is_empty() {
        Err(error)
    } else {
        Ok(value)
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn projects_required_record_identity() {
        let phenopacket = parse_phenopacket_json(
            br#"{
              "id": "packet-1",
              "subject": { "id": "subject-1" }
            }"#,
        )
        .unwrap();

        let projection = project_phenopacket(&phenopacket).unwrap();

        assert_eq!(projection.phenopacket_id(), "packet-1");
        assert_eq!(projection.subject_id(), "subject-1");
    }

    #[test]
    fn projects_present_and_excluded_phenotypes() {
        let phenopacket = parse_phenopacket_json(
            br#"{
              "id": "packet-1",
              "subject": { "id": "subject-1" },
              "phenotypicFeatures": [
                { "type": { "id": "HP:0001250", "label": "Seizure" } },
                {
                  "type": { "id": "HP:0004322", "label": "Short stature" },
                  "excluded": true
                }
              ]
            }"#,
        )
        .unwrap();

        let projection = project_phenopacket(&phenopacket).unwrap();

        assert_eq!(
            projection.phenotypes(),
            &[
                ProjectedPhenotype::new("HP:0001250".parse().unwrap(), TermPresence::Present),
                ProjectedPhenotype::new("HP:0004322".parse().unwrap(), TermPresence::Excluded),
            ]
        );
    }

    #[test]
    fn projects_top_level_and_interpretation_diseases() {
        let phenopacket = parse_phenopacket_json(
            br#"{
              "id": "packet-1",
              "subject": { "id": "subject-1" },
              "diseases": [
                { "term": { "id": "MONDO:0005148", "label": "Type 2 diabetes mellitus" } },
                {
                  "term": { "id": "OMIM:101600", "label": "Pfeiffer syndrome" },
                  "excluded": true
                }
              ],
              "interpretations": [
                {
                  "id": "interpretation-1",
                  "diagnosis": {
                    "disease": { "id": "OMIM:101600", "label": "Pfeiffer syndrome" }
                  }
                }
              ]
            }"#,
        )
        .unwrap();

        let projection = project_phenopacket(&phenopacket).unwrap();

        assert_eq!(
            projection.diseases(),
            &[
                ProjectedDisease::new("MONDO:0005148".parse().unwrap(), TermPresence::Present),
                ProjectedDisease::new("OMIM:101600".parse().unwrap(), TermPresence::Present),
                ProjectedDisease::new("OMIM:101600".parse().unwrap(), TermPresence::Excluded),
            ]
        );
    }

    #[test]
    fn projects_recorded_procedure_medical_actions_only() {
        let phenopacket = parse_phenopacket_json(
            br#"{
              "id": "packet-1",
              "subject": { "id": "subject-1" },
              "medicalActions": [
                {
                  "procedure": {
                    "code": { "id": "MAXO:0000072", "label": "Ultrasonography procedure" }
                  }
                }
              ]
            }"#,
        )
        .unwrap();

        let projection = project_phenopacket(&phenopacket).unwrap();

        assert_eq!(
            projection.recorded_medical_actions(),
            &["MAXO:0000072".parse().unwrap()]
        );
    }

    #[test]
    fn flags_genomic_interpretations_without_projecting_variant_details() {
        let phenopacket = parse_phenopacket_json(
            br#"{
              "id": "packet-1",
              "subject": { "id": "subject-1" },
              "interpretations": [
                {
                  "id": "interpretation-1",
                  "diagnosis": {
                    "disease": { "id": "OMIM:101600", "label": "Pfeiffer syndrome" },
                    "genomicInterpretations": [
                      {
                        "subjectOrBiosampleId": "subject-1",
                        "interpretationStatus": "CAUSATIVE",
                        "gene": { "valueId": "HGNC:1234", "symbol": "GENE1" }
                      }
                    ]
                  }
                }
              ]
            }"#,
        )
        .unwrap();

        let projection = project_phenopacket(&phenopacket).unwrap();

        assert!(projection.has_genomic_interpretations());
    }

    #[test]
    fn fails_projection_for_missing_subject_id() {
        let phenopacket = parse_phenopacket_json(
            br#"{
              "id": "packet-1",
              "subject": {}
            }"#,
        )
        .unwrap();

        assert!(matches!(
            project_phenopacket(&phenopacket),
            Err(ProjectionError::MissingSubjectId)
        ));
    }

    #[test]
    fn fails_projection_for_malformed_phenotype_id() {
        let phenopacket = parse_phenopacket_json(
            br#"{
              "id": "packet-1",
              "subject": { "id": "subject-1" },
              "phenotypicFeatures": [
                { "type": { "id": "hp:0001250", "label": "Seizure" } }
              ]
            }"#,
        )
        .unwrap();

        let error = project_phenopacket(&phenopacket).unwrap_err();

        match error {
            ProjectionError::InvalidOntologyIdentifier { field, value, .. } => {
                assert_eq!(field, "phenotypicFeatures[0].type.id");
                assert_eq!(value, "hp:0001250");
            }
            other => panic!("unexpected error: {other:?}"),
        }
    }

    #[test]
    fn fails_projection_for_missing_phenotype_type() {
        let phenopacket = parse_phenopacket_json(
            br#"{
              "id": "packet-1",
              "subject": { "id": "subject-1" },
              "phenotypicFeatures": [{}]
            }"#,
        )
        .unwrap();

        assert!(matches!(
            project_phenopacket(&phenopacket),
            Err(ProjectionError::MissingOntologyClass { field })
                if field == "phenotypicFeatures[0].type"
        ));
    }

    #[test]
    fn fails_projection_for_non_procedure_medical_action() {
        let phenopacket = parse_phenopacket_json(
            br#"{
              "id": "packet-1",
              "subject": { "id": "subject-1" },
              "medicalActions": [
                {
                  "treatment": {
                    "agent": { "id": "DrugCentral:1234", "label": "Example drug" }
                  }
                }
              ]
            }"#,
        )
        .unwrap();

        assert!(matches!(
            project_phenopacket(&phenopacket),
            Err(ProjectionError::UnsupportedMedicalAction { action, .. })
                if action == "treatment"
        ));
    }
}
