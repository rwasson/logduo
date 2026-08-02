"""
quick_scripts_in_readme.py

Last edited: 2026-8-2
"""

from pathlib import Path

from logduo import log, run

my_log_dir = Path.cwd() / "logs"

log.configure(
    log_dir_path=my_log_dir,
    keep=3,
    console_theme="light",
    log_prefix="source",
)

log("hello world")
log(f"output directory path = {log.output_dir_path}")
log(f"main log file path = {log.main_log_file_path}")

log.export_logduo_docs()

var = 3 * 3

log.debug(f"made it here: var = {var}")

output_dir_path = log.output_dir_path
assert isinstance(output_dir_path, Path)     # Satisfy static type checkers.

myplot_output_path = output_dir_path / "myplot.png"


log("")
log("interactive example")
log("hello world")

log.info("hello world again, info is the default logging level.")
log.warning("The logging level 'WARNING' is displayed in orange on the console.")

help(log.configure)
help(run)


log.close()
