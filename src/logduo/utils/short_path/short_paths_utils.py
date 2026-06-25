"""
short_path_utils.py

Last Edited: 2026-06-19
"""

_ELLIPSIS_CHAR = "…"
_MIN_WIDTH_WINDOWS_DRIVE = 3
_MIN_WIDTH_SHORT_PATH = 15


# === Internal helpers =========================================================
# --- shorten_stem() -----------------------------------------------------------
def shorten_stem(stem: str, limit: int, ellipsis_str: str = _ELLIPSIS_CHAR) -> str:
    """Return s shortened to limit with a centered ellipsis."""
    if limit <= 0:
        return ""
    if len(stem) <= limit:
        return stem
    if limit <= len(ellipsis_str):
        return ellipsis_str[:limit]

    budget = limit - len(ellipsis_str)
    left = budget // 2
    right = budget - left

    return stem[:left] + ellipsis_str + stem[-right:]


# --- split_filename() ---------------------------------------------------------
def split_filename(filename: str) -> tuple[str, str]:
    """
    Split filename into:
        stem.ext1.ext2.ext3
    →
        (stem, .ext1.ext2.ext3)
    """
    if "." not in filename:
        return filename, ""
    stem, remainder = filename.split(".", 1)

    return stem, "." + remainder


# --- is_windows_path() --------------------------------------------------------
def is_windows_path(path: str) -> bool:
    return (
        len(path) >= _MIN_WIDTH_WINDOWS_DRIVE
        and path[0].isalpha()
        and path[1] == ":"
        and path[2] in ("/", "\\")
    )
