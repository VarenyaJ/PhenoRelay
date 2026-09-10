from __future__ import annotations

import json

import yaml
from fastapi.testclient import TestClient

from phenorelay.server import create_app


def test_server_exposes_health_and_pheno_info() -> None:
    client = TestClient(create_app(demo=True))

    assert client.get("/api/health").json() == {"status": "ok"}
    info = client.get("/api/pheno/info").json()

    assert info["release"]["site_id"] == "synthetic-site"
    assert info["record_detail_default"] == "disabled"


def test_server_serves_static_browser() -> None:
    client = TestClient(create_app(demo=True))

    response = client.get("/")

    assert response.status_code == 200
    assert "PhenoRelay" in response.text


def test_server_exposes_filtering_terms() -> None:
    client = TestClient(create_app())

    response = client.get("/api/pheno/filtering_terms").json()

    assert response["release"]["release_id"] == "synthetic-release-1"
    assert any(term["term"] == "HP:0001250" for term in response["filtering_terms"])


def test_server_filters_pheno_records_by_query_parameters() -> None:
    client = TestClient(create_app())

    response = client.get("/api/pheno/records", params={"phenotype": "HP:0001250"}).json()

    assert response["record_count"] == 1
    assert response["filters"] == {"phenotype": "HP:0001250"}
    assert response["records"][0]["phenopacket_id"] == "synthetic-packet-1"


def test_server_exposes_projected_record_detail() -> None:
    client = TestClient(create_app())

    response = client.get("/api/pheno/records/synthetic-packet-1").json()

    assert response["record"]["phenopacket_id"] == "synthetic-packet-1"
    assert response["record"]["phenotypes"][0]["term"] == "HP:0001250"
    assert response["record"]["subject_id_redacted"] is True


def test_server_returns_404_for_missing_projected_record() -> None:
    client = TestClient(create_app())

    response = client.get("/api/pheno/records/missing-record")

    assert response.status_code == 404


def test_server_blocks_raw_source_by_default(tmp_path) -> None:
    client = TestClient(demo_raw_source_app(tmp_path, allow_raw=False))

    response = client.get("/api/pheno/records/public-packet/source")

    assert response.status_code == 403


def test_server_exposes_raw_source_only_for_demo_mode(tmp_path) -> None:
    client = TestClient(demo_raw_source_app(tmp_path, allow_raw=True))

    response = client.get("/api/pheno/records/public-packet/source")

    assert response.status_code == 200
    data = response.json()
    assert data["phenopacket_id"] == "public-packet"
    assert data["source"]["id"] == "public-packet"


def test_server_blocks_raw_source_path_escape(tmp_path) -> None:
    client = TestClient(
        demo_raw_source_app(tmp_path, allow_raw=True, source_filename="../../escape.json")
    )

    response = client.get("/api/pheno/records/public-packet/source")

    assert response.status_code == 403


def test_server_runs_pheno_query() -> None:
    client = TestClient(create_app())

    response = client.post(
        "/api/pheno/query",
        json={
            "query_id": "q1",
            "feature": "phenotype",
            "term": "HP:0001250",
            "match_mode": "exact",
            "presence": "present",
            "requested_granularity": "count",
        },
    ).json()

    assert response["release"]["site_id"] == "synthetic-site"
    assert response["outcome"]["count"] == 1


def test_server_exposes_beacon_info_shape() -> None:
    client = TestClient(create_app(demo=True))

    response = client.get("/api/info").json()

    assert response["id"] == "synthetic-site"
    assert response["apiVersion"] == "v2.0"


def test_server_returns_unsupported_for_genomic_variants() -> None:
    client = TestClient(create_app())

    response = client.post("/api/g_variants", json={"query_id": "q1"}).json()

    assert response["phenoRelay"]["status"] == "unsupported"
    assert response["phenoRelay"]["feature"] == "variant"


def demo_raw_source_app(tmp_path, *, allow_raw: bool, source_filename: str = "public-packet.json"):
    records = tmp_path / "records.yaml"
    records.write_text(
        yaml.safe_dump(
            {
                "records": [
                    {
                        "phenopacket_id": "public-packet",
                        "subject_id_redacted": True,
                        "phenotypes": [],
                        "diseases": [],
                        "medical_actions": [],
                        "source_cohort": "PTPN11",
                        "source_filename": source_filename,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    source_dir = tmp_path / "source" / "PTPN11"
    source_dir.mkdir(parents=True)
    (source_dir / "public-packet.json").write_text(
        json.dumps({"id": "public-packet"}), encoding="utf-8"
    )
    return create_app(
        records_path=records,
        demo=True,
        allow_demo_raw_source=allow_raw,
        demo_source_dir=tmp_path / "source",
    )
