"""
safe_console_print.py

This little helper must be isolated in its own file to prevent circular dependencies

Last edited: 2026-4-25
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

from logduo.internals.engine.runtime_classes import MessageKind

if TYPE_CHECKING:
    from logduo import Duo


# --- _safe_console_print() -------------------------------------------------
def _safe_console_print(
        duo: Duo,
        *,
        message: Any,
        message_kind: MessageKind,
) -> None:
    """
    Final console emitter.

    Behavior:
    - Rich renderables (Panel, Table, etc.) are printed as-is.
    - Markup strings are treated as plain text.
    """

    console = duo._console
    if console is None:
        print(message)
        return

    try:
        if message_kind in (
                MessageKind.RICH_TEXT,
                MessageKind.RICH_RENDERABLE,
        ):
            console.print(message)
        else:
            console.print(message, soft_wrap=True)
    except Exception:  # noqa
        try:
            print(message)
        except Exception:  # noqa
            pass


