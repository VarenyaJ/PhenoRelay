use std::{fmt, str::FromStr};

use serde::{Deserialize, Serialize};
use thiserror::Error;

#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd, Serialize, Deserialize)]
#[serde(try_from = "String", into = "String")]
pub struct OntologyTermId {
    prefix: String,
    local_id: String,
}

impl OntologyTermId {
    pub fn prefix(&self) -> &str {
        &self.prefix
    }

    pub fn local_id(&self) -> &str {
        &self.local_id
    }
}

impl fmt::Display for OntologyTermId {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "{}:{}", self.prefix, self.local_id)
    }
}

impl FromStr for OntologyTermId {
    type Err = IdentifierError;

    fn from_str(value: &str) -> Result<Self, Self::Err> {
        let (prefix, local_id) = value
            .split_once(':')
            .ok_or(IdentifierError::MissingSeparator)?;

        let mut prefix_characters = prefix.chars();
        if !prefix_characters
            .next()
            .is_some_and(|character| character.is_ascii_uppercase())
            || !prefix_characters
                .all(|character| character.is_ascii_uppercase() || character.is_ascii_digit())
        {
            return Err(IdentifierError::InvalidPrefix);
        }
        if local_id.is_empty()
            || !local_id.chars().all(|character| {
                character.is_ascii_alphanumeric() || matches!(character, '.' | '-' | '_' | '/')
            })
        {
            return Err(IdentifierError::InvalidLocalId);
        }

        Ok(Self {
            prefix: prefix.to_owned(),
            local_id: local_id.to_owned(),
        })
    }
}

impl TryFrom<String> for OntologyTermId {
    type Error = IdentifierError;

    fn try_from(value: String) -> Result<Self, Self::Error> {
        value.parse()
    }
}

impl From<OntologyTermId> for String {
    fn from(value: OntologyTermId) -> Self {
        value.to_string()
    }
}

#[derive(Clone, Debug, Eq, Error, PartialEq)]
pub enum IdentifierError {
    #[error("ontology identifier must contain a colon")]
    MissingSeparator,
    #[error("ontology prefix must contain only uppercase ASCII letters and digits")]
    InvalidPrefix,
    #[error("ontology local identifier contains unsupported characters")]
    InvalidLocalId,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_supported_ontology_identifiers() {
        for value in ["HP:0001250", "MONDO:0005148", "MAXO:0000017"] {
            let identifier: OntologyTermId = value.parse().unwrap();
            assert_eq!(identifier.to_string(), value);
        }
    }

    #[test]
    fn rejects_unparsed_strings() {
        assert_eq!(
            "hp:0001250".parse::<OntologyTermId>(),
            Err(IdentifierError::InvalidPrefix)
        );
        assert_eq!(
            "1HP:0001250".parse::<OntologyTermId>(),
            Err(IdentifierError::InvalidPrefix)
        );
        assert_eq!(
            "HP0001250".parse::<OntologyTermId>(),
            Err(IdentifierError::MissingSeparator)
        );
    }

    #[test]
    fn deserialization_uses_the_parser() {
        assert!(serde_json::from_str::<OntologyTermId>("\"HP:0001250\"").is_ok());
        assert!(serde_json::from_str::<OntologyTermId>("\"hp:0001250\"").is_err());
    }
}
