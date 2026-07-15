"""
example_scripts_runner.py

Run installed Logduo example scripts and log results.

Skips:
    nested_child_script.py

Reason:
    nested_child_script.py is intended to be run by nested_parent_script.py.
    It calls log.join() and expects an active parent session.

Runs automatically in macOS, Ubuntu and Windows when changes pushed to GitHub.
    called by:  .github/workflows/tests.yml

Last edited: 2026-07-08
"""

from __future__ import annotations

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from logduo import log

PROJECT_ROOT = Path(__file__).resolve().parents[2]
EXAMPLES_DIR = PROJECT_ROOT / "src" / "logduo" / "internals" / "artifacts" / "logduo_docs" / "example_scripts"

SKIP_EXAMPLES = {
    "__init__.py",
    "nested_child_script.py",
}

EXPECTED_EXPORTED_FILES = {
    "README.txt",
    "examples/first_script.py",
    "examples/console_rendering.py",
    "examples/data_analysis.py",
    "examples/math_report_notation.py",
    "examples/nested_parent_script.py",
    "examples/nested_child_script.py",
}


@dataclass(frozen=True)
class ExampleResult:
    name: str
    path: Path
    returncode: int
    stdout: str
    stderr: str


def _section(title: str) -> None:
    log("")
    log("=" * 87)
    log(title)
    log("=" * 87)


def _find_example_scripts() -> list[Path]:
    if not EXAMPLES_DIR.exists():
        raise FileNotFoundError(f"Examples directory not found: {EXAMPLES_DIR}")

    example_scripts = []

    for path in sorted(EXAMPLES_DIR.glob("*.py")):
        if path.name in SKIP_EXAMPLES:
            continue

        if path.name.startswith("_"):
            continue

        example_scripts.append(path)

    return example_scripts


def _run_example(path: Path) -> ExampleResult:
    _section(f"Example script: {path.name}")

    command = [sys.executable, str(path)]

    log("Command:")
    log(" ".join(command))

    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except Exception as exc:
        log.exception(f"{path.name} crashed before completion.")
        return ExampleResult(
            name=path.name,
            path=path,
            returncode=1,
            stdout="",
            stderr=repr(exc),
        )

    if completed.stdout.strip():
        log("STDOUT")
        log(completed.stdout)

    if completed.stderr.strip():
        log("STDERR")
        log(completed.stderr)

    if completed.returncode == 0:
        log.success(f"{path.name} passed.")
    else:
        log.error(f"{path.name} failed with return code {completed.returncode}.")

    return ExampleResult(
        name=path.name,
        path=path,
        returncode=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def run_example_scripts() -> list[ExampleResult]:
    """Run all standalone example scripts."""
    example_scripts = _find_example_scripts()

    _section("Example script discovery")
    log(f"Examples directory: {EXAMPLES_DIR}")
    log(f"Skipped examples: {sorted(SKIP_EXAMPLES)}")
    log(f"Runnable examples found: {len(example_scripts)}")

    for path in example_scripts:
        log(f"- {path.name}")

    return [_run_example(path) for path in example_scripts]


def failed_examples(results: list[ExampleResult]) -> list[ExampleResult]:
    """Return examples that failed or crashed."""
    return [result for result in results if result.returncode != 0]


def validate_logduo_docs_export() -> None:
    """
    Validate log.export_logduo_docs().
    Uses an explicit export directory inside the current validation run output
    so the test is safe on local machines and GitHub runners.
    """

    _section("Documentation export validation")
    docs_dir = log.output_dir_path / "logduo_docs_export_demo"
    log("Export directory:")
    log(str(docs_dir))
    log("First export:")
    log.export_logduo_docs(docs_dir)
    log("Second export:")
    log.export_logduo_docs(docs_dir)
    missing_files: list[str] = []

    for relative_file_path in sorted(EXPECTED_EXPORTED_FILES):
        file_path = docs_dir / relative_file_path
        if file_path.exists():
            log.success(f"Found exported file: {relative_file_path}")
        else:
            log.error(f"Missing exported file: {relative_file_path}")
            missing_files.append(relative_file_path)
    if missing_files:
        raise RuntimeError(
            "Documentation export validation failed. "
            f"Missing files: {missing_files}"
        )
    log.success("Documentation export validation passed.")


def main() -> None:
    log.configure(
        log_dir_path=PROJECT_ROOT / "developer_resources" / "logduo_validation" / "logs",
        console_verbosity=3,
        log_verbosity=3,
    )

    results = run_example_scripts()
    failures = failed_examples(results)

    validate_logduo_docs_export()

    _section("Example script summary")

    if not failures:
        log.success("All standalone example scripts passed.")
        log.close()
        return

    log.error("Some example scripts failed:")
    for failure in failures:
        log.error(f"- {failure.name}: return code {failure.returncode}")

    log.close()
    raise SystemExit(1)


if __name__ == "__main__":
    main()
