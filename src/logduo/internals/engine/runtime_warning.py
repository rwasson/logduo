"""
runtime_warning.py

Central runtime warning emission helper for Logduo.

Responsible for:
- warning deduplication
- fallback warning emission during partial initialization
- warning classification passthrough for JSONL (warn_key)

Last edited: 2026-5-27
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from logduo.internals.engine.runtime_classes import MessageKind

if TYPE_CHECKING:
    from logduo import Duo


# --- _runtime_warning() -------------------------------------------------------
def _runtime_warning(
    duo: Duo,
    *,
    warn_msg: str, extra: str | None = None,
    warn_key: str | None = None
) -> None:
    """
    Emit a deduplicated runtime warning.
    Warning messages should not include '\n'.

    Warnings are automatically prefixed with:
    LOGDUO WARNING:

    Warning messages should not include '\n' (emitted as MessageKind.INLINE)

    Deduplication is based only on warn_msg.
    extra and warn_key do not affect dedup behavior.
    """
    from logduo.internals.engine.level_entry import _level_entry
    from logduo.internals.formatters.safe_console_print import _safe_console_print

    runtime = duo._runtime

    # --- dedup based on msg only (not extras) ---
    if runtime.warning_already_registered(warn_msg):
        return
    runtime.unique_warning_set.add(warn_msg)

    # --- build display message ---
    base_warn_msg = f"LOGDUO WARNING: {warn_msg}"
    full_warn_msg = base_warn_msg if extra is None else f"{base_warn_msg} ({extra})"

    if "\n" in full_warn_msg:
        raise RuntimeError(
            "LOGDUO INTERNAL ERROR: \n\n"
            "_runtime_warning() received a message containing '\\n'."
            "Runtime warnings must emit single (inline) messages"
          )

    # --- dispatch or fallback ---
    # Use normal logging pipeline once runtime is initialized.
    if duo._initialized:
        _level_entry(
            duo,
            full_warn_msg,
            level="WARNING",
            label="WARNING",
            no_prefix=False,
            log_wrap_width="off",
            console_style="warning",
            warn_key=warn_key,
            event_type="system_warning",
        )
    elif duo._console:
        # fallback for partial initialization
        _safe_console_print(duo, message=full_warn_msg, message_kind=MessageKind.INLINE)

    else:
        # fallback for complete failure to initialize
        print(full_warn_msg)


    # Runtime warnings must be visible on console even when console_verbosity = 0.
    if duo._initialized and duo.session_config.console_verbosity == 0:
        print(full_warn_msg)
