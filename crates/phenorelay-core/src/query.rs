use serde::{Deserialize, Serialize};

use crate::OntologyTermId;

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum MatchMode {
    Exact,
    Descendants,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum TermPresence {
    Present,
    Excluded,
    Any,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ResponseGranularity {
    Existence,
    Count,
    Record,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "feature", rename_all = "snake_case")]
pub enum Query {
    Phenotype {
        term: OntologyTermId,
        match_mode: MatchMode,
        presence: TermPresence,
    },
    Disease {
        term: OntologyTermId,
        match_mode: MatchMode,
    },
    MedicalAction {
        term: OntologyTermId,
        match_mode: MatchMode,
    },
    Gene {
        symbol: String,
    },
}

impl Query {
    pub fn feature(&self) -> QueryFeature {
        match self {
            Self::Phenotype { .. } => QueryFeature::Phenotype,
            Self::Disease { .. } => QueryFeature::Disease,
            Self::MedicalAction { .. } => QueryFeature::MedicalAction,
            Self::Gene { .. } => QueryFeature::Gene,
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum QueryFeature {
    Phenotype,
    Disease,
    MedicalAction,
    Gene,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(tag = "status", rename_all = "snake_case")]
pub enum QueryOutcome {
    Match { exists: bool, count: Option<u64> },
    Unsupported { feature: QueryFeature },
    Forbidden,
    Unavailable { reason: UnavailableReason },
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum UnavailableReason {
    Timeout,
    PeerError,
    IndexNotReady,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn preserves_unsupported_as_distinct_from_no_match() {
        let no_match = QueryOutcome::Match {
            exists: false,
            count: Some(0),
        };
        let unsupported = QueryOutcome::Unsupported {
            feature: QueryFeature::Gene,
        };

        assert_ne!(no_match, unsupported);
    }

    #[test]
    fn query_round_trips_through_json() {
        let query = Query::Phenotype {
            term: "HP:0001250".parse().unwrap(),
            match_mode: MatchMode::Descendants,
            presence: TermPresence::Present,
        };

        let json = serde_json::to_string(&query).unwrap();
        assert_eq!(serde_json::from_str::<Query>(&json).unwrap(), query);
    }
}
