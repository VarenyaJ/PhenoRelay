from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer
import yaml

from phenorelay import __version__
from phenorelay.backends import BACKEND_CAPABILITIES, filter_backend_capabilities
from phenorelay.clinical_impact import (
    ClinicalImpactError,
    load_clinical_impact_annotations,
    summarize_clinical_impact,
)
from phenorelay.evidence import check_evidence_snippets
from phenorelay.index import (
    IndexError,
    LocalReleaseIndex,
    load_projected_records,
    load_query_request,
)
from phenorelay.manifest import ManifestError, load_site_manifest
from phenorelay.reference_cache import ReferenceCacheError, load_reference_cache

app = typer.Typer(
    name="phenorelay",
    help="Phenopacket-native discovery, evidence, and federation tooling.",
    no_args_is_help=True,
)


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option("--version", help="Show the PhenoRelay version and exit."),
    ] = False,
) -> None:
    if version:
        typer.echo(__version__)
        raise typer.Exit


@app.command()
def inspect(
    phenopacket: Annotated[
        Path,
        typer.Argument(
            exists=True,
            dir_okay=False,
            readable=True,
            help="Phenopacket JSON file to inspect.",
        ),
    ],
    show_subject_id: Annotated[
        bool,
        typer.Option(
            "--show-subject-id",
            help="Include the subject identifier in output. Use only with non-sensitive data.",
        ),
    ] = False,
) -> None:
    """Print minimal identity fields from a Phenopacket JSON file."""
    data = json.loads(phenopacket.read_text(encoding="utf-8"))
    subject_id = (data.get("subject") or {}).get("id") if show_subject_id else None
    typer.echo(
        json.dumps(
            {
                "phenopacket_id": data.get("id"),
                "subject_id": subject_id,
                "subject_id_redacted": not show_subject_id,
                "phenotype_count": len(data.get("phenotypicFeatures") or []),
                "disease_count": len(data.get("diseases") or []),
                "medical_action_count": len(data.get("medicalActions") or []),
            },
            indent=2,
            sort_keys=True,
        )
    )


@app.command()
def backends(
    manifest: Annotated[
        Path | None,
        typer.Option(
            "--manifest",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Site manifest YAML file to inspect instead of the built-in catalog.",
        ),
    ] = None,
    role: Annotated[
        str | None,
        typer.Option("--role", help="Only include backends with this role."),
    ] = None,
    status: Annotated[
        str | None,
        typer.Option("--status", help="Only include backends with this status."),
    ] = None,
    supports: Annotated[
        str | None,
        typer.Option(
            "--supports",
            help="Only include backends where the named supports_* capability is true.",
        ),
    ] = None,
) -> None:
    """Print scaffolded storage backend capability metadata."""
    try:
        capabilities = (
            load_site_manifest(manifest).storage_backends
            if manifest is not None
            else BACKEND_CAPABILITIES
        )
        filtered = filter_backend_capabilities(
            capabilities,
            role=role,
            status=status,
            supports=supports,
        )
    except (ManifestError, ValueError) as exc:
        raise typer.BadParameter(str(exc)) from exc

    typer.echo(
        json.dumps(
            [capability.to_dict() for capability in filtered],
            indent=2,
            sort_keys=True,
        )
    )


@app.command("index-summary")
def index_summary(
    manifest: Annotated[
        Path,
        typer.Option(
            "--manifest",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Site manifest YAML file for the local release.",
        ),
    ],
    records: Annotated[
        Path,
        typer.Option(
            "--records",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Projected record YAML file to index.",
        ),
    ],
) -> None:
    """Print a summary for a local projected-record release index."""
    index = build_local_index(manifest, records)
    typer.echo(json.dumps(index.summary(), indent=2, sort_keys=True))


@app.command("query-local")
def query_local(
    manifest: Annotated[
        Path,
        typer.Option(
            "--manifest",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Site manifest YAML file for the local release.",
        ),
    ],
    records: Annotated[
        Path,
        typer.Option(
            "--records",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Projected record YAML file to query.",
        ),
    ],
    request: Annotated[
        Path,
        typer.Option(
            "--request",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Query request YAML file.",
        ),
    ],
) -> None:
    """Run one query request against a local projected-record release index."""
    try:
        index = build_local_index(manifest, records)
        outcome = index.query(load_query_request(request))
    except (ManifestError, IndexError) as exc:
        raise typer.BadParameter(str(exc)) from exc
    typer.echo(json.dumps(outcome, indent=2, sort_keys=True))


@app.command("validate-evidence")
def validate_evidence(
    outcome: Annotated[
        Path,
        typer.Argument(
            exists=True,
            dir_okay=False,
            readable=True,
            help="Query outcome YAML file containing evidence snippets.",
        ),
    ],
    cache_dir: Annotated[
        Path,
        typer.Option(
            "--cache-dir",
            exists=True,
            file_okay=False,
            readable=True,
            help="Directory of reviewed Markdown reference-cache files.",
        ),
    ],
) -> None:
    """Check that outcome evidence snippets appear in reviewed cache files."""
    data = yaml.safe_load(outcome.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise typer.BadParameter("outcome must contain a YAML mapping")

    try:
        cache = load_reference_cache(cache_dir)
    except ReferenceCacheError as exc:
        raise typer.BadParameter(str(exc)) from exc

    checks = check_evidence_snippets(data, cache)
    typer.echo(json.dumps([check.to_dict() for check in checks], indent=2, sort_keys=True))
    if any(not check.ok for check in checks):
        raise typer.Exit(1)


@app.command("impact-summary")
def impact_summary(
    annotations: Annotated[
        Path,
        typer.Option(
            "--annotations",
            exists=True,
            dir_okay=False,
            readable=True,
            help="Clinical impact annotation YAML file to summarize.",
        ),
    ],
) -> None:
    """Print a summary of clinical impact annotations."""
    try:
        loaded = load_clinical_impact_annotations(annotations)
    except ClinicalImpactError as exc:
        raise typer.BadParameter(str(exc)) from exc

    typer.echo(json.dumps(summarize_clinical_impact(loaded), indent=2, sort_keys=True))


def build_local_index(manifest: Path, records: Path) -> LocalReleaseIndex:
    try:
        return LocalReleaseIndex.build(
            manifest=load_site_manifest(manifest),
            records=load_projected_records(records),
        )
    except (ManifestError, IndexError) as exc:
        raise typer.BadParameter(str(exc)) from exc
