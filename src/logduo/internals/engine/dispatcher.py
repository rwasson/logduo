"""
dispatcher.py

Central routing engine for logduo.
Responsibilities:
    - Resolve per-call arguments
    - Determine routing (console, main_sink_log, user_sink_log, JSONL)
    - Construct EmitEvent payloads per sink
    - Ensure emitters remain sink-isolated (no cross-sink knowledge)

Key invariants:
    - Callsite (file_name: line number) is computed ONCE per event, if required
    - Sink-specific resolution of call_args occurs in dispatcher.
         - Emitters receive only the finalized data needed for their own output.

Design constraints:
    - No formatting logic here
    - No file system logic here
    - No per-line mutation beyond splitting off leading and trailing blank lines

Loguru interaction:
    - Main sink logs and User sink logs pass through Loguru.
    - User sink messages appear in Loguru only if mirrored to main_sink_log
      (filtered by Loguru if to_main_log=True).
    - Metadata bound via loguru.bind() (e.g. sink_name, file_name) can be used f
        for applying Loguru filters.

Naming model:
    - sink_name = logical origin of the event (who emitted it)
        e.g. log.info(...) → "main_sink"
             audit.info(...) → "audit"   (stem of file_name)

    - file_name = physical destination (where it was written)
        e.g. "run.log", "audit.log"

    These are NOT one-to-one because routing is fan-out:
        - One sink_name may write to multiple outputs
            (e.g. "main_sink" → console and/or main_sink_log)
        - A user sink may also mirror to multiple outputs
            (e.g. "audit" → audit.log + main_sink_log + console)

    In short:
        sink_name → origin (logical)
        file_name → destination (physical)

Last edited: 2026-05-27
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from logduo import Duo

from logduo.internals.api_arg_resolvers.level_call_args_resolver import _resolve_level_call_args
from logduo.internals.engine.runtime_classes import (
    CreatedFileRecord,
    EmitEvent,
    RuntimeRecord,
    UserSinkConfig,
)
from logduo.internals.filesystem.callsite_utils import _get_caller, _shorten_callsite_for_prefix
from logduo.internals.formatters.message_prep import _message_kind
from logduo.internals.session_config.session_constants import (
    _LEVEL_RANK,
    _MAX_VERBOSITY_LEVEL,
    _SINK_TAG_WIDTH,
)
from logduo.internals.sinks.console import _emit_console
from logduo.internals.sinks.jsonl import _emit_jsonl
from logduo.internals.sinks.main_sink_log import _emit_main_sink_log
from logduo.internals.sinks.user_sink_log import _emit_user_sink


# --- _dispatch_event() ----------------------------------------------------------------------
def _dispatch_event(  # noqa: PLR0915
    duo: Duo,
    *,
    sink_name: str,
    level: str,
    label: str,
    message: object,
    call_args: dict[str, Any],
    warn_key: str | None = None,
    event_type: str = "message",
) -> None:
    """
    Route one normalized log event to enabled destinations.

    Routing responsibilities:
    - resolve per-sink call args
    - apply verbosity gating
    - compute shared metadata once (callsite, message_kind)
    - construct sink-specific EmitEvent payloads

    Notes:
    - Console always uses session_config formatting policy.
    - User sinks may fan out to:
        user_sink_log, main_sink_log, console, JSONL.
    - JSONL routing occurs last so output_targets reflects final routing.

    Terminology:
    - sink_name:
        logical event origin
        e.g. "main_sink", "audit"
    - file_name:
        physical output destination
        e.g. "run.log", "audit.log"
    - event_type:
        primarily used by the JSONL emitter.
        Distinguishes normal log messages from
        internally-generated events such as:
            session_start
            session_end
            system_warning
            session_file_registration
    """

    output_target_list: list[str] = []

    duo._refresh_pid()
    runtime = duo._runtime
    runtime.event_count += 1  # event counter

    # --- Obtain CreatedFileRecord (key = file_path) for formatting fields ---
    # These destination kinds are limited to one per session
    # both have sink_name = "main_sink"
    main_sink_log_cfr = _get_cfr_by_kind(runtime, "main_sink_log")
    jsonl_cfr = _get_cfr_by_kind(runtime, "jsonl")

    # Users can create call new_logger() multiple times,
    # so must find file_path to locate their file entry in CreatedFileRecord
    user_sink_config = None
    user_sink_log_cfr = None
    if sink_name != "main_sink":
        user_sink_config = runtime.user_sink_config_registry.get(sink_name)
        if user_sink_config is None:
            raise ValueError(
                f"LOGDUO INTERNAL ERROR: sink_name={sink_name!r} has no UserSinkConfig"
            )
        if user_sink_config.log_file_path is not None:
            user_sink_log_cfr = runtime._get_created_file_record_by_file_path(
                user_sink_config.log_file_path
            )

    # --- Precompute verbosity rank ---
    #  rank = {1 (CRITICAL, ERROR, WARNING), 2 (SUCCESS, INFO), 3 (DEBUG, TRACE)}
    rank = _LEVEL_RANK.get(level)
    if rank is None:
        raise RuntimeError(f"LOGDUO ERROR: Unknown level {level!r}")

    # --- Derive callsite (file_name:line_number or None) ---
    callsite = None
    if _needs_callsite(
        duo,
        level=level,
        main_sink_log_cfr=main_sink_log_cfr,
        jsonl_cfr=jsonl_cfr,
        user_sink_log_cfr=user_sink_log_cfr,
        user_sink_config=user_sink_config,
    ):
        try:
            file_name, line_num = _get_caller()
            if isinstance(file_name, str) and isinstance(line_num, int):
                callsite = _shorten_callsite_for_prefix(file_name, line_num)
        except (OSError, RuntimeError, ValueError, TypeError):
            pass

    # --- Derive sink_tag for main_sink_log and console (if conditions apply) ---
    # sink_tag is name of new_logger and can optionally prepend message
    sink_tag = None
    if (
        duo.session_config.show_logger_name
        and user_sink_config is not None
        and (user_sink_config.to_main_log or user_sink_config.to_console)
    ):
        sink_tag = sink_name[:_SINK_TAG_WIDTH].upper()

    # --- Determine message_kind to pass to EmitEvent
    # message_kind:
    #    INLINE (string without '\n'),
    #    STRUCTURED (string with \n'),
    #    RICH Text
    #    Rich Renderable (all other Rich objects)
    #    OBJECT (all other objects)
    message_kind = _message_kind(message)

    # message_kind Emitter policy:
    #   - Console:
    #       INLINE strings are wrapped, with continuation lines stacked under '|'
    #       Rich objects are rendered directly.
    #       Other objects rendered as strings if possible
    #   - Logs (main_sink and user_sink):
    #       If log_wrap_width != 'off', INLINE strings are wrapped, with continuation lines stacked under '|'
    #       Rich Text is converted to plain text.
    #       Other objects rendered as strings if possible
    #   - JSONL:
    #       Object or string version is always recorded.

    # --- Console ---
    console_config = duo.session_config
    if _should_route_to_sink(
        rank=rank,
        destination="console",
        user_sink_config=user_sink_config,
        console_verbosity=duo.session_config.console_verbosity,
        main_sink_log_verbosity=duo.session_config.log_verbosity,
    ):
        resolved_call_args = _resolve_level_call_args(
            duo, is_console_sink=True, sink_config=console_config, call_args=call_args
        )
        output_target_list.append("console")
        event = EmitEvent(
            sink_name=sink_name,
            target_kind="console",
            level=level,
            label=label,
            message=message,
            resolved_call_args=resolved_call_args,
            callsite=callsite,
            created_file_record=None,
            output_targets=["console"],
            warn_key=None,
            event_type=None,
            sink_tag=sink_tag,
            message_kind=message_kind,
        )
        _emit_console(duo, event=event)

    # --- Main_sink log ---
    if main_sink_log_cfr is not None:
        if _should_route_to_sink(
            rank=rank,
            destination="main_sink_log",
            user_sink_config=user_sink_config,
            console_verbosity=duo.session_config.console_verbosity,
            main_sink_log_verbosity=duo.session_config.log_verbosity,
        ):
            resolved_call_args = _resolve_level_call_args(
                duo, is_console_sink=False, sink_config=main_sink_log_cfr, call_args=call_args
            )
            output_target_list.append(main_sink_log_cfr.file_name)

            event = EmitEvent(
                sink_name=sink_name,
                target_kind="main_sink_log",
                level=level,
                label=label,
                message=message,
                resolved_call_args=resolved_call_args,
                callsite=callsite,
                created_file_record=main_sink_log_cfr,
                output_targets=[main_sink_log_cfr.file_name],
                warn_key=None,
                event_type=None,
                sink_tag=sink_tag,
                message_kind=message_kind,
            )
            _emit_main_sink_log(duo, event=event)

    # --- User_Sink Log ---
    user_sink_routed = False
    if user_sink_log_cfr is not None:
        if _should_route_to_sink(
            rank=rank,
            destination="user_sink_log",
            user_sink_config=user_sink_config,
            console_verbosity=duo.session_config.console_verbosity,
            main_sink_log_verbosity=duo.session_config.log_verbosity,
        ):
            user_sink_routed = True
            resolved_call_args = _resolve_level_call_args(
                duo, is_console_sink=False, sink_config=user_sink_log_cfr, call_args=call_args
            )
            output_target_list.append(user_sink_log_cfr.file_name)
            event = EmitEvent(
                sink_name=sink_name,
                target_kind="user_sink_log",
                level=level,
                label=label,
                message=message,
                resolved_call_args=resolved_call_args,
                callsite=callsite,
                created_file_record=user_sink_log_cfr,
                output_targets=[user_sink_log_cfr.file_name],
                warn_key=None,
                event_type=None,
                sink_tag=None,
                message_kind=message_kind,
            )
            _emit_user_sink(duo, event=event)

    # --- Check for silent user-sink routing errors ---
    if user_sink_config is not None:
        if user_sink_config.log_file_path is None and user_sink_config.log_verbosity > 0:
            raise RuntimeError(
                f"LOGDUO INTERNAL ERROR: User sink '{sink_name}' has "
                "log_verbosity > 0 but no log_file_path"
            )
        if user_sink_config.log_verbosity > 0:
            if rank <= user_sink_config.log_verbosity and not user_sink_routed:
                raise RuntimeError(
                    f"LOGDUO INTERNAL ERROR: User sink '{sink_name}' expected to route "
                    f"but did not (level={level}, verbosity={user_sink_config.log_verbosity})"
                )

    # --- JSONL ---
    # MUST be last to capture full output_target_list
    if duo.session_config.write_jsonl:
        if jsonl_cfr is not None:
            resolved_call_args = _resolve_level_call_args(
                duo, is_console_sink=False, sink_config=jsonl_cfr, call_args=call_args
            )
            output_target_list.append(jsonl_cfr.file_name)
            event = EmitEvent(
                sink_name=sink_name,
                target_kind="jsonl",
                level=level,
                label=label,
                message=message,
                resolved_call_args=resolved_call_args,
                callsite=callsite,
                created_file_record=jsonl_cfr,
                output_targets=output_target_list.copy(),
                warn_key=warn_key,
                event_type=event_type,
                sink_tag=None,
                message_kind=message_kind,
            )
            _emit_jsonl(duo, event=event)


# === Internal helpers =========================================================
def _get_cfr_by_kind(runtime: RuntimeRecord, kind: str) -> CreatedFileRecord | None:
    for cfr in runtime._get_file_list_in_cfr():
        if cfr.file_kind == kind:
            return cfr
    return None


# --- _needs_callsite() --------------------------------------------------------
def _needs_callsite(  # noqa: PLR0911  # many returns
    duo: Duo,
    *,
    level: str,
    main_sink_log_cfr: CreatedFileRecord | None,
    jsonl_cfr: CreatedFileRecord | None,
    user_sink_log_cfr: CreatedFileRecord | None,
    user_sink_config: UserSinkConfig | None,
) -> bool:
    """
    Conservative decision: compute callsite if ANY sink might need it.
    Does NOT depend on per-sink resolution.
    """

    # --- 1) JSONL always needs callsite ---
    if duo.session_config.write_jsonl and jsonl_cfr is not None:
        return True

    # --- 2) Console prefix ---
    if duo.session_config.console_prefix == "source":
        return True

    # --- 3) Main log prefix ---
    if main_sink_log_cfr is not None and main_sink_log_cfr.log_prefix == "source":
        return True

    # --- 4) User sink prefix ---
    if user_sink_log_cfr is not None and user_sink_log_cfr.log_prefix == "source":
        return True

    # --- 5) Debug-driven callsite ---
    if level == "DEBUG" and duo.session_config.show_debug_source:
        if duo.session_config.console_verbosity == _MAX_VERBOSITY_LEVEL:
            return True

        if (main_sink_log_cfr is not None and
                duo.session_config.log_verbosity == _MAX_VERBOSITY_LEVEL):
            return True

        if (user_sink_config is not None
                and user_sink_config.log_verbosity == _MAX_VERBOSITY_LEVEL):
            return True

    return False


# --- _should_route_to_sink() --------------------------------------------------
def _should_route_to_sink(  # noqa: PLR0911  # many returns
    *,
    rank: int,
    destination: str,
    user_sink_config: UserSinkConfig | None,
    console_verbosity: int,
    main_sink_log_verbosity: int,
) -> bool:
    """
    destination: "console", "main_sink_log", "user_sink_log"
    user_sink_config: None or UserSinkConfig

    Note: destination decision not needed for "jsonl"
     - if their paths were identified at the start of _dispatch_event(),
       then messages should be dispatched to them
    """

    # --- CONSOLE ---
    if destination == "console":
        if user_sink_config is not None:
            if not user_sink_config.to_console:
                return False
        if rank > console_verbosity:
            return False
        return True

    # --- MAIN SINK LOG ---
    if destination == "main_sink_log":
        if user_sink_config is not None:
            if not user_sink_config.to_main_log:
                return False

        if rank > main_sink_log_verbosity:
            return False

        return True

    # --- USER SINK LOG ---
    if destination == "user_sink_log":
        if user_sink_config is None:
            return False
        if rank > user_sink_config.log_verbosity:
            return False
        return True

    raise RuntimeError(f"LOGDUO ERROR: unknown destination={destination!r}")
