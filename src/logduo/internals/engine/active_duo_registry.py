"""
active_duo_registry.py

Process-global registry for the currently active Duo instance.

Used by:
- log.join()
- active session lookup helpers

Last edited: 2026-5-27
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from logduo.logduo import Duo


# --- active session registry --------------------------------------------------
_ACTIVE_DUO: Duo | None = None


# --- _get_active_duo() --------------------------------------------------------
def _get_active_duo() -> Duo | None:
    return _ACTIVE_DUO


# ---_set_active_duo() ---------------------------------------------------------
def _set_active_duo(duo: Duo) -> None:
    global _ACTIVE_DUO
    _ACTIVE_DUO = duo


# --- _clear_active_duo() ------------------------------------------------------
def _clear_active_duo(duo: Duo | None = None) -> None:
    """
    Clear registry only if:
    - no Duo specified, or
    - specified Duo matches active registry instance
    """

    global _ACTIVE_DUO

    if duo is None or _ACTIVE_DUO is duo:
        _ACTIVE_DUO = None
