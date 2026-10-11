Logduo
======
Easy logging and output management for Python scripts and interactive sessions.

Simple by default, configurable for advanced logging workflows.

Platforms: Tested through GitHub Actions on macOS, Windows, and Ubuntu.


Features
--------
- No setup required — safe defaults applied
- Manages output directories and log files automatically
- Supports console-only logging without creating output directories or files
- Provides `help()` documentation and actionable error messages
- Validates arguments to all Logduo methods and functions
- Safely prunes old run directories containing a Logduo marker file
- Generates optional session artifacts: `config_table.txt`, `config.json`
- Emits ANSI-styled and Rich output to console while preserving plain-text logs
- Provides a utility to log/print plain-text tables from common Python data via `text_table()`
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
- If [tool.logduo] settings are not provided, Logduo applies its own configuration defaults.
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
  - verbosity = 0, output to that destination is suppressed
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
- `log.configure(<argument>=None)`
  - Explicit `None` resets that configuration argument to its built-in Logduo default.
  - This is useful when a script or package uses Logduo and needs to ensure the default value 
    is used, even if there is a project-level TOML setting.
    
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

    log(
        'Demo of logging line options: no_prefix=True, console_style="italic blue", '
        'left_indent=26, and log_wrap_width=80. '
        'Console wrapping is controlled separately by console_wrap_width '
        f'(current session value: {log.session_config.console_wrap_width}).',
        no_prefix=True,
        console_style="italic blue",
        left_indent=26,
        log_wrap_width=80,
    )

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

- Access output paths. 
    - log.output_dir_path
    - log.main_log_file_path

      These properties are `None` until Logduo is initialized by `log.configure()` or 
      a logging call such as `log("message")`.

      Resolving a path does not necessarily create the corresponding directory or file.
      Logduo creates output directories only when file output is actually needed.
  
- Use `text_table()` to log/print python data: `log(text_table(my_data))`
    - for more information, at interactive prompt: 
    
          from logduo import text_table
          help(text_table)
  
    - or check included example script: `console_rendering.py`.


Per-call line options
---------------------
Example: `log("hello", no_prefix=True, left_indent=4)`
- `no_prefix=True` suppresses the prefix for that logging call.
- `left_indent=n` adds `n` spaces before displayed message text.
  Wrapped continuation lines retain the requested indentation.
- `log_wrap_width=n` overrides log-file wrapping for that call.
  It does not change console wrapping.
- `console_style="..."` applies a Rich style to console output for that call.
    It does not affect plain-text log output.


Message Rendering
-----------------
- Simple strings and text-like Python objects:
    - Plain-text strings without `\n`, and Python objects with a useful text
      representation (such as dictionaries, lists, numbers, and custom objects),
      are displayed on the same line as the prefix in both the console and log.
    - Long text wraps beneath the start of the message.

- Multiline strings (strings containing `\n`):
    - Displayed below the prefix in both the console and log, preserving the
      user-supplied line layout and maximum available line width.
    - Long lines may wrap in the console to fit the console width.
    - In log files, the user-supplied line breaks are preserved.

- Rich Text objects
    - Displayed flush left below the prefix in the console, 
      unless `left-indent` is applied or Rich's Padding() is used.
    - Written as plain text in log files.

- Other Rich objects, such as `Panel`, and `Table`:
    - Displayed flush left below the prefix in the console, unless Rich's 
      Padding() is used (not eligible for `left-indent`).
    - Represented by placeholders in log files.

- Other objects, such as images and figures:
    - Displayed using placeholder or text representations in the console and log.

- For more examples, use `log.export_logduo_docs()` and see
  `console_rendering.py`.


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
