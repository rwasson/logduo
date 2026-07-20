"""
first_script.py

Logduo example.

Demonstrates:
- session configuration
- help
- verbosity
- standard log levels
- custom levels
- message wrapping
- structured blocks (messages containing \n)
- output path helpers
- additional log files
- log.close()

Last edited: 2026-6-22
"""

from pathlib import Path
from pydoc import plain, render_doc

from logduo import log

# from logduo import log, text_table, run

LOG_DIR = Path.cwd() / "logs"

# verbosity=3 so DEBUG and TRACE messages are visible in example_scripts
log.configure(
    log_dir_path=LOG_DIR,
    console_wrap_width=150,
    log_wrap_width=80,
)

log("hello world")
log("")
log("Each log message has 3 options: no_prefix (True/False), log_wrap_width, console_style (Rich styles)")
log('Example: log("hello world in bold orchid", no_prefix=True, console_style="bold orchid", log_wrap_width=80)))')
log("hello world in bold orchid", console_style="bold orchid", no_prefix=True, log_wrap_width=80)


log(" ")
log("--- Help ---")
log("View help in the console: help(log.configure)")
log(
    "Write help to the log:\n"
    "    from pydoc import plain, render_doc\n"
    "    log(plain(render_doc(log.configure)))"
)

log(plain(render_doc(log.configure, title="Logduo documentation: %s")))


log(" ")
log("Obtain Logduo docs (README.txt and example scripts): log.export_logduo_docs()")
log.export_logduo_docs()
log(f"View configuration field: log.session_config.console_verbosity = {log.session_config.console_verbosity}")
log("    Note: session configuration is read-only after startup.")
log("    Note: configuration table (including descriptions and allowed values) is auto-generated each session.")
log("          To disable auto-generation: log.configure(..., write_config_table=False)")


log(" ")
log("--- Log levels----")
log("Emission controlled by configured log_verbosity and console_verbosity (default = 2, range = [0, 3])")
log.critical("critical message: displayed if verbosity >= 1")
log.error("error message: displayed if verbosity >= 1")
log.warning("warning message: displayed if verbosity >= 1")
log.success("success message: displayed if verbosity >= 2")
log.info("information message: displayed if verbosity >= 2. This is the default level for:  log(message) ")
log.debug("debug message: displayed if verbosity = 3")
log.debug("debug message: line starts with name of script and the message's line number.")
log.debug("debug message: to disable debug source: log.configure(..., show_debug_source = False)")
log.trace("trace message: displayed if verbosity = 3")

log(" ")
log("--- Exception logging with Traceback ---")
log("Example: use log.exception() inside an except block to show a traceback")
try:
    x = 1 / 0
except ZeroDivisionError:
    log.exception("Division by zero")

# new_level() example
log(" ")
log("--- Custom level labels ----")
log('log.new_level("TIP", console_style="bold orchid", level="DEBUG")')
log.new_level("TIP", console_style="bold orchid", level="DEBUG")
log.tip('Default severity level is "INFO" if not specified in new_level().')
log(" ", no_prefix=True)


log(" ")
log("--- Wrapping and indent behavior ---")
log(
    "This is a deliberately long message that demonstrates wrapping "
    "behavior in both the console and the log file. Wrapped lines "
    "remain aligned with the start of the message text."
)

pad = " " * 13
# messages indented by pad to clear level prefix
# without {pad}, messages displayed flush left

log("This message contains '\\n' characters (structured block).\n"
    "Messages containing '\\n' are displayed flush left below the prefix.\n"
    "This gives structured blocks maximum line width, and allows users to specify desired indent."
    )
log(" ")
log(
    f"{pad}Manual padding can be used to indent structured blocks if desired.\n"
    f"{pad}Example:\n"
    f"{pad}pad = ' ' * 13\n"
    f"{pad}log(f\"{{pad}}Manual padding can be used when indentation is desired.\\n\")"
)

log(" ")
log("--- Path helpers ---")
log("1. output_dir_path (directory of output files) = log.output_dir_path:")
log(f"output_dir_path = {log.output_dir_path}")
log(" ")
log("2. main_log_file_path (path of main log file) = log.main_log_file_path:")
log(f"main_log_file_path = {log.main_log_file_path}")
log(" ")
log("log.close() is optional in scripts but mandatory in interactive sessions.")


log(" ")
log("--- new_logger(): create dedicated output file ---")
log('rep = log.new_logger("report", to_console=True, to_main_log=True)')
log('rep(message) will send message to report.log, as well as to console and main log file.')
rep = log.new_logger(
    "report",
    to_console=True,
    to_main_log=True,
)
rep("Question 1 answer")
rep("Question 2 answer")
log("To disable display of 'REPORT' tag: log.configure(..., show_logger_name=False)")

log.close()


