"""
export_logduo_docs.py

Last edited: 2026-06-24
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from shutil import copy2
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logduo import Duo

from logduo.internals.engine.runtime_classes import RuntimeRecord
from logduo.internals.filesystem.created_file_record_builders import _build_export_doc_created_file_record
from logduo.internals.filesystem.created_file_record_registration import (
    _register_created_file_record,
)


@dataclass(frozen=True)
class DocsExportFileResult:
    name: str
    path: Path
    status: str  # "created" or "preserved"


# --- _export_logduo_docs() ----------------------------------------------------
def _export_logduo_docs(
    duo: Duo,
    path: str | Path | None = None,
) -> None:
    runtime = duo._runtime

    assert runtime.project_dir_path_abs is not None

    if path is None:
        logduo_dir_path = (
            runtime.project_dir_path_abs / "logduo_docs"
        ).resolve(strict=False)
    else:
        logduo_dir_path = Path(path).expanduser().resolve(strict=False)

    logduo_dir_path.mkdir(parents=True, exist_ok=True)

    readme_result = _write_readme_txt(
        duo=duo,
        runtime=runtime,
        logduo_dir_path=logduo_dir_path,
    )

    example_results = _write_example_scripts(
        duo=duo,
        logduo_dir_path=logduo_dir_path,
    )

    message = _build_docs_export_message(
        logduo_dir_path=logduo_dir_path,
        readme_result=readme_result,
        example_results=example_results,
    )

    print(message, flush=True)


# --- _write_readme_txt() ------------------------------------------------------
def _write_readme_txt(
    *,
    duo: Duo,
    runtime: RuntimeRecord,
    logduo_dir_path: Path,
) -> DocsExportFileResult:

    readme_file_path = logduo_dir_path / "README.txt"

    if readme_file_path.exists():
        return DocsExportFileResult(
            name="README.txt",
            path=readme_file_path,
            status="preserved",
        )

    try:
        source_readme_path = (
                Path(__file__).resolve().parent
                / "logduo_docs"
                / "README.txt"
        )
        readme_text = source_readme_path.read_text(encoding="utf-8")

        msg = f"Generated on: {runtime.start_time_display}"

        readme_file_path.write_text(
            msg + "\n\n" + readme_text,
            encoding="utf-8",
        )

        record = _build_export_doc_created_file_record(
            file_path=readme_file_path.resolve(),
        )

        _register_created_file_record(
            duo,
            record,
        )

        return DocsExportFileResult(
            name="README.txt",
            path=readme_file_path,
            status="created",
        )

    except Exception as e:
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR:\n\n"
            "Failed to write README.txt.\n\n"
        ) from e


# --- _write_example_scripts() -------------------------------------------------
def _write_example_scripts(
    *,
    duo: Duo,
    logduo_dir_path: Path,
) -> list[DocsExportFileResult]:
    source_examples_dir = (
        Path(__file__).resolve().parent
        / "logduo_docs"
        / "example_scripts"
    )

    if not source_examples_dir.is_dir():
        raise RuntimeError(
            f"LOGDUO INTERNAL ERROR:\n\n"
            f"Missing bundled example scripts directory:\n"
            f"{source_examples_dir}"
        )

    source_file_paths = sorted(source_examples_dir.glob("*.py"))

    if not source_file_paths:
        raise RuntimeError(
            f"LOGDUO INTERNAL ERROR:\n\n"
            f"No bundled example scripts found in:\n"
            f"{source_examples_dir}"
        )

    target_examples_dir = logduo_dir_path / "examples"
    target_examples_dir.mkdir(parents=True, exist_ok=True)

    results: list[DocsExportFileResult] = []

    for source_file_path in source_file_paths:
        target_file_path = target_examples_dir / source_file_path.name

        if target_file_path.exists():
            results.append(
                DocsExportFileResult(
                    name=source_file_path.name,
                    path=target_file_path,
                    status="preserved",
                )
            )
            continue

        try:
            copy2(source_file_path, target_file_path)
            record = _build_export_doc_created_file_record(
                file_path=target_file_path.resolve(),
            )
            _register_created_file_record(duo, record)
        except Exception as e:
            raise RuntimeError(
                "LOGDUO INTERNAL ERROR:\n\n"
                "Failed to export example script:\n"
                f"{target_file_path}\n"
            ) from e


        results.append(
            DocsExportFileResult(
                name=source_file_path.name,
                path=target_file_path,
                status="created",
            )
        )

    return results


# --- _build_docs_export_message() ---------------------------------------------
def _build_docs_export_message(
    *,
    logduo_dir_path: Path,
    readme_result: DocsExportFileResult,
    example_results: list[DocsExportFileResult],
) -> str:
    created_count = sum(
        result.status == "created"
        for result in [readme_result, *example_results]
    )
    preserved_count = sum(
        result.status == "preserved"
        for result in [readme_result, *example_results]
    )

    example_lines = "\n".join(
        f"    {result.status:9} {result.name}"
        for result in example_results
    )

    return (
        "\n"
        "log.export_logduo_docs() completed.\n"
        f"Docs directory: {logduo_dir_path}\n"
        f"Files created: {created_count}\n"
        f"Existing files preserved (no files overwritten): {preserved_count}\n"
        "File results:\n"
        f"    {readme_result.status:9} {readme_result.name}\n"
        f"{example_lines}\n"
        "The IDE may need time to refresh before displaying the files."
        "\n"
    )
