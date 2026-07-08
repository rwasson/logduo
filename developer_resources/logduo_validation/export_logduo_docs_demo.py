"""
export_logduo_docs_demo.py

Developer validation script for log.export_logduo_docs().
Demonstrates where Logduo exports local documentation files:
- PYTEST_TOOLKIT_README.txt
- bundled example scripts

Also verifies the export message clearly reports:
- docs directory
- files created
- files preserved
- no-overwrite behavior

Last edited: 2026-07-08
"""

from pathlib import Path

from logduo import log

# from logduo import log, text_table, run

LOG_DIR = Path.cwd() / "logs"

# verbosity=3 so DEBUG and TRACE messages are visible in example_scripts
log.configure(log_dir_path=LOG_DIR)

log.export_logduo_docs()

log.close()


