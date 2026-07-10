"""
path_finders.py

Includes:
    _derive_session_log_paths()
    _get_script_path_abs()
    _get_toml_path_abs()

Last edited: 2026-5-27
"""

from __future__ import annotations

import sys
from pathlib import Path

_MODULE_DEBUG = False


def _debug(msg: str) -> None:
    if _MODULE_DEBUG:
        print(f"DEBUG PATH_FINDER: {msg}")


# --- _derive_session_log_paths() ----------------------------------------------
def _derive_session_log_paths(
    *,
    project_dir_path_abs: Path,
    session_name: str,
    log_file_layout: str,
    log_file_mode: str,
    session_timestamp: str,
    log_file_path: str,  # "auto" | absolute path
    log_dir_path: str,  # "auto" | absolute path
    log_file_name: str,  # "auto" | filename
) -> dict[str, Path | None]:
    """
    All user config args for paths already validated (raised if invalid)
    project_dir_path_abs is guaranteed not to be None by time this function is called

    Possible values:
        log_file_path = "auto" | absolute path
        log_dir_path  = "auto" | absolute path
        log_file_name = "auto" | filename

    Returns canonical internal truth:
        log_dir_path_abs  (base log directory - (parent of pyproject.toml)/logs or cwd/logs)
        main_sink_log_dir_path_abs (full path to dir where main log file would be stored if created)
        main_sink_log_file_path_abs (full path to where main log file would be stored if created)
    """

    # --- Case 1: explicit log_file_path provided by user ---
    if " " in session_timestamp or ":" in session_timestamp:
        raise ValueError(
            "LOGDUO INTERNAL ERROR: Invalid session_timestamp format (must be path-safe). "
        )

    # Note: priority given to direct specification of log_file_path (even if log_dir_path also given)
    # log_dir_path is set to parent of log_file_path
    if log_file_path != "auto":
        log_file_path_abs = Path(log_file_path).resolve()
        log_dir_path_abs = log_file_path_abs.parent
        log_file_path_abs = log_file_path_abs.with_suffix(log_file_path_abs.suffix or ".log")

        if log_file_mode == "timestamped":
            log_file_path_abs = log_file_path_abs.with_name(
                f"{log_file_path_abs.stem}_{session_timestamp}{log_file_path_abs.suffix}"
            )

        main_sink_log_file_path_abs = log_file_path_abs

        return {
            "log_dir_path_abs": log_dir_path_abs,
            "main_sink_log_dir_path_abs": log_dir_path_abs,
            "main_sink_log_file_path_abs": main_sink_log_file_path_abs,
        }

    # --- Determine root logs directory ---
    if log_dir_path != "auto":
        log_dir_path_abs = Path(log_dir_path).resolve()
    else:
        log_dir_path_abs = project_dir_path_abs / "logs"

    # --- Determine session log directory ---
    if log_file_layout in {"script", "run"}:
        session_name_log_dir_path_abs = (log_dir_path_abs / session_name).resolve()
    else:
        session_name_log_dir_path_abs = log_dir_path_abs

    # --- Determine run directory ---
    if log_file_layout == "run":
        run_log_dir_path_abs = (
            session_name_log_dir_path_abs / f"run_{session_timestamp}"
        ).resolve()
        main_sink_log_dir_path_abs = run_log_dir_path_abs
    else:
        main_sink_log_dir_path_abs = session_name_log_dir_path_abs

    # --- Determine log file name ---
    if log_file_name == "auto":
        log_file_name_stem = session_name
        log_file_name_suffix = ".log"
    else:
        log_file_name_path = Path(log_file_name)
        log_file_name_stem = log_file_name_path.stem
        log_file_name_suffix = log_file_name_path.suffix or ".log"  # only add .log if missing

    effective_log_file_name = f"{log_file_name_stem}{log_file_name_suffix}"

    if log_file_mode == "timestamped":
        effective_log_file_name = _apply_timestamp_to_filename(
            filename=effective_log_file_name, session_timestamp=session_timestamp
        )

    # --- Construct main log file path -------------------------------------
    main_sink_log_file_path_abs = (main_sink_log_dir_path_abs / effective_log_file_name).resolve()

    # --- Return canonical paths ----------------------------------------------
    return {
        "log_dir_path_abs": log_dir_path_abs,
        "main_sink_log_dir_path_abs": main_sink_log_dir_path_abs,
        "main_sink_log_file_path_abs": main_sink_log_file_path_abs,
    }


# --- _get_script_path_abs() ---------------------------------------------------
def _get_script_path_abs(
    # *,
    # exclude_path_prefixes: tuple[str, ...] | None = None,
) -> tuple[Path | None, str | None]:
    """
    Determine the best available script path and report which
    script_path_source won.

    Returns
    -------
    tuple[Path | None, str]
        (script_path_abs, script_path_source)

        script_path_source is one of:
            "main_file"
            None
    """

    # --- Use __main__.__file__ (main) to identify calling script ---
    main_mod = sys.modules.get("__main__")
    main_file_path = getattr(main_mod, "__file__", None)

    candidate = _normalize_path_candidate(main_file_path)
    if candidate is not None:
        _debug(f"[script detection] via __main__.__file__ → {candidate}")
        return candidate, "main_file"

    return None, None


# --- _get_toml_path_abs() ----------------------------------------------------
def _get_toml_path_abs(*, cwd_path_abs: Path | None) -> tuple[Path | None, str | None]:

    if cwd_path_abs is None:
        return None, None

    current_dir = cwd_path_abs.resolve(strict=False)

    while True:
        candidate_toml_path_abs = current_dir / "pyproject.toml"

        # --- found pyproject.toml ---
        if candidate_toml_path_abs.is_file():
            try:
                with candidate_toml_path_abs.open("r", encoding="utf-8"):
                    pass

            except Exception:  # noqa
                warn_msg = (
                    f"Discovered pyproject.toml is not readable:\n  {candidate_toml_path_abs}"
                )
                return None, warn_msg

            return candidate_toml_path_abs.resolve(strict=False), None

        # --- reached filesystem root ---
        if current_dir.parent == current_dir:
            return None, None

        # --- continue upward walk ---
        current_dir = current_dir.parent


# === Internal helpers =========================================================


# --- _normalize_path_candidate() ----------------------------------------------
def _normalize_path_candidate(  # noqa: PLR0911  # many returns
        raw_path: str | Path | None
) -> Path | None:
    """
    Return a usable Python script path, else None.

    Rules:
      - must resolve to a real file
      - must end with .py
      - reject obvious environment/package/internal paths
    """
    if raw_path is None:
        return None

    try:
        p = Path(raw_path).expanduser().resolve(strict=False)
    except (OSError, RuntimeError, ValueError, TypeError):
        return None

    p_str = str(p).lower().replace("\\", "/")
    if not p.is_file():
        return None
    if p.suffix.lower() != ".py":
        return None

    # Reject environment/package-managed paths.
    # Goal: identify user script origins, not interpreter/library internals.
    bad_markers = ("/site-packages/", "/dist-packages/", "/.venv/", "/venv/", "/virtualenvs/")

    if any(marker in p_str for marker in bad_markers):
        return None
    if p.name == "__main__.py":
        return None
    return p


# --- _apply_timestamp_to_filename() -------------------------------------------
def _apply_timestamp_to_filename(*, filename: str, session_timestamp: str) -> str:
    """Insert timestamp before filename extension."""
    p = Path(filename)
    stem = p.stem
    suffix = p.suffix
    return f"{stem}_{session_timestamp}{suffix}"
