from __future__ import annotations

from pathlib import Path

from phenorelay.index import LocalReleaseIndex, load_projected_records
from phenorelay.manifest import load_site_manifest
from phenorelay.query_service import QueryService


def test_query_service_wraps_query_outcome_with_release_metadata() -> None:
    response = example_service().query(
        {
            "query_id": "q1",
            "feature": "phenotype",
            "term": "HP:0001250",
            "match_mode": "exact",
            "presence": "present",
            "requested_granularity": "count",
        }
    )

    assert response["release"]["site_id"] == "synthetic-site"
    assert response["outcome"]["count"] == 1


def test_query_service_builds_filtering_terms() -> None:
    terms = example_service().filtering_terms()

    assert {
        (term["feature"], term["term"], term["presence"], term["count"]) for term in terms
    } >= {
        ("phenotype", "HP:0001250", "present", 1),
        ("phenotype", "HP:0011344", "excluded", 1),
        ("disease", "MONDO:0000001", "present", 1),
        ("medical_action", "MAXO:0000072", None, 1),
    }


def test_query_service_record_summaries_include_projection_metadata() -> None:
    summaries = example_service().record_summaries()

    assert summaries[0]["phenopacket_id"] == "synthetic-packet-1"
    assert summaries[0]["source_cohort"] is None
    assert summaries[0]["gene_count"] == 0


def example_service() -> QueryService:
    return QueryService(
        LocalReleaseIndex.build(
            manifest=load_site_manifest(Path("examples/site-manifest.yaml")),
            records=load_projected_records(Path("examples/projected-records.yaml")),
        )
    )
