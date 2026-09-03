from __future__ import annotations

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
