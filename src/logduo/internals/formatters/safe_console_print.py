"""
safe_console_print.py

This helper must be isolated in its own file to prevent circular dependencies

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
    Print the final message safely to the console.

    Rich Text, Panels, Tables, Matplotlib figures, and other display objects retain
    their normal presentation in the console. Regular strings are displayed exactly
    as supplied.

    For file output, Rich Text is converted to plain text. Objects that cannot be
    meaningfully represented in a text log, such as Panels, Tables, and Matplotlib
    figures, are replaced with descriptive placeholders.

    If the console cannot encode a character, it is safely escaped rather than
    causing the logging call to fail.
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


