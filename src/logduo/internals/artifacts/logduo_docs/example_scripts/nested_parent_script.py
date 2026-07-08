"""
nested_parent_script.py

Demonstrates running a child script/s from a parent script.

The parent script starts the Logduo session. The child script joins
that active session with log.join(), so both scripts write to the same
session log and output directory.

The parent script can call multiple child scripts and/or call
one child script multiple times.

Run this file directly.

Child script used by this example:
    nested_child_script.py

Last edited: 2026-07-08
"""

from pathlib import Path

from logduo import log, run

LOG_DIR = Path.cwd() / "logs"

def main() -> None:  # noqa: PLR0915   # example scripts can have 'too many statements'

    log.configure(
        console_theme="light",
        log_dir_path=LOG_DIR,
        console_wrap_width=140,
        write_jsonl=True,
        console_prefix="source",
        log_prefix="source",
    )

    log(
        "run(<file>) executes a Python script from a parent script "
        "or an interactive session."
    )
    log("run(<file>) where <file> is an absolute file path "
        "or an importable module name")
    log("For more details: help(run)")



    script_dir_path = Path(__file__).parent

    run(script_dir_path / "nested_child_script.py")

    log.close()


if __name__ == "__main__":
    main()
