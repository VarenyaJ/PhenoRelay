from __future__ import annotations

import json

import yaml

from phenorelay.demo_data import fetch_demo_phenopackets


def test_fetch_demo_phenopackets_copies_exact_source_files_and_manifest(tmp_path) -> None:
    source = tmp_path / "phenopacket-store"
    cohort_dir = source / "notebooks" / "PTPN11" / "phenopackets"
    cohort_dir.mkdir(parents=True)
    (source / "LICENSE").write_text("CC0-1.0\n", encoding="utf-8")
    (source / ".git").mkdir()
    (source / ".git" / "HEAD").write_text("abc123\n", encoding="utf-8")
    record = cohort_dir / "example.json"
    record.write_text(json.dumps({"id": "example"}), encoding="utf-8")
    out_dir = tmp_path / "demo"

    summary = fetch_demo_phenopackets(source=source, out_dir=out_dir, cohorts=("PTPN11",))

    copied = out_dir / "source" / "PTPN11" / "example.json"
    assert copied.read_text(encoding="utf-8") == record.read_text(encoding="utf-8")
    assert summary.cohort_counts == {"PTPN11": 1}

    manifest = yaml.safe_load((out_dir / "source-manifest.yaml").read_text(encoding="utf-8"))
    assert manifest["source_commit"] == "abc123"
    assert manifest["source_license"] == "CC0-1.0"
    assert manifest["files"][0]["source_path"] == "notebooks/PTPN11/phenopackets/example.json"
