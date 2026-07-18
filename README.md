Logduo
======
Logging, console output, and file management for Python scripts and interactive sessions.

Simple by default, configurable for advanced logging workflows.

Platform: Tested on macOS, Windows, and Ubuntu.


Key Capabilities
-----------------
- Manages output directories and log files
- Supports ANSI-styled and Rich console output while preserving readable plain-text logs
- Provides extensive `help()` documentation and actionable error messages
- Validates arguments to all Logduo methods and functions to prevent unexpected behavior
- Safely prunes old run directories containing a Logduo marker file
- Generates session artifacts: config_table.txt, config.json
- Captures JSONL event streams
- Creates dedicated log files via `new_logger()`
- Creates custom logging labels via `new_level()`
- Supports nested scripts via `log.join()` and `run()`



Quick Start (in script or interactive session)
----------------------------------------------
    from logduo import log

    log("hello world")
    log.warning("warning message")

If a message is logged before `log.configure()` is called, the logging session starts automatically using Logduo defaults and `pyproject.toml` settings.

Key default settings:
  - `console_verbosity = 2` and `log_verbosity = 2`
    - Messages (other than TRACE and DEBUG) are sent to both the console and the main log file.
  - `log_dir_path = "auto"`
    - The `logs` directory is placed in the project root if identified; otherwise, in the current working directory.
  - `log_file_layout = "run"`
    - Logs are created in timestamped run directories.
  - `keep = "off"`
    - Previous run directories are not pruned automatically.
    - If `keep` is set to a positive integer `n`, the newest `n` Logduo-marked run directories are kept and older run directories are pruned.
  - `write_config_table = True`
    - `config_table.txt` is written with configuration values, descriptions, and allowed values.


Configure (Optional)
--------------------
Recommendation: Place all regularly used configuration settings in pyproject.toml under `[tool.logduo]`

    from pathlib import Path
    from logduo import log

    my_log_dir = Path("/absolute/path/to/my_log_dir")

    log.configure(log_dir_path=my_log_dir, keep=3, console_verbosity=3, log_verbosity=3)
    log("hello world")


Export Logduo Docs
------------------
Export bundled documentation and example scripts to a local `logduo_docs/` directory:

    log.export_logduo_docs()

Exported files include:
- `README.txt`
- `examples/first_script.py`
- `examples/console_rendering.py`
- `examples/data_analysis.py`
- `examples/math_report_notation.py`
- `examples/nested_parent_script.py`
- `examples/nested_child_script.py`


Help
----
- Help is available for all Logduo methods and functions (displays in console only):

      help(log.configure)

- Help includes examples, argument descriptions, and usage notes.

    
Typical Workflows
-----------------
- Debug session: By default, log.debug() includes the calling file name and line number at the start of each message. Disable with: log.configure(..., show_debug_source=False)

       from logduo import log
       log.configure(log_verbosity=3, console_verbosity=3)

       log.debug(f"made it here: var = {var}")

- Create additional log files for dedicated output. Messages logged with `rep` are recorded in report.log and optionally mirrored to the console and/or main log file.

       rep = log.new_logger("report", to_console=True, to_main_log=False)
       rep("Question 1 answer:")

- Use the output directory to save plots, CSVs, reports, and other generated files

       myplot_output_path = log.output_dir_path / "myplot.png"

- Close the session (required in interactive sessions, optional in scripts)

       log.close()


Logduo Methods and Functions
----------------------------
- Manage session:
  - `log.configure()`
  - `log.close()`
  - `log.join()`

- Log levels:
  - `log()` or `log.info()`
  - `log.trace()`
  - `log.debug()`
  - `log.success()`
  - `log.warning()`
  - `log.error()`
  - `log.critical()`
  - `log.exception()`  # ERROR + Traceback

- Create custom log label:
  - `log.new_level()`  # Create a custom label handled as an existing level; default = "INFO"

- Create additional output:
  - `log.new_logger()`       # Logduo-managed extra log file
  - `log.new_loguru_sink()`  # Advanced Loguru sink
  - `log.export_logduo_docs()`

- Access paths:
  - `log.output_dir_path`
  - `log.main_log_file_path`

- Utility function: 
  - `run()`  # Execute child script or importable module in a parent script or an interactive session.
  - Import with: `from logduo import run`

 
Behavior
========

Prefixes
--------
- One prefix per log event.
- Console and log files have independent prefix settings: `console_prefix`, `log_prefix`
  - `off` → No prefix. Wrapped lines align flush left
  - `level` → Prefix shows level. Wrapped lines align under message.
  - `timestamp` → Prefix shows timestamp and level. Wrapped lines align under message.
  - `source` → Prefix shows timestamp, level, and source. Wrapped lines align under source.
- Example console output: `console_prefix="source"`, `show_pid_in_console=True`, `console_wrap_width=80`

  
        16:30:40.371 | WARNING  | example_2.py:382 -  (15408:i1) Logduo is designed for
                                  data scientists, researchers, students, and Python
                                  developers who want readable console output, organized
                                  log files, and minimal logging setup.
    

Message Rendering
-----------------
- Strings without `\n`: Displayed inline with the prefix.
    - Console: Wrapped (displayed line width = `console_wrap_width`).
    - Log files: Wrapped only if `log_wrap_width` is set to a positive integer. Default is `"off"`.
- Strings containing `\n`: Displayed as block flush left below prefix. Line breaks are honored.
    - This preserves the full available line width for tables, panels, JSON, tracebacks, and other structured content.
    - Use manual indenting or Rich `Padding` if indent behavior is desired:
  
           indent = " " * 13
           log(
              f"{indent}Step 1: Load data\n"
              f"{indent}Step 2: Clean data\n"
           ) 
- ANSI-styled strings and Rich `Text` objects are rendered on the console and written as plain text in log files.
- Other Rich objects, such as `Panel`, are rendered on the console but displayed as placeholders in log files. 
    - For more examples, use `log.export_logduo_docs()` and see `console_rendering.py`. 




  
Log File Name and Location
--------------------------
- Log file name:
  - Custom `log_file_name`: `log.configure(log_file_name="my_name.ext")`
  - Default `log_file_name`: calling script stem + `.log`
    - If the calling script is my_file.py: default `log_file_name` → `my_file.log`
    - If no calling script is found, as expected in interactive sessions: default `log_file_name` → `session.log`
- Location of log directory:
  - Custom `log_dir_path`: `log.configure(log_dir_path=my_log_dir)`
  - Default `log_dir_path`:
    - If pyproject.toml is not detected: `log_dir_path` = current working directory / "logs"
    - If pyproject.toml is detected: `log_dir_path` = parent directory of pyproject.toml / "logs"
- Location of log file: set by `log_file_layout`: `"flat"`, `"script"`, or `"run"` (default)
  - flat:   `log_dir_path/log_file_name`
  - script: `log_dir_path/script_stem/log_file_name`
  - run:    `log_dir_path/script_stem/run_yyyy_mm_dd__hh_mm_ss/log_file_name`

Note:
  - If no calling script is found, `script_stem` is set to `"session"` when `log_file_layout` = `"script"` or `"run"`
  - If `log_file_path` is provided, it specifies the complete log file path
    - `log_file_path` overrides `log_file_layout`, `log_dir_path`, and `log_file_name`
    - `log_file_path` does not override `log_file_mode` (`"write"`, `"append"`, or `"timestamped"`)
    - `log.output_dir_path` is set to the parent of `log_file_path`
    

Loguru Integration
------------------
- Logduo uses Loguru as its underlying file-sink engine.

- The following Loguru sink options can be passed through `log.configure()`:
  - `rotation`: start a new log file when a size/time rule is met.
      Example: `rotation="10 MB"` or `rotation="1 week"`.
      Use `rotation="off"` for no rotation (default = `"off"`).
  - `retention`: remove older rotated log files when a retention rule is met.
      Example: `retention="14 days"` or `retention=5`.
      This applies to rotated files, not to Logduo run-directory pruning (default = `"off"`).
  - `compression`: compress rotated log files.
      Example: `compression="zip"`.
      This applies to rotated files, not the active log file (default = `"off"`).
  - `enqueue`: write logs through a background queue.
      Useful for thread/process safety (default = `True`).
  - `catch`: catch logging errors instead of letting them crash the program (default = `True`).
  - `backtrace`: show extended traceback context for exceptions (default = `False`).
  - `diagnose`: include extra variable/context information in exception tracebacks (default = `False`).

- Logduo performs message formatting, wrapping, routing, session management,
  and Rich integration before messages reach Loguru.

- Use `log.new_logger()` when you want a normal Logduo-managed extra log file.

- Use `log.new_loguru_sink()` when you want direct Loguru control, such as:
  - using custom Loguru filters
  - adding extra Loguru sinks
  - sending selected events to separate destinations
  - passing options directly to `logger.add()`

- Sinks added with `log.new_loguru_sink()` are advanced/pass-through sinks.
  They are not managed like standard Logduo main logs or `new_logger()` files.


Console compatibility
--------------------------
- Logduo supports modern Unicode-capable terminals on Windows, macOS, and Linux. 
- Full Rich console output requires a Unicode-capable output stream. 
- Restricted legacy encodings such as Windows-1252 may not support all Rich formatting. 
- Log files are written as UTF-8.

  
Quality Assurance
-----------------
Logduo is validated using:
- pytest, with over 500 individual tests
- Ruff
- mypy
- Vulture
