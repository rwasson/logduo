"""
/logduo_project/source/logduo/__init__.py

PUBLIC LOGDUO ENTRYPOINT

Last edited: 2026-5-27
"""

from __future__ import annotations

from logduo.utils.run.run import run
from logduo.utils.table.text_table import text_table

from .logduo import Duo, logduo, logduo as log

__all__ = [
    "log",         # typical entry
    "Duo",         # advanced entry for independent logger instances
    "run",         # interactive/nested workflow helper: reloads imported script
    "text_table",  # created log-friendly table, supports ANSI in console
]
