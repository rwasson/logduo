"""
api_arg_resolver_helpers.py

Resolver helpers for:
- new_logger()
- new_loguru_sink()
- level_entry()

Includes:
- per-arg validation/normalization
- sink-path resolution
- internal sentinel checks

Imported across Logduo internal API layers.

Last edited: 2026-5-27
"""
from __future__ import annotations

from pathlib import Path
from re import Pattern
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from logduo import Duo

from rich.style import Style

from logduo.internals.engine.runtime_classes import CreatedFileRecord
from logduo.internals.engine.runtime_warning import _runtime_warning
from logduo.internals.session_config.session_config_classes import SessionConfig
from logduo.internals.session_config.session_config_resolver import _resolve_header_footer_value
from logduo.internals.session_config.cerberus_utils import _norm_log_file_mode
from logduo.internals.session_config.session_constants import (
    _DEFAULT_LOG_VERBOSITY,
    _NOT_GIVEN,
    _NotGiven,
    _RESERVED_SINK_STEMS,
    _VALID_LOG_FILE_MODES,
    _VALID_PREFIX,
    _VALID_SINK_STEM_NAME_RE,
    _VALID_VERBOSITY_LEVELS, _MIN_WRAP_WIDTH,
)


class SinkInfo(TypedDict):
    value_is_path: bool
    file_path: Path
    base_file_name_with_ext: str


# --- _resolve_int_arg() -------------------------------------------------------
def _resolve_int_arg(
    *,
    arg_name: str,
    value: int | None | _NotGiven,
    min_value: int | None = None,
    max_value: int | None = None,
    allowed_values: list[int] | None = None,
) -> int:

    if type(value) is not int:
        raise ValueError(f"{arg_name} must be an integer (not {value!r})")

    if min_value is not None and max_value is not None and min_value > max_value:
        raise RuntimeError(f"{arg_name}: min_value > max_value")

    if min_value is not None and value < min_value:
        raise ValueError(f"{arg_name} must be >= {min_value} (not {value!r})")

    if max_value is not None and value > max_value:
        raise ValueError(f"{arg_name} must be <= {max_value} (not {value!r})")

    if allowed_values is not None and value not in allowed_values:
        raise ValueError(f"{arg_name} must be one of: {allowed_values} (not {value!r})")

    return value


# --- _resolve_bool_arg() ------------------------------------------------------
def _resolve_bool_arg(
    *,
    arg_name: str,
    value: bool | None | _NotGiven,
    default: bool = False,
) -> bool:

    resolved_value = _precheck_auto_and_none(arg_name=arg_name, value=value, default=default)
    if not isinstance(resolved_value, bool):
        raise ValueError(f"{arg_name} must be True or False (not {resolved_value!r})")
    assert isinstance(resolved_value, bool)
    return resolved_value


# --- _resolve_to_main_sink_log() ----------------------------------------------
def _resolve_to_main_sink_log(
        *,
        duo: Duo,
        to_main_log: bool | None | _NotGiven,
        default: bool = False,
) -> bool:
    resolved_to_main_log = _precheck_auto_and_none(
        arg_name="to_main_log",
        value=to_main_log,
        default=default,
    )
    if not isinstance(resolved_to_main_log, bool):
        raise ValueError(f"Invalid to_main_log={to_main_log!r}. Must be True or False")
    if resolved_to_main_log and duo.session_config.log_verbosity <= 0:
        _runtime_warning(
            duo, warn_msg="to_main_log=True but main log is disabled; using to_main_log=False "
        )
        return False

    return resolved_to_main_log


# --- _resolve_log_verbosity() -------------------------------------------------
def _resolve_log_verbosity(
        *,
        duo: Duo,
        log_verbosity: int | None | _NotGiven,
) -> int:

    default_log_verbosity: int = duo.session_config.log_verbosity

    #  new_logger falls back to global default for log_verbosity
    # if session_config sets log_verbosity to 0
    if log_verbosity is _NOT_GIVEN and default_log_verbosity == 0:
        default_log_verbosity = _DEFAULT_LOG_VERBOSITY

    resolved_log_verbosity = _precheck_auto_and_none(
        arg_name="log_verbosity",
        value=log_verbosity,
        default=default_log_verbosity,
    )

    if not isinstance(resolved_log_verbosity, int):
        raise ValueError(
            f"Invalid log_verbosity={resolved_log_verbosity!r}. "
            f"Must be one of: {_VALID_VERBOSITY_LEVELS}"
        )
    if resolved_log_verbosity not in _VALID_VERBOSITY_LEVELS:
        raise ValueError(
            f"Invalid log_verbosity={resolved_log_verbosity!r}. "
            f"Must be one of: {_VALID_VERBOSITY_LEVELS}"
        )

    return resolved_log_verbosity


# --- _resolve_log_file_mode() -------------------------------------------------
def _resolve_log_file_mode(
        *,
        duo: Duo,
        log_file_mode: str | None | _NotGiven,
) -> str:
    err_msg = f"Invalid log_file_mode={log_file_mode!r}. Must be one of: {_VALID_LOG_FILE_MODES}"
    resolved_log_file_mode = _precheck_auto_and_none(
        arg_name="log_file_mode",
        value=log_file_mode,
        default=duo.session_config.log_file_mode,
    )

    raw = resolved_log_file_mode
    if not isinstance(raw, str):
        raise ValueError(err_msg)

    v = raw.strip().lower()
    v = _norm_log_file_mode(v)  # normalize "a" -> "append",...

    if not isinstance(v, str):
        raise ValueError(err_msg)

    if v not in _VALID_LOG_FILE_MODES:
        raise ValueError(err_msg)

    return v


# --- _resolve_log_prefix() ----------------------------------------------------
def _resolve_log_prefix(
        *,
        duo: Duo,
        log_prefix: str | None | _NotGiven,
) -> str:
    resolved_log_prefix = _precheck_auto_and_none(
        arg_name="log_prefix",
        value=log_prefix,
        default=duo.session_config.log_prefix
    )

    if not isinstance(resolved_log_prefix, str):
        raise ValueError(f"Invalid log_prefix={resolved_log_prefix!r}. Allowed: {sorted(_VALID_PREFIX)}")

    v = resolved_log_prefix.strip().lower()

    if v not in _VALID_PREFIX:
        raise ValueError(f"Invalid log_prefix={resolved_log_prefix!r}. Allowed: {sorted(_VALID_PREFIX)}")

    return v


# --- _resolve_log_header() ----------------------------------------------------
def _resolve_log_header(
        *,
        log_header: str | None | _NotGiven,
) -> str:
    """Internally returns 'auto' or user's custom string"""
    if log_header is None:
        raise ValueError("log_header cannot be None; use 'off' to disable")
    resolved_log_header = _precheck_auto_and_none(
        arg_name="log_header",
        value=log_header,
        default="auto")
    return _resolve_header_footer_value(arg_name="log_header", value=resolved_log_header)


# --- _resolve_log_footer() ----------------------------------------------------
def _resolve_log_footer(
        *,
        log_footer: str | None | _NotGiven,
) -> str:
    """Internally returns 'auto' or user's custom string"""
    if log_footer is None:
        raise ValueError("log_footer cannot be None; use 'off' to disable")
    resolved_log_footer = _precheck_auto_and_none(
        arg_name="log_footer",
        value=log_footer,
        default="auto",
    )
    return _resolve_header_footer_value(arg_name="log_footer", value=resolved_log_footer)


# --- _resolve_log_wrap_width() ------------------------------------------------
def _resolve_log_wrap_width(
        *,
        duo: Duo,
        log_wrap_width: int | str | None | _NotGiven,
) -> int | str:
    """Resolve log_wrap_width for calls and sink configs."""
    resolved_log_wrap_width = _precheck_auto_and_none(
        arg_name="log_wrap_width",
        value=log_wrap_width,
        default=duo.session_config.log_wrap_width,
    )

    if isinstance(resolved_log_wrap_width, int):
        if resolved_log_wrap_width < _MIN_WRAP_WIDTH:
            warn_msg = f"log_wrap_width too small ({resolved_log_wrap_width} < {_MIN_WRAP_WIDTH}); using: 'off'"
            _runtime_warning(duo, warn_msg=warn_msg)
            return "off"
        return resolved_log_wrap_width
    elif isinstance(resolved_log_wrap_width, str):
        v = resolved_log_wrap_width.strip().lower()
        if v == "off":
            return "off"

    raise ValueError(f"Invalid log_wrap_width = {resolved_log_wrap_width!r}; use int or 'off' to disable")


# --- _resolve_new_logger_target_arg() -----------------------------------------------------
def _resolve_new_logger_target_arg(
        *,
        duo: Duo,
        value: str | Path,
) -> SinkInfo:
    if not isinstance(value, (str, Path)):  # excludes None or _NOT_GIVEN
        raise ValueError("new_logger() target must be a string or Path")

    if isinstance(value, str):
        value = value.strip()
        if value.lower() == "auto":
            raise ValueError(
                "new_logger() target cannot be 'auto'; 'auto' is reserved for internal use"
            )
        if not value:
            raise ValueError("new_logger() target cannot be empty")

    p = Path(value)
    value_is_path = isinstance(value, Path) or p.is_absolute()

    if value_is_path:
        if not p.is_absolute():
            raise ValueError("new_logger() target path must be absolute")
        if p.exists() and p.is_dir():
            raise ValueError("new_logger() target path must be a file path, not a directory")
        if not p.name:
            raise ValueError("new_logger() target path must include a filename")
        filename = p.name

        normalized_filename = f"{p.stem.lower()}{p.suffix}"

        _validate_filename_full(
            filename=normalized_filename,
            stem_regex=_VALID_SINK_STEM_NAME_RE,  # check again lower_cased file stem
            reserved_stems=_RESERVED_SINK_STEMS,
        )

        final_path = p.resolve(strict=False)  # save original case file stem

        return {"value_is_path": True, "file_path": final_path, "base_file_name_with_ext": filename}

    # --- Name-only sink case ---
    raw = str(value).strip()

    # --- block path-like input ---
    if "/" in raw or "\\" in raw:
        raise ValueError("new_logger() target file name must not contain path separators")

    if raw in {".", ".."}:
        raise ValueError("new_logger() target file name cannot be '.' or '..'")

    p = Path(raw)
    stem = p.stem.lower()
    suffix = p.suffix.lower()

    if not stem:
        raise ValueError(
            "Invalid new_logger() target name. Must include a valid stem "
            "(letters, numbers, underscores)"
        )

    if not suffix:
        suffix = ".log"

    filename = f"{stem}{suffix}"

    _validate_filename_full(
        filename=filename, stem_regex=_VALID_SINK_STEM_NAME_RE, reserved_stems=_RESERVED_SINK_STEMS
    )

    # --- derive default path ---
    base_dir = duo._runtime.main_sink_log_dir_path_abs
    if base_dir is None:
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR: main_sink_log_dir_path_abs is not set on runtime"
        )

    final_path = (Path(base_dir) / filename).resolve(strict=False)

    return {"value_is_path": False, "file_path": final_path, "base_file_name_with_ext": filename}


# --- _resolve_call_no_prefix() ------------------------------------------------
def _resolve_call_no_prefix(
        *,
        is_console_sink: bool,
        sink_config: SessionConfig | CreatedFileRecord,
        no_prefix: bool | _NotGiven,
) -> bool:
    """call arg only, but can be built from sink_config's log_prefix"""

    if no_prefix is None:
        raise ValueError("no_prefix cannot be None; use True/False or omit")

    if is_console_sink:
        assert isinstance(sink_config, SessionConfig)
        if sink_config.console_prefix == "off":
            no_prefix_config = True
        else:
            no_prefix_config = False
    elif sink_config.log_prefix == "off":
        no_prefix_config = True
    else:
        no_prefix_config = False

    if no_prefix is _NOT_GIVEN:
        return no_prefix_config

    elif not isinstance(no_prefix, bool):
        raise ValueError("no_prefix must be True or False")

    return no_prefix


# --- _resolve_call_log_wrap_width() -------------------------------------------
def _resolve_call_log_wrap_width(
        *,
        duo: Duo ,
        sink_config: SessionConfig | CreatedFileRecord,
        log_wrap_width: int | str | _NotGiven,
) -> int | str:
    # call arg and sink_config arg
    # only applies to file sinks, console_emitter will ignore
    err_msg = (
        f"Invalid log_wrap_width = {log_wrap_width}; cannot be None, use 'off', an "
        f"integer > 19, or exclude from arg list to use default"
    )
    if log_wrap_width is None:
        raise ValueError(err_msg)
    resolved_log_wrap_width = _precheck_auto_and_none(
        arg_name="log_wrap_width",
        value=log_wrap_width,
        default=sink_config.log_wrap_width,
    )

    if isinstance(resolved_log_wrap_width, int):
        if resolved_log_wrap_width < _MIN_WRAP_WIDTH:
            warn_msg = f"log_wrap_width too small ({log_wrap_width} < {_MIN_WRAP_WIDTH}); using: 'off'"
            _runtime_warning(duo, warn_msg=warn_msg)
            return "off"
        return resolved_log_wrap_width

    elif isinstance(resolved_log_wrap_width, str):
        v = resolved_log_wrap_width.strip().lower()
        if v == "off":
            return "off"

    raise ValueError(err_msg)


# --- _resolve_call_console_style() --------------------------------------------
def _resolve_call_console_style(
        *,
        theme_dict: dict[str, str],
        console_style: str | _NotGiven,
) -> str | None:
    """
    Validate and normalize console_style.

    Accepted values:
        - Logduo theme keys from console_theme_dict
          (e.g. "warning", "muted", "title")
        - Valid Rich style strings
          (e.g. "italic blue", "bold gold3")

    Theme keys are valid because the Rich Console is initialized with:
        Console(theme=Theme(console_theme_dict))

    allowing Rich to resolve theme names at render time.
    """

    if console_style is None:
        raise ValueError(
            "console_style cannot be None; exclude from arg list if not applying Rich formatting"
        )

    resolved_console_style = _precheck_auto_and_none(
        arg_name="console_style",
        value=console_style,
        default=None,
    )

    if resolved_console_style is not None and not isinstance(resolved_console_style, str):
        raise ValueError(
            "console_style must be string for Rich formatting (e.g., console_style='italic blue')"
        )

    if resolved_console_style is None:
        return None

    theme_key = resolved_console_style.lower()

    if theme_key in theme_dict:
        return theme_key

    try:
        Style.parse(resolved_console_style)
    except Exception as e:
        raise ValueError(f"Invalid console_style: {resolved_console_style!r}") from e

    return resolved_console_style


# --- _validate_filename_full() ------------------------------------------------
def _validate_filename_full(
        *,
        filename: str,
        stem_regex: Pattern[str],
        reserved_stems: set[str],
) -> None:

    if not isinstance(filename, str):
        raise ValueError("File name must be a string")

    filename = filename.strip()
    if not filename:
        raise ValueError("File name cannot be empty")

    if filename.lower() == "auto":
        raise ValueError("File name cannot be 'auto'; this value is reserved for internal use")

    if filename in {".", ".."}:
        raise ValueError("File name cannot be '.' or '..'")
    if filename.count(".") != 1:
        raise ValueError(f"Invalid file name '{filename}'. Must contain exactly one '.'")

    p = Path(filename)
    if not p.suffix:
        raise ValueError("File name must include an extension")

    stem = p.stem
    if not stem:
        raise ValueError("File name must include a valid stem")
    if "." in stem:
        raise ValueError("Stem must not include '.'")
    if not stem_regex.match(stem):
        raise ValueError(
            "Stem must use lowercase letters (a–z), digits (0–9), underscores (_), 1–32 characters"
        )

    if stem in reserved_stems:
        reserved = ", ".join(sorted(reserved_stems))
        raise ValueError(f'Stem "{stem}" is reserved. Reserved names: {reserved}')



# --- _assert_no_not_given -----------------------------------------------------
def _assert_no_not_given(
    obj: object,
    *,
    path: str = "root",
) -> None:
    if obj is _NOT_GIVEN:
        raise RuntimeError(f"_NOT_GIVEN leak at {path}")

    if isinstance(obj, dict):
        for k, v in obj.items():
            _assert_no_not_given(v, path=f"{path}.{k}")

    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            _assert_no_not_given(v, path=f"{path}[{i}]")


# --- _assert_no_none() --------------------------------------------------------
def _assert_no_none(
    obj: object,
    *,
    allowed_fields: set[str] | None = None,
    path: str = "root",
) -> None:
    if allowed_fields is None:
        allowed_fields = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            new_path = f"{path}.{k}"
            if v is None and k not in allowed_fields:
                raise RuntimeError(f"None not allowed at {new_path}")
            _assert_no_none(v, allowed_fields=allowed_fields, path=new_path)
    elif isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            new_path = f"{path}[{i}]"
            if v is None:
                raise RuntimeError(f"None not allowed at {new_path}")
            _assert_no_none(v, allowed_fields=allowed_fields, path=new_path)



# --- _precheck_auto_and_none() ------------------------------------------------
def _precheck_auto_and_none(
    *,
    arg_name: str,
    value: object,
    default: object,
) -> object:
    """
    Enforces:
    - reject "auto"
    - reject None
    - resolve _NOT_GIVEN → default
    - NEVER returns _NOT_GIVEN
    """

    if isinstance(value, str) and value.strip().lower() == "auto":
        raise ValueError(
            f"Invalid value for '{arg_name}': 'auto' is reserved for internal use. "
            "Omit the argument to use default behavior."
        )

    if value is None:
        raise ValueError(f"{arg_name} cannot be None.")

    if value is _NOT_GIVEN:
        if default is _NOT_GIVEN:
            raise RuntimeError(f"{arg_name}: no value provided and no default available")
        return default

    return value

