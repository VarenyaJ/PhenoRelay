from __future__ import annotations

import json

import yaml

from phenorelay.demo_projection import build_demo_release, project_phenopacket
from phenorelay.index import load_projected_records


def test_project_phenopacket_extracts_demo_release_fields(tmp_path) -> None:
    path = tmp_path / "PMID_12345678_example.json"
    path.write_text(json.dumps(demo_phenopacket()), encoding="utf-8")

    record = project_phenopacket(path, "PTPN11")

    assert record.phenopacket_id == "example-packet"
    assert record.subject_id_redacted is True
    assert record.source_cohort == "PTPN11"
    assert record.source_filename == "PMID_12345678_example.json"
    assert record.source_pmids == ("PMID:12345678",)
    assert record.phenotypes[0].term == "HP:0004322"
    assert record.phenotypes[0].presence == "present"
    assert record.phenotypes[1].term == "HP:0001250"
    assert record.phenotypes[1].presence == "excluded"
    assert record.diseases[0].term == "OMIM:151100"
    assert record.genes == ("PTPN11",)
    assert record.variant_descriptors == ("variant-1",)
    assert record.has_genomic_interpretations is True


def test_build_demo_release_writes_manifest_and_projected_records(tmp_path) -> None:
    source = tmp_path / "demo" / "source" / "PTPN11"
    source.mkdir(parents=True)
    (source / "PMID_12345678_example.json").write_text(
        json.dumps(demo_phenopacket()), encoding="utf-8"
    )
    records_path = tmp_path / "demo" / "projected-records.yaml"
    manifest_path = tmp_path / "demo" / "site-manifest.yaml"

    summary = build_demo_release(
        demo_dir=tmp_path / "demo",
        records_path=records_path,
        manifest_path=manifest_path,
    )

    assert summary.record_count == 1
    assert summary.cohort_counts == {"PTPN11": 1}
    assert load_projected_records(records_path)[0].genes == ("PTPN11",)

    manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
    assert manifest["site_id"] == "phenorelay-demo"
    assert manifest["record_count"] == 1


def demo_phenopacket() -> dict:
    return {
        "id": "example-packet",
        "subject": {"id": "public subject", "sex": "MALE"},
        "phenotypicFeatures": [
            {"type": {"id": "HP:0004322", "label": "Short stature"}},
            {"type": {"id": "HP:0001250", "label": "Seizure"}, "excluded": True},
        ],
        "diseases": [{"term": {"id": "OMIM:151100", "label": "LEOPARD syndrome 1"}}],
        "interpretations": [
            {
                "diagnosis": {
                    "genomicInterpretations": [
                        {
                            "variantInterpretation": {
                                "variationDescriptor": {
                                    "id": "variant-1",
                                    "geneContext": {
                                        "valueId": "HGNC:9644",
                                        "symbol": "PTPN11",
                                    },
                                }
                            }
                        }
                    ]
                }
            }
        ],
    }
