"""
script_simple.py

Used by test_header_footer_blocks.py to verify

script-path detection and script-mode header/footer generation.
"""

import os

from logduo import log

log.configure(
    log_dir_path=os.environ["LOGDUO_TEST_OUTPUT_DIR"],
    log_file_layout="script",
    log_file_mode="write",
    log_wrap_width=80,
)

log("hello")
log(f"output_dir_path = {log.output_dir_path}")
log(f"os.environ['LOGDUO_TEST_OUTPUT_DIR'] = {os.environ['LOGDUO_TEST_OUTPUT_DIR']}")


log.close()
