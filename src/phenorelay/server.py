from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from phenorelay.index import LocalReleaseIndex, load_projected_records
from phenorelay.manifest import load_site_manifest
from phenorelay.query_service import QueryService


def create_app(
    *,
    manifest_path: Path = Path("examples/site-manifest.yaml"),
    records_path: Path = Path("examples/projected-records.yaml"),
    demo: bool = False,
) -> FastAPI:
    service = QueryService(
        LocalReleaseIndex.build(
            manifest=load_site_manifest(manifest_path),
            records=load_projected_records(records_path),
        )
    )
    app = FastAPI(title="PhenoRelay", version="0.1.0")
    app.state.query_service = service
    app.state.demo = demo

    static_dir = browser_static_path()
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    def browser() -> FileResponse:
        return FileResponse(static_dir / "index.html")

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/api/info")
    def beacon_info() -> dict[str, Any]:
        release = service.release_metadata()
        return {
            "id": release["site_id"],
            "name": "PhenoRelay Beacon adapter",
            "apiVersion": "v2.0",
            "environment": "demo" if demo else "local",
            "organization": {"name": "PhenoRelay"},
            "description": "Beacon-compatible adapter over a PhenoRelay release index.",
            "version": str(release["release_id"]),
        }

    @app.get("/api/service-info")
    def service_info() -> dict[str, Any]:
        release = service.release_metadata()
        return {
            "id": release["site_id"],
            "name": "PhenoRelay",
            "type": {
                "group": "org.ga4gh",
                "artifact": "beacon",
                "version": "v2.0",
            },
            "description": "Phenopacket-native discovery service with Beacon-compatible routes.",
            "organization": {"name": "PhenoRelay"},
            "version": str(release["release_id"]),
        }

    @app.get("/api/filtering_terms")
    def beacon_filtering_terms() -> dict[str, Any]:
        return {"response": {"filteringTerms": service.filtering_terms()}}

    @app.post("/api/individuals")
    def beacon_individuals(request: dict[str, Any]) -> dict[str, Any]:
        outcome = service.query(request)["outcome"]
        return {
            "meta": {
                "requestedGranularity": request.get("requested_granularity", "count"),
                "receivedRequestSummary": request,
            },
            "responseSummary": {
                "exists": outcome.get("exists", False),
                "numTotalResults": outcome.get("count", 0),
            },
            "response": {"resultSets": []},
            "phenoRelay": outcome,
        }

    @app.post("/api/g_variants")
    def beacon_genomic_variants(request: dict[str, Any]) -> dict[str, Any]:
        return {
            "meta": {
                "requestedGranularity": request.get("requested_granularity", "count"),
                "receivedRequestSummary": request,
            },
            "responseSummary": {"exists": False, "numTotalResults": 0},
            "response": {"resultSets": []},
            "phenoRelay": {
                "query_id": request.get("query_id", "g-variants"),
                "status": "unsupported",
                "feature": "variant",
            },
        }

    @app.get("/api/pheno/info")
    def pheno_info() -> dict[str, Any]:
        return service.pheno_info()

    @app.get("/api/pheno/releases/current")
    def pheno_current_release() -> dict[str, Any]:
        return service.release_metadata()

    @app.get("/api/pheno/filtering_terms")
    def pheno_filtering_terms() -> dict[str, Any]:
        return {"release": service.release_metadata(), "filtering_terms": service.filtering_terms()}

    @app.post("/api/pheno/query")
    def pheno_query(request: dict[str, Any]) -> dict[str, Any]:
        return service.query(request)

    @app.get("/api/pheno/records")
    def pheno_records() -> dict[str, Any]:
        return {"release": service.release_metadata(), "records": service.record_summaries()}

    return app


def browser_static_path() -> Path:
    return Path(str(files("phenorelay") / "browser_static"))
