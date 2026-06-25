"""
path_validators.py

Path handling helpers used during session_config  resolution.
These are not general purpose path helpers - they are tailored to Logduo.

NOTE:
- Assumes upstream schema normalization/defaulting already completed.

Last edited: 2026-06-08
"""

from pathlib import Path
from typing import Any

from logduo.internals.session_config.session_constants import _LOG_FILE_NAME_RE


# ---_raise_if_invalid_config_arg_log_dir_path() -------------------------------
def _raise_if_invalid_config_arg_log_dir_path(value: str | Path) -> str:
    """
    While this helper functionally can be used to validate any dir_path,
    Its raise messages are specific to the config arg, log_dir_path
    """

    # --- empty string (only applies to str) ---
    if isinstance(value, str) and not value.strip():
        raise ValueError(
            "log_dir_path cannot be an empty string. "
            "Omit the log_dir_path from log.configure() to use Logduo derived default."
        )

    # --- raise if not absolute Path ---
    try:
        p = Path(value)
    except TypeError as e:
        raise ValueError(
            f"log_dir_path must be an absolute path (str or Path); got {type(value).__name__}. "
            "Omit the log_dir_path from log.configure() to use Logduo derived default."
        ) from e

    # --- must be absolute ---
    if not p.is_absolute():
        raise ValueError(
            f"log_dir_path must be an absolute path; got {value!r}. "
            "Omit the log_dir_path from log.configure() to use Logduo derived default."
        )

    # --- must be writable ---
    result = _is_abs_dir_path_writable(str(p), allow_missing_parent=True, with_reasons=True)
    assert isinstance(result, tuple)
    ok, _ = result

    if not ok:
        raise ValueError(
            f"log_dir_path not writable; got {value!r}. "
            "Omit the log_dir_path from log.configure() to use Logduo derived default."
        )

    return str(p.resolve(strict=False))


# --- _raise_if_invalid_config_arg_log_file_path() -----------------------------
def _raise_if_invalid_config_arg_log_file_path(value: str | Path) -> str:
    """
    While this helper functionally can be used to validate any file_path,
    Its raise messages are specific to the config arg, log_file_path
    """

    # --- empty string (only applies to str) ---
    if isinstance(value, str) and not value.strip():
        raise ValueError(
            f"log_file_path cannot be an empty string; got {value!r}. "
            f"Omit the log_file_path from log.configure() to use Logduo derived default."
        )

    try:
        p = Path(value)
    except (TypeError, ValueError) as e:
        raise ValueError(
            f"log_file_path must be an absolute path (str or Path); "
            f"got {type(value).__name__}. "
            f"Omit the log_file_path from log.configure() "
            f"to use Logduo derived default."
        ) from e

    # --- must be absolute ---
    if not p.is_absolute():
        raise ValueError(
            f"log_file_path must be an absolute path; got {value!r}. "
            f"Omit the log_file_path from log.configure() to use Logduo derived default."
        )

    filename = p.name

    # --- invalid filename segments ---
    if filename in {"", ".", ".."}:
        raise ValueError(
            f"log_file_path invalid filename segment: {value!r}. "
            f"Omit the log_file_path from log.configure() to use Logduo derived default."
        )

    # --- regex validation ---
    if not _LOG_FILE_NAME_RE.match(filename):
        raise ValueError(
            f"Invalid log_file_name: {filename!r}\n\n"
            "log_file_name must be a valid filename and may not contain:\n"
            "  - control characters\n"
            "  - forward slashes (/)\n"
            "  - backslashes (\\)\n"
            "  - '.' or '..'\n\n"
            "Omit log_file_name to use the Logduo default."
        )

    # --- parent directory must be usable ---
    result = _is_abs_dir_path_writable(str(p.parent), allow_missing_parent=True, with_reasons=True)

    assert isinstance(result, tuple)
    ok, _ = result

    if not ok:
        raise ValueError(
            f"log_file_path parent directory unusable: {value!r}. "
            f"Omit the log_file_path from log.configure() to use Logduo derived default."
        )

    return str(p.resolve(strict=False))


# --- _raise_if_invalid_config_arg_log_file_name() -----------------------------
def _raise_if_invalid_config_arg_log_file_name(value: str) -> str:
    """
    While this helper functionally can be used to validate any file_name,
    Its raise messages are specific to the config arg, log_file_name
    """

    raw = value.strip() if isinstance(value, str) else ""
    if not raw:
        raise ValueError(
            "log_file_name cannot be empty. "
            "Omit the log_file_name from log.configure() to use Logduo derived default."
        )

    p = Path(raw)
    if p.name != raw:
        raise ValueError(
            "log_file_name must not contain directory components. "
            "Omit the log_file_name from log.configure() to use Logduo derived default."
        )

    if raw in {".", ".."}:
        raise ValueError(
            f"log_file_name invalid: {raw!r}. "
            f"Omit the log_file_name from log.configure() to use Logduo derived default."
        )

    if not _LOG_FILE_NAME_RE.match(raw):
        raise ValueError(
            f"log_file_name invalid: {raw!r}. "
            f"Omit the log_file_name from log.configure() to use Logduo derived default."
        )

    return raw


# --- _raise_if_invalid_session_config_path_fields()----------------------------
def _raise_if_invalid_session_config_path_fields(
        normalized_session_config: dict[str, Any],
) -> dict[str, Any]:

    # log_file_path
    log_file_path = normalized_session_config.get("log_file_path")
    if log_file_path != "auto":
        log_file_path = _raise_if_invalid_config_arg_log_file_path(str(log_file_path))
        normalized_session_config["log_file_path"] = log_file_path

    # log_file_name
    log_file_name = normalized_session_config["log_file_name"]

    if log_file_name != "auto":
        log_file_name = _raise_if_invalid_config_arg_log_file_name(log_file_name)
        normalized_session_config["log_file_name"] = log_file_name

    # log_dir_path
    log_dir_path = normalized_session_config.get("log_dir_path")
    if log_dir_path != "auto":
        log_dir_path = _raise_if_invalid_config_arg_log_dir_path(str(log_dir_path))
        normalized_session_config["log_dir_path"] = log_dir_path

    return normalized_session_config


# === Internal validators ======================================================

# --- _is_abs_dir_path_writable()  ---------------------------------------------
def _is_abs_dir_path_writable(  # noqa: PLR0911  # many returns
    directory: str | Path,
    *,
    allow_existing: bool = True,
    allow_missing_parent: bool = False,
    with_reasons: bool = False,
) -> bool | tuple[bool, list[dict[str, str]]]:
    """
    Validate that `directory` is an absolute directory path that is *writable*,
    either as an existing directory or as a directory we could create.

    Semantics
    ---------
    - Path must:
        * not start with '~'
        * be absolute

    - If the path EXISTS:
        * It must be a directory.
        * If allow_existing is False -> FAIL.
        * Otherwise, we probe by creating a temp file inside it.

    - If the path does NOT exist:
        * If allow_missing_parent is False:
              parent must exist and be a directory; we probe writability in parent.
        * If allow_missing_parent is True:
              we walk up parents until we find the first existing dir and probe
              writability there.

    Returns
    -------
    - with_reasons=False (default): bool
    - with_reasons=True: (bool, list[{"path": str, "reason": str}])
    """
    import tempfile
    from pathlib import Path

    d = Path(directory)
    failures: list[dict[str, str]] = []

    # 1) Disallow leading '~' (must be pre-expanded)
    if isinstance(directory, str) and directory.startswith("~"):
        failures.append(
            {
                "path": str(directory),
                "reason": "VALIDATION (DIR PATH WRITABLE): Path starts with '~'. "
                "Use an absolute path with no '~'.",
            }
        )
        return (False, failures) if with_reasons else False

    # 2) Must be absolute
    if not d.is_absolute():
        failures.append(
            {"path": str(d), "reason": "VALIDATION (DIR PATH WRITABLE): Path is not absolute."}
        )
        return (False, failures) if with_reasons else False

    # 3) If the exact path exists
    if d.exists():
        if not d.is_dir():
            failures.append(
                {
                    "path": str(d),
                    "reason": "VALIDATION (DIR PATH WRITABLE): Path exists but is not a directory.",
                }
            )
            return (False, failures) if with_reasons else False

        if not allow_existing:
            failures.append(
                {
                    "path": str(d),
                    "reason": "VALIDATION (DIR PATH WRITABLE): Directory exists and allow_existing=False.",
                }
            )
            return (False, failures) if with_reasons else False

        # Probe by creating a temp file inside the directory
        try:
            with tempfile.NamedTemporaryFile(dir=str(d)):
                pass
        except OSError as e:
            failures.append(
                {
                    "path": str(d),
                    "reason": f"VALIDATION (DIR PATH WRITABLE): Directory exists but not writable: {e}",
                }
            )
            return (False, failures) if with_reasons else False

        return (True, failures) if with_reasons else True

    # 4) Path does NOT exist → reason about parents
    parent = d.parent

    if not allow_missing_parent:
        # Require parent to exist and be a directory
        if not parent.exists():
            failures.append(
                {
                    "path": str(d),
                    "reason": "VALIDATION (DIR PATH WRITABLE): Parent directory does not exist.",
                }
            )
            return (False, failures) if with_reasons else False
        if not parent.is_dir():
            failures.append(
                {
                    "path": str(d),
                    "reason": "VALIDATION (DIR PATH WRITABLE): Parent exists but is not a directory.",
                }
            )
            return (False, failures) if with_reasons else False

        # Probe: can we create something under parent?
        try:
            with tempfile.TemporaryDirectory(dir=str(parent)):
                pass
        except OSError as e:
            failures.append(
                {
                    "path": str(d),
                    "reason": f"VALIDATION (DIR PATH WRITABLE): Cannot create in parent directory: {e}",
                }
            )
            return (False, failures) if with_reasons else False

        return (True, failures) if with_reasons else True

    # allow_missing_parent = True
    # Walk upwards until we find a real existing directory to probe
    probe_base: Path | None = None
    for ancestor in d.parents:
        if ancestor.exists():
            if ancestor.is_dir():
                probe_base = ancestor
            else:
                failures.append(
                    {
                        "path": str(d),
                        "reason": "VALIDATION (DIR PATH WRITABLE): "
                        "Found existing ancestor that is not a directory.",
                    }
                )
                return (False, failures) if with_reasons else False
            break

    if probe_base is None:
        failures.append(
            {
                "path": str(d),
                "reason": "VALIDATION (DIR PATH WRITABLE): No existing parent directory found "
                "(cannot probe writability).",
            }
        )
        return (False, failures) if with_reasons else False

    # Probe at the existing ancestor
    try:
        with tempfile.TemporaryDirectory(dir=str(probe_base)):
            pass
    except OSError as e:
        failures.append(
            {
                "path": str(d),
                "reason": f"VALIDATION (DIR PATH WRITABLE): Cannot create under ancestor {probe_base}: {e}",
            }
        )
        return (False, failures) if with_reasons else False

    return (True, failures) if with_reasons else True
