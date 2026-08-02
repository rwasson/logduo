Logduo
======
Easy logging and output management for Python scripts and interactive sessions.

Simple by default, configurable for advanced logging workflows.

Platforms: Tested through GitHub Actions on macOS, Windows, and Ubuntu.


Features
--------
- No setup required — safe defaults applied
- Manages output directories and log files automatically
- Provides `help()` documentation and actionable error messages
- Validates arguments to all Logduo methods and functions
- Safely prunes old run directories containing a Logduo marker file
- Generates optional session artifacts: `config_table.txt`, `config.json`
- Emits ANSI-styled and Rich output to console while preserving plain-text logs
- Creates dedicated log files via `new_logger()`
- Creates advanced pass-through Loguru sinks via `new_loguru_sink()`
- Creates custom logging levels via `new_level()`
- Supports nested scripts via `run()` and `log.join()`
- Captures JSONL event streams
- Reports log-generated files in console and log footers


Quick interactive session
---------------------------

    >>> from logduo import log, run
    >>> log("hello world")

    Logging started:  2026-07-31 17:28:27
    | INFO     | hello world

    >>> log.info("hello world again; INFO is the default logging level.")

    | INFO     | hello world again; INFO is the default logging level.

    >>> log.warning("The logging level 'WARNING' is displayed in orange on the console.")

    | WARNING  | The logging level 'WARNING' is displayed in orange on the console.

    >>> help(log.configure)
    >>> help(run)
    >>> log.close()
    ───────────────────────────────────────────────────────
    Logging ended:    2026-07-31 17:29:12 (duration 45 sec)
    Output directory:
        /Users/my_name/my_project/logs/session/run_2026_07_31__17_28_27
    Log-generated files in output directory:
        config_table.txt
        session.log

- If a log statement, such as `log("hello world")`, is called before `log.configure()`, 
  Logduo applies configuration settings from `[tool.logduo]` in `pyproject.toml`.  
- If `[tool.logduo]` settings are not provided, Logduo applies its own configuration defaults.
- `help()` output appears on the console only and is not written to log files.
   - Use focused calls such as `help(log.configure)` or `help(log.new_logger)`.
   - `help(log)` displays the complete logger API and is therefore lengthy.
- `log.close()` is required to end logging in interactive sessions

  
Key Logduo default configuration settings
-----------------------------------------
- `console_theme = "dark"`
- `console_wrap_width = 120` and `log_wrap_width = "off"`
- `console_verbosity = 3` and `log_verbosity = 3`
  - verbosity = 3, all logging levels emitted (including DEBUG and TRACE)
  - verbosity = 2, only CRITICAL, ERROR, WARNING, INFO, SUCCESS are emitted
  - verbosity = 1, only CRITICAL, ERROR, WARNING are emitted
  - verbosity = 0, output is suppressed
- `console_prefix = "level"` and `log_prefix = "timestamp"`
  - Prefix options layer cumulatively: `"off"`, `"level"`, `"timestamp"`, `"source"` 
  - Example prefix = `"source":   16:30:40.371 | WARNING  | example_2.py:382` 
- `log_dir_path = "auto"`
  - `"auto"` → 
     - If pyproject.toml is not detected: `log_dir_path` = current working directory / "logs"
     - If pyproject.toml is detected: `log_dir_path` = parent directory of pyproject.toml / "logs"
  - Other option: provide an explicit absolute log-directory path.
- `log_file_mode = "write"`
  - `"write"` → Existing log files are overwritten.
  - Other options: `"append"`, `"timestamped"` (adds timestamp to log file name before extension).
- `log_file_name = "auto"`
  - `"auto"` → 
     - If Logduo is initialized inside a script, `log_file_name` = <script_stem>.log
     - If Logduo is initialized in an interactive session, `log_file_name` = session.log
  - Other option: provide an explicit file name (".log" will be appended if no extension is given) 
- `log_file_layout = "run"`
  - `"run"`:    `log_dir_path/script_stem/run_yyyy_mm_dd__hh_mm_ss/log_file_name`
  - `"script"`: `log_dir_path/script_stem/log_file_name`
  - `"flat"`:   `log_dir_path/log_file_name`
  - If Logduo is initialized in an interactive session, script_stem = "session"
- `log_file_path = "auto"`
  - `"auto"` → the log file name and location are determined by
     `log_dir_path`, `log_file_name`, and `log_file_layout`.
  - Other option: provide an explicit log file path (overrides `log_dir_path`, `log_file_name`, 
    and `log_file_layout`)
- `keep = "off"`
  - Previous run directories are not pruned automatically.
  - If `keep` is set to a positive integer `n`, the newest `n` Logduo-marked run directories are 
    kept and older run directories are pruned.
- `write_config_table = True`
  - `config_table.txt` written to output directory (useful reference for all configuration settings).

    
Quick script with log.configure()
---------------------------------

    from pathlib import Path
    from logduo import log, run

    my_log_dir = Path.cwd() / "logs"

    log.configure(log_dir_path=my_log_dir, keep=3, console_theme="light")

    log("hello world")
    log(f"output directory path = {log.output_dir_path}")
    log(f"main log file path = {log.main_log_file_path}")

    log.export_logduo_docs()

    var = 3 * 3

    log.debug(f"made it here: var = {var}")

    output_dir_path = log.output_dir_path
    assert isinstance(output_dir_path, Path)     # Satisfy static type checkers.

    myplot_output_path = output_dir_path / "myplot.png"

    log.close()

- If `log.configure()` is called after logging has started or after a previous
  `log.configure()` call, a warning is issued and the new configuration is ignored.
- If Logduo is initialized inside a script, `log.debug()` includes the source (calling file name 
  and line number) at the start of each debug message unless disabled with: 

      `log.configure(show_debug_source=False)`.

- A logging session must be closed, and a new session started, to change Logduo settings. 
- Logging sessions in scripts close automatically during normal interpreter
  shutdown using best-effort cleanup.
- While not required, explicit `log.close()` is supported in scripts and is useful when subsequent 
  code needs the completed log files immediately.


Export Logduo docs: log.export_logduo_docs()
--------------------------------------------
Exports bundled documentation and example scripts to a local `logduo_docs/` directory.

Exported files include examples of advanced workflows:
- `README.txt`
- `examples/first_script.py`
- `examples/console_rendering.py`
- `examples/data_analysis.py`
- `examples/math_report_notation.py`
- `examples/script_parent.py`
- `examples/script_child.py`


Logduo Methods, Functions, and Properties
----------------------------------------
- Manage session:
  - `log.configure()`
  - `log.close()`

- Logging levels:
  - `log()` or `log.info()`
  - `log.trace()`
  - `log.debug()`
  - `log.success()`
  - `log.warning()`
  - `log.error()`
  - `log.critical()`
  - `log.exception()`  # Error message and traceback

- Create custom logging level:
  - `log.new_level()`  # Maps a custom display label to an existing severity level; default = "INFO"

- Create additional output:
  - `log.new_logger()`       # Logduo-managed extra log file
  - `log.new_loguru_sink()`  # Advanced Loguru sink
  - `log.export_logduo_docs()`

- Execute a nested script or importable module: 
   - Inside script_parent.py or interactive session: `run(<path to script_child.py>)`
   - Inside script_child.py: `log = log.join()`

- Access paths. 
    - log.output_dir_path
    - log.main_log_file_path

      These properties are `None` until Logduo is initialized by `log.configure()` or 
      a logging call such as `log("message")`.


Message Rendering
-----------------
- Strings without `\n`: Displayed inline with the prefix.
    - Console: Wrapped to `console_wrap_width`).
    - Log files: Wrapped only if `log_wrap_width` is set to a positive integer. Default is `"off"`.
- Strings containing `\n`: Displayed as block flush left below prefix. Line breaks are honored.
    - This preserves the full available line width for tables, panels, JSON, tracebacks, and other 
      structured content.
    - Use manual indenting or Rich `Padding` if indent behavior is desired:
  
           indent = "   "
           log(
              f"{indent}Step 1: Load data\n"
              f"{indent}Step 2: Clean data\n"
           ) 
- ANSI-styled strings and Rich `Text` objects are rendered on the console and written as plain text in log files.
- Other Rich objects, such as `Panel`, are rendered on the console but displayed as placeholders in log files. 
    - For more examples, use `log.export_logduo_docs()` and see `console_rendering.py`. 


Loguru Integration
------------------
- Logduo uses Loguru as its underlying file-sink engine.
- Logduo performs message formatting, wrapping, routing, session management,
  and Rich integration before messages reach Loguru.
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
- Use `log.new_logger()` when you want a normal Logduo-managed extra log file.
- Use `log.new_loguru_sink()` when you want direct Loguru control, such as:
  - using custom Loguru filters
  - adding extra Loguru sinks
  - sending selected events to separate destinations
  - passing options directly to `logger.add()`
- Sinks added with `log.new_loguru_sink()` are advanced pass-through sinks.
  Logduo manages their creation and session lifecycle, but messages sent directly
  through Loguru bypass normal Logduo formatting, wrapping, routing, headers, and footers.


Console compatibility
---------------------
- Logduo supports modern Unicode-capable terminals on Windows, macOS, and Linux.
- Some older or restricted terminals may not display every Rich character correctly.
- Log files are always written as UTF-8.
