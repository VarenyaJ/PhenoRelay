from __future__ import annotations

from pathlib import Path

from phenorelay.index import (
    LocalReleaseIndex,
    ProjectedRecord,
    ProjectedTerm,
    load_projected_records,
)
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


def test_query_service_exposes_projected_record_detail() -> None:
    detail = demo_service().record_detail("packet-1")

    assert detail is not None
    assert detail["phenopacket_id"] == "packet-1"
    assert detail["source_pmids"] == ["PMID:12345678"]
    assert detail["genes"] == ["PTPN11"]
    assert detail["variant_descriptors"] == ["variant-1"]
    assert detail["phenotypes"][0]["term"] == "HP:0004322"
    assert detail["diseases"][0]["term"] == "OMIM:151100"


def test_query_service_filters_records_by_demo_metadata() -> None:
    service = demo_service()

    cohort_matches = service.record_summaries({"cohort": "PTPN11"})
    gene_matches = service.record_summaries({"gene": "PTPN11"})

    assert [record["phenopacket_id"] for record in cohort_matches] == ["packet-1"]
    assert [record["phenopacket_id"] for record in gene_matches] == ["packet-1"]
    assert [
        record["phenopacket_id"]
        for record in service.record_summaries({"source_pmid": "PMID:12345678"})
    ] == ["packet-1"]
    assert [
        record["phenopacket_id"]
        for record in service.record_summaries({"has_genomic_interpretations": "false"})
    ] == ["packet-2"]


def test_query_service_filters_records_by_terms_and_text() -> None:
    service = demo_service()

    assert [
        record["phenopacket_id"]
        for record in service.record_summaries(
            {"phenotype": "HP:0001250", "phenotype_presence": "excluded"}
        )
    ] == ["packet-2"]
    assert [
        record["phenopacket_id"]
        for record in service.record_summaries({"disease": "OMIM:151100"})
    ] == ["packet-1"]
    text_matches = service.record_summaries({"text": "variant-1"})

    assert [record["phenopacket_id"] for record in text_matches] == ["packet-1"]


def example_service() -> QueryService:
    return QueryService(
        LocalReleaseIndex.build(
            manifest=load_site_manifest(Path("examples/site-manifest.yaml")),
            records=load_projected_records(Path("examples/projected-records.yaml")),
        )
    )


def demo_service() -> QueryService:
    return QueryService(
        LocalReleaseIndex.build(
            manifest=load_site_manifest(Path("examples/site-manifest.yaml")),
            records=(
                ProjectedRecord(
                    phenopacket_id="packet-1",
                    subject_id_redacted=True,
                    phenotypes=(
                        ProjectedTerm("HP:0004322", "Short stature"),
                        ProjectedTerm("HP:0001250", "Seizure"),
                    ),
                    diseases=(ProjectedTerm("OMIM:151100", "LEOPARD syndrome 1"),),
                    medical_actions=(),
                    has_genomic_interpretations=True,
                    source_cohort="PTPN11",
                    source_filename="PMID_12345678_packet.json",
                    source_pmids=("PMID:12345678",),
                    genes=("PTPN11",),
                    variant_descriptors=("variant-1",),
                ),
                ProjectedRecord(
                    phenopacket_id="packet-2",
                    subject_id_redacted=True,
                    phenotypes=(ProjectedTerm("HP:0001250", "Seizure", "excluded"),),
                    diseases=(ProjectedTerm("MONDO:0000002", None),),
                    medical_actions=(),
                    source_cohort="ABCA4",
                    source_filename="PMID_87654321_packet.json",
                    source_pmids=("PMID:87654321",),
                    genes=("ABCA4",),
                ),
            ),
        )
    )
