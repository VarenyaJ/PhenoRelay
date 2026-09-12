from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from phenorelay.server import create_app

FIXTURE_DIR = Path("tests/fixtures/beacon")


def test_beacon_info_matches_golden_fixture() -> None:
    client = TestClient(create_app(demo=True))

    assert client.get("/api/info").json() == load_fixture("api-info.json")


def test_beacon_service_info_matches_golden_fixture() -> None:
    client = TestClient(create_app(demo=True))

    assert client.get("/api/service-info").json() == load_fixture("api-service-info.json")


def test_beacon_filtering_terms_match_golden_fixture() -> None:
    client = TestClient(create_app(demo=True))

    assert client.get("/api/filtering_terms").json() == load_fixture("api-filtering-terms.json")


def test_beacon_individuals_match_golden_fixture() -> None:
    client = TestClient(create_app(demo=True))
    request = {
        "query_id": "q1",
        "feature": "phenotype",
        "term": "HP:0001250",
        "match_mode": "exact",
        "presence": "present",
        "requested_granularity": "count",
    }

    assert client.post("/api/individuals", json=request).json() == load_fixture(
        "api-individuals-count.json"
    )


def load_fixture(name: str) -> dict[str, Any]:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))
