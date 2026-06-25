"""
export_logduo_docs.py

Last edited: 2026-06-24
"""
from __future__ import annotations

from pathlib import Path
from shutil import copy2
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logduo import Duo

from logduo.internals.engine.runtime_classes import RuntimeRecord


# --- _export_logduo_docs() -----------------------------------------------------
def _export_logduo_docs(
    duo: Duo,
    path: str | Path | None = None,
) -> None:

    runtime = duo._runtime

    assert runtime.project_dir_path_abs is not None

    if path is None:
        logduo_dir_path = (runtime.project_dir_path_abs / "logduo_docs").resolve(strict=False)
    else:
        logduo_dir_path = Path(path).expanduser()

    directory_already_existed = logduo_dir_path.exists()
    logduo_dir_path.mkdir(parents=True, exist_ok=True)

    _write_readme_txt(runtime=runtime, logduo_dir_path=logduo_dir_path)
    _write_example_scripts(logduo_dir_path=logduo_dir_path)

    if directory_already_existed:
        message = "logduo_docs already exists; missing files were added."

    else:
        message = "logduo_docs created."

    print(
        f"{message}\n"
        f"Location:\n{logduo_dir_path}\n"
        "Existing files were preserved; missing files were added.\n"
        "The IDE may need time to refresh before displaying the files.",
        flush=True,
    )


# --- _write_readme_txt() ------------------------------------------------------
def _write_readme_txt(
    *,
    runtime: RuntimeRecord,
    logduo_dir_path: Path,
) -> None:
    assert runtime.log_dir_path_abs is not None

    readme_file_path = logduo_dir_path / "README.txt"
    if readme_file_path.exists():
        return

    try:
        source_readme_path = Path(__file__).parent / "logduo_docs" / "README.txt"
        readme_text = source_readme_path.read_text(encoding="utf-8")

        msg = f"Generated on: {runtime.start_time_display}"

        readme_file_path.write_text(
            msg + "\n\n" + readme_text,
            encoding="utf-8",
        )

    except Exception as e:
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR:\n\n"
            "Failed to write README.txt.\n\n"
        ) from e


# --- _write_example_scripts() -------------------------------------------------
def _write_example_scripts(
    *,
    logduo_dir_path: Path,
) -> None:

    source_examples_dir = (
        Path(__file__).parent
        / "logduo_docs"
        / "example_scripts"
    )

    source_example_script_names = (
        "first_script.py",
        "rich_and_ansi.py",
        "parent.py",
        "parents_child.py",
    )

    target_examples_dir = (logduo_dir_path / "examples")

    target_examples_dir.mkdir(parents=True, exist_ok=True)

    for file_name in source_example_script_names:
        source_file_path = (source_examples_dir / file_name)
        if not source_file_path.exists():
            raise RuntimeError(
                f"LOGDUO INTERNAL ERROR:\n\n"
                f"Missing bundled example script:\n"
                f"{source_file_path}"
            )

        target_file_path = (target_examples_dir / file_name)

        if target_file_path.exists():
            continue

        copy2(source_file_path, target_file_path)

