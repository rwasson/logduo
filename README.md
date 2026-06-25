Logduo
======
Logging, console, and file management for Python.

Works in scripts and interactive sessions with no setup, but supports extensive customization.

Platform: Tested on macOS, Windows, and Ubuntu using Python 3.13.


Key Capabilities
-----------------
- Automatically manages output directories and log files
- Safely prunes old run sessions
- Creates dedicated log files via new_logger()
- Creates custom logging labels via new_level()
- Supports imported and nested scripts via log.join()
- Supports Rich and ANSI-styled console output
- Captures JSONL event streams (configurable)
- Generates session artifacts such as config_table.txt, config.json, and README.txt
- Provides extensive help() documentation and actionable error messages


Quick Start (in script or interactive session)
-----------------------------------------------
    from logduo import log

    log("hello world")
    log.warning("warning message")

- The first log statement automatically starts a session using defaults and [tool.logduo] settings in pyproject.toml (if available).
- By default, messages are sent to both console and a log file.
- By default, Logduo generates a log file and config_table.txt in a timestamped run directory.
- Paths of all Logduo-created files are listed in the default footer displayed
in the console and main log file.


Configure (Optional)
--------------------
    from logduo import log

    my_log_dir = Path("/absolute/path/to/my_log_dir")

    log.configure(log_dir_path=my_log_dir, console_verbosity=3)
    log("hello world")


Logduo Docs
-----------
- Example scripts demonstrating typical usage, Rich/ANSI rendering, 
run(), and log.join() are included with the package installation:

        first_script.py
        rich_and_ansi.py
        parent.py (imports parents_child.py)


- README.txt and example scripts and  can be saved to your project in the subdirectory /logduo_docs:

        log.export_logduo_docs()


Help
----
- Help is available for all Logduo methods and functions (displays in console only):

      help(log.configure)

- Help includes examples, argument descriptions, and usage notes.

    
Typical Workflows
----------------
- Debug session: By default, log.debug() includes the calling file name and line number at the start of each message. Disable with: log.configure(..., show_debug_source=False)

       from logduo import log
       log.configure(log_verbosity=3, console_verbosity=3)

       log.debug(f"made it here: var = {var}")

- Create additional log files (for dedicated output) if needed. Messages logged with rep() are recorded in report.log and optionally mirrored to console and/or main log file.

       rep = log.new_logger("report", to_console=True, to_main_log=False)
       rep("Question 1 answer:")

- Use the output directory to save plots, CSVs, reports, and other generated files

       myplot_output_path = log.output_dir_path / "myplot.png"

- Close the session (required in interactive sessions, optional in scripts)

       log.close()


Logduo Methods and Functions:  from logduo import log, run, text_table
----------------------------------------------------------------------
- Manage Sessions:
    - log.configure()
    - log.close()
    - log.join()


- Log Messages:
    - log.trace()
    - log.debug()
    - log.info() or log()
    - log.success()
    - log.warning()
    - log.error()
    - log.critical()
    - log.exception()  # ERROR + Traceback


- Create Additional Output Files:
    - log.export_logduo_docs()
    - log.new_logger()
    - log.new_loguru_sink()

    
- Create Custom Labels:
    - log.new_level()


- Access paths:
    - log.output_dir_path
    - log.main_log_file_path
  

- Utility Functions: 
    - run() - import/reload a child script from a parent script or interactive session
    - text_table() - create an ANSI-aware table string for printing or logging 
    
    

--------
Behavior
========


Prefixes
--------
- One prefix per log event.
- Console and log files have independent prefix settings: console_prefix, log_prefix
  - off → No prefix. Wrapped lines align flush left
  - level → Prefix shows level. Wrapped lines align under message.
  - timestamp → Prefix shows timestamp and level. Wrapped lines align under message.
  - source → Prefix shows timestamp, level and source. Wrapped lines align under source.
- Example console output: prefix="source", show_pid_in_console=True, console_wrap_width=80

  
        16:30:40.371 | WARNING  | example_2.py:382 -  (15408:i1) Logduo is designed for
                                  data scientists, researchers, students, and Python
                                  developers who want readable console output, organized
                                  log files, and minimal logging setup.
    

Message Rendering
-----------------
- Strings without '\n': Displayed inline with the prefix.
    - Console: Wrapped (line width = console_wrap_width).
    - Log files:  Wrapped only if log_wrap_width is set. Default = off.
- Strings containing '\n': Displayed as block flush left below prefix - line breaks honored
    - This preserves the full available line width for tables,
         panels, JSON, tracebacks, and other structured content.
    -  Manual padding or Rich padding can be used if indent behavior is desired:
  
           pad = " " * 4
           log(
              f"{pad}Step 1: Load data\n"
              f"{pad}Step 2: Clean data\n"
           )
    
- ANSI-styled strings are rendered on the console and written as plain text in log files.


Rich Integration
----------------
- Console: Rich objects are displayed as blocks flush left on the line(s) below the prefix.

    - Rich Text Example (with indent via Padding):

           log(Padding(Text("Step 1: \nStep 2: "), pad=(0, 0, 0, 27),))

            08:35:02.099 | INFO     |
                                      Step 1: 
                                    Step 2: 

    - Rich Panel Example (border box shown in blue on console):

            log(Panel("hello", border_style='blue', title='hello panel'))

            08:35:02.099 | INFO     |
            ┌───────┐
            │ hello │
            └───────┘

- Log: Rich Text objects are converted to plain text strings. Other objects are displayed via Rich placeholders.

    - Rich Text Example: Rich styles not displayed in log -  plain text only.

            log(Text("value = ") + Text.from_markup("[blue]hello[/blue]"))
  
            08:35:02.099 | INFO     |  value = hello

    - Rich Panel Example: Log file displays a Rich placeholder marker.

           log(Panel("hello", border_style='blue', title='hello panel' ))

           08:35:02.099 | INFO     | Padding(<rich.panel.Panel object at 0x10a396660>, (0,0,0,13))


Log File Naming and Location
----------------------------
- Log file name: 
    - If calling script is my_file.py, default log_file_name →  "my_file.log"
    - If calling script is not found, default log_file_name →  "session.log"
    - Custom log_file_name can be used: log.configure(log_file_name="my_name.ext")
  

- Default log file location:
    - log_root:
        - If pyproject.toml is not detected: log_root = current working directory
        - If pyproject.toml is detected: log_root = parent directory of pyproject.toml
    - log_dir_layout (default = run) sets log file location: 
        - run:     /log_root/logs/script_stem/run_yyyy_mm_dd__hh_mm_ss/log_file_name
        - script:  /log_root/logs/script_stem/log_file_name
        - flat:    /log_root/logs/log_file_name


- If log_dir_layout = "script" or "flat", consider log_file_mode = "timestamped":
  - script:  /log_root/logs/script_stem/log_file_name_stem_yyyy_mm_dd__hh_mm_ss.log
  - flat:    /log_root/logs/log_file_name_stem_yyyy_mm_dd__hh_mm_ss.log
  

- Additional notes on paths:  
  - If log_dir_path is provided, the log directory can be placed outside log_root.
  - If log_file_path is provided, it specifies the complete log file path.
       - log_file_path overrides log_dir_layout, log_dir_path and log_file_name
       - log_dir_path becomes the parent of log_file_path
       - log_file_path does not override log_file_mode ('write', 'append', 'timestamped')


Prune Run Directories
---------------------
If log_dir_layout = "run":
- Run directories containing the auto-generated .logduo_marker file are eligible for pruning.
- By default, the number of kept run directories = 10.
- The keep value can be changed: log.configure(..., keep = 3) 
- Directories older than the keep value are removed at the start of the session.

    
Loguru Integration
------------------
- Logduo uses Loguru to provide mature file-output infrastructure,
including:
  - log rotation
  - retention policies
  - compression
  - asynchronous/enqueued logging
  - sink lifecycle management
- Logduo performs all message formatting, wrapping, routing, session management,
and Rich integration before messages reach Loguru.

  
Quality Assurance
-----------------
Logduo is validated using:
- pytest (over 500 tests)
- Ruff
- mypy
- Vulture
