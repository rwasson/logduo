"""
short_path.py

Last edited 2026-06-04
"""

from collections.abc import Sequence
from pathlib import Path

__all__ = ["short_path", "short_path_list"]

from logduo.utils.short_path.short_paths_utils import (
    _MIN_WIDTH_SHORT_PATH,
    _MIN_WIDTH_WINDOWS_DRIVE,
    is_windows_path,
    shorten_stem,
    split_filename,
)


# --- short_path() -------------------------------------------------------------
def short_path(
    path: str | Path,
    *,
    width: int = 80,
    anchor_dir: str | Path | None = None,
    max_parents: int | None = None,
    _min_width_short_path: int = _MIN_WIDTH_SHORT_PATH,
) -> str:
    """
    Build the shortest useful path by starting with the filename and
    prepending parents until width would be exceeded.

        filename (shorten if needed to fit width by itself)
        ↓
        add nearest parent
        ↓
        add next parent
        ↓
        stop when:
            • width would be exceeded
            • anchor is reached
            • max_parents is reached
         ↓
        return last fit


    """
    was_windows_path = False
    if width < _min_width_short_path:
        raise ValueError("width must be >= {_min_width_short_path}")

    if max_parents is not None and max_parents < 0:
        raise ValueError("max_parents must be >= 0")

    # --- Build path parts ---
    path_str = str(path)
    if is_windows_path(path_str):
        was_windows_path = True
        parts = path_str.replace("\\", "/").split("/")
        if anchor_dir is not None:
            anchor_parts = str(anchor_dir).replace("\\", "/").split("/")

            # if Path is inside anchor_dir; collapse anchor prefix to anchor name.
            if parts[: len(anchor_parts)] == anchor_parts:
                parts = [anchor_parts[-1], *parts[len(anchor_parts) :]]
    else:
        path_abs = Path(path).expanduser().resolve(strict=False)

        if anchor_dir is not None:
            anchor_abs = Path(anchor_dir).expanduser().resolve(strict=False)
            try:
                rel = path_abs.relative_to(anchor_abs)
                parts = [anchor_abs.name, *rel.parts]
            except ValueError:
                parts = list(path_abs.parts)
        else:
            parts = list(path_abs.parts)

        # Remove leading '/' from absolute paths.
        if parts and parts[0] == "/":
            parts = parts[1:]

    filename = parts[-1]

    # --- Filename alone ---
    if len(filename) > width:
        stem, ext = split_filename(filename)
        stem_width = width - len(ext)
        short_stem = shorten_stem(stem, stem_width)
        short_filename = short_stem + ext
        return short_filename

    if max_parents == 0:
        return filename

    best_fit = filename
    parents_added = 0

    # --- Add parents nearest → farthest ---
    for parent in reversed(parts[:-1]):
        if max_parents is not None and parents_added >= max_parents:
            break
        if best_fit == filename:
            candidate = f"/{parent}/{filename}"
        else:
            candidate = f"/{parent}{best_fit}"
        if len(candidate) > width:
            return best_fit

        best_fit = candidate
        parents_added += 1

    # remove leading / if inserted in front of C: in initial Windows paths
    if (
        was_windows_path
        and len(best_fit) >= _MIN_WIDTH_WINDOWS_DRIVE
        and best_fit[0] == "/"
        and best_fit[1].isalpha()
        and best_fit[2] == ":"
    ):
        return best_fit[1:]

    return best_fit


# --- short_path_list() -------------------------------------------------------
def short_path_list(
    paths: Sequence[str | Path],
    *,
    width: int = 80,
    anchor_dir: str | Path | None = None,
    max_parents: int | None = None,
) -> list[tuple[str, str]]:
    """
    Build long and shortened labels for a sequence of paths.

    Returns:
        [long_path, short_path]
    """

    if not paths:
        return []

    results: list[tuple[str, str]] = []

    for path in paths:
        path_abs = Path(path).expanduser().resolve(strict=False)
        long_path = path_abs.as_posix()
        short_label = short_path(
            path_abs, width=width, anchor_dir=anchor_dir, max_parents=max_parents
        )
        results.append((long_path, short_label))

    return results


