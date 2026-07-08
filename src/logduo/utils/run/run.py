"""
run.py

Interactive development helper for importing or reloading modules
in interactive sessions or nested-script development workflows.

Last edited: 2026-5-27
"""

import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType

__all__ = ["run"]


def run(file: (str | Path)) -> ModuleType:
    """
    Execute a Python script or load/reload an importable module.

    This helper is primarily intended for:
    - execution of a script in interactive sessions
    - execution of a script from inside another script
    - simulation iteration
    - rapid testing loops

    Recommended:
        script_dir = Path("/Users/name/project/scripts")
        run(script_dir / "my_script.py")

    Advanced:
        run("my_module")
        # when my_module is already importable by Python

    Args:
        file:
            Absolute script path (recommended):
                run(Path("/Users/name/project/scripts/my_script.py"))
            Importable module name:
                run("my_module")

    Behavior:
        - each call executes a fresh copy of the target script
        - changes made to the script are picked up on the next run()

        If you want normal Python import/reload behavior,
        use import and importlib.reload() directly.

    Notes:
        - run() executes the target script, but does not restart Python
        - variables in your interactive session or calling script are not reset
    """
    value_is_path, file = _resolve_run_target(file)

    # --- file is script path ---
    if value_is_path:
        abs_file_path = file
        module_name = f"_run_{abs(hash(abs_file_path))}"

        spec = importlib.util.spec_from_file_location(
            module_name,
            str(abs_file_path),
        )

        if spec is None or spec.loader is None:
            raise RuntimeError(f"Could not load script:\n{abs_file_path}")

        sys.modules.pop(module_name, None)
        module = importlib.util.module_from_spec(spec)

        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module

    # --- file is importable module name ---
    assert isinstance(file, str)
    module_name = file
    spec = importlib.util.find_spec(module_name)

    if spec is None:
        raise ValueError(
            f"Could not find importable module: {module_name!r}\n\n"
            "Recommended:\n\n"
            "    script_dir = Path('/absolute/path/to/scripts')\n"
            "    run(script_dir / 'my_script.py')\n\n"
            "Advanced:\n\n"
            "    run('my_module')\n"
            "    # only works when Python can already import it"
        )

    sys.modules.pop(module_name, None)

    return importlib.import_module(module_name)


# === Internal helper ==========================================================
def _resolve_run_target(value: str | Path) -> tuple[bool, str | Path]:
    """
    Normalize and validate a run() target.
    Returns:

        (value_is_path, resolved_value)

    If value_is_path is True:
        resolved_value is an absolute validated Path.
    If value_is_path is False:
        resolved_value is a validated importable module name.

    """
    if not isinstance(value, (str, Path)):
        raise ValueError("run() target must be a string or Path")

    # --- Explicit Path provided ---
    if isinstance(value, Path):

        if not value.is_absolute():
            raise ValueError("run() path must be absolute")

        if value.suffix.lower() != ".py":
            raise ValueError("run() path must point to a .py file")

        if not value.exists():
            raise ValueError(f"Script file does not exist:\n{value}")

        if value.is_dir():
            raise ValueError("run() path must be a file, not a directory")

        return True, value.resolve(strict=True)

    # --- Script name string provided ---
    file = value.strip()

    if not file:
        raise ValueError("run() target cannot be empty")

    if (
        "/" in file
        or "\\" in file
        or file.endswith(".py")
        or Path(file).is_absolute()
    ):
        raise ValueError(
            "run() accepts either:\n"
            "    run('my_script')\n"
            "or:\n"
            "    run(Path('/absolute/path/my_script.py'))"
        )

    return False, file
