"""
parents_child.py

Assumes a logduo session is already active
(created in a parent script or interactive session).

This file should JOIN the existing logduo session, not configure a new one.

To run this example in Pycharm: right click on the file: parent.py

Last edited: 2026-06-16
"""

from logduo import log


# --- join existing active session --------------------------------------------
# no arguments expected
log = log.join()


# --- normal logging after join -----------------------------------------------
log("joined session successfully")
log.warning("warning example")


log("To create a new custom logger 'rep':")
log('    rep = log.new_logger("report", to_console=True, to_main_log=True) ')


# --- logging with a new dedicated logger (rep) --------------------------------
rep = log.new_logger("report", to_console=True, to_main_log=True)

rep("rep(messages) will appear in report.log")
rep("Since both to_console and to_main_log were enabled: ")
rep("rep() messages will also appear on the console and in the main log. ")
rep("The prefix for REPORT lines can be disabled in the main log file:")
rep("    log.configure(..., show_logger_name = False)")
