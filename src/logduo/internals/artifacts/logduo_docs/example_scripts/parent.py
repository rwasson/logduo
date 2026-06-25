"""
parent.py

Demonstrates logging in parent and child scripts using run() and log.join().

The child script used by this example is:
    parents_child.py

Last edited: 2026-06-16
"""

from pathlib import Path

from logduo import log, run

LOG_DIR = Path.cwd() / "logs"

def main() -> None:

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

    run(script_dir_path / "parents_child.py")

    log.close()


if __name__ == "__main__":
    main()
