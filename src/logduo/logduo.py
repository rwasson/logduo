"""
logduo.py

Public API layer for Logduo.

Provides:
- session lifecycle management
- logging entry points
- custom levels
- user sinks (new_logger)
- Loguru sink integration

Most implementation lives in internal modules.
See README.md for more details.

Last edited: 2026-6-13
"""

from __future__ import annotations

import atexit
import os
from collections import defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

from rich.console import Console

from logduo.internals.artifacts.export_logduo_docs import _export_logduo_docs
from logduo.internals.engine.active_duo_registry import _get_active_duo
from logduo.internals.engine.close_session import _close_session
from logduo.internals.engine.level_entry import _exception_entry, _level_entry
from logduo.internals.engine.new_level import _create_custom_level_label
from logduo.internals.engine.runtime_classes import RuntimeRecord
from logduo.internals.engine.start_session import _start_session
from logduo.internals.engine.user_sink_call_adapter import UserSinkCallAdapter
from logduo.internals.session_config.session_config_classes import (
    _build_session_config_class_instance,
    ArgSourceRecord,
    SessionConfig,
)
from logduo.internals.session_config.session_config_spec import DEFAULTS
from logduo.internals.session_config.session_constants import (
    _NOT_GIVEN,
    _NotGiven,
    _VALID_LEVELS,
    LogFileModeType,
    PrefixType,
)
from logduo.internals.sinks.new_loguru_sink import _initialize_new_loguru_sink
from logduo.internals.sinks.user_sink_log import _initialize_user_sink

_PID_INSTANCE_COUNTER: defaultdict[int, int] = defaultdict(int)


class Duo:
    """
    Most users should use the shared instance:
        from logduo import log

    Independent Duo instances may also be created:
        from logduo import Duo
        metrics = Duo()

    Notes
    -----
        - Each Duo instance maintains independent session state.
        - All Duo instances share the global Loguru backend.
        - Process IDs may be included in logging output when enabled.
    """

    def __init__(self) -> None:

        # --- StartupConfig ---
        # SessionConfig-shaped object populated from DEFAULTS.
        # Not yet fully resolved (e.g., console_theme_dict = {}).
        _startup_config = _build_session_config_class_instance(DEFAULTS.copy())
        self._startup_config: SessionConfig = _startup_config

        # --- SessionConfig (immutable) ---
        # Replaced in _start_session() with the fully resolved session config.
        # Some fields intentionally retain semantic values such as "auto"
        # (e.g. log_header/log_footer) and are resolved later during emission.
        self.session_config: SessionConfig = _startup_config
        self._arg_source_record: ArgSourceRecord = ArgSourceRecord()

        # --- RuntimeRecord ---
        # Contains fields populated during runtime
        # (e.g., event_count, paths, session state).
        # See runtime_classes.py for RuntimeRecord and related runtime classes.
        self._runtime: RuntimeRecord = RuntimeRecord()

        # --- Lifecycle flags ---
        self._initialized: bool = False
        self._console: Console | None = None
        self._atexit_registered: bool = False
        self._warned_already_configured: bool = False
        self._auto_configured: bool = False


    # === Public API (User-Facing Methods) =====================================

    # --- configure() ----------------------------------------------------------
    def configure(self, **configure_args: Any) -> SessionConfig:
        """
        Purpose
        ------
        Optionally configure the logging session.

        Configuration values are loaded in the following order:
            1. Built-in defaults
            2. [tool.logduo] settings from pyproject.toml (if detected)
            3. log.configure() arguments

        Call log.configure() before emitting the session's first log message.

        Example
        --------
        1. Basic setup (use default/toml configuration settings only):
            import os
            from logduo import log
            os.chdir("/desired/project/root")
            log("hello world")

        2. Override selected default configuration settings:
            import os
            from logduo import log
            os.chdir("/desired/project/root")
            log_dir_path = "/absolute/path/to/logs"
            log.configure(
                log_dir_path=log_dir_path,   # set custom path to log dir
                write_config_table=False,      # no config_table.txt
            )
            log("hello world")

        3. Use a custom Rich session header and/or footer in console and/or log:
           Note: "off" will suppress the default header/footer

            custom_log_header = (
                "[blue]═══ Analysis Run ═══[/blue] \\n"
                "[blue]Project:[/blue] Example Project"
            )
            log.configure(log_header=custom_log_header)
            log("hello world")


        4. Inside imported scripts, do not call log.configure() again:
            # inside imported script
            from logduo import log
            log = log.join()
            log("hello world from inside my_imported_script.py")

        Notes
        -----
        - Change to current working directory (cwd) before starting a log session.
            Logduo uses cwd to determine the default location of:
                - log files
                - artifact files (e.g., config_table.txt)
                - pyproject.toml (optional)
        - pyproject.toml configuration is optional. To configure Logduo via TOML:
              [tool.logduo]
              log_verbosity = 3
              keep = 3
              console_theme = "light"
        - After a logging session has started, later calls to log.configure()
            are ignored. To start a new logging session:
                log.close()      # close current logging session
                log.configure()  # start new logging session
        - To view the active session configuration:
                - open config_table.txt (which also displays descriptions and allowed values)
                - log(text_table(log.session_config))


        """
        if self._initialized:
            if not self._warned_already_configured:
                self._warned_already_configured = True

                # --- build warning message -----------------------------------
                if self._auto_configured:
                    warning_msg = (
                        "log.configure() called after a log level statement, "
                        "e.g., log.warning(msg).\n"
                        "    Configuration settings are set to defaults "
                        "for this session.\n"
                        "    To change settings: call log.close(), "
                        "then call log.configure()."
                    )
                else:
                    warning_msg = (
                        "log.configure() called more than once.\n"
                        "    Only the first call is used.\n"
                        "    To change settings: call log.close(), "
                        "then call log.configure() again."
                    )

                # --- emit warning --------------------------------------------
                _level_entry(
                    self,
                    warning_msg,
                    level="WARNING",
                    label="WARNING",
                    no_prefix=False,
                    log_wrap_width="off",
                    console_style="warning",
                    event_type="system_warning",
                )
            return self.session_config
        return self._initialize_session(configure_args=configure_args)

    # --- export_logduo_docs() ------------------------------------------------------
    def export_logduo_docs(self, path: str | Path | None = None) -> None:
        """
        Purpose
        -------
        Create a local copy of bundled Logduo documentation.

        Location
        --------
        If path is provided:
            Documentation is written to the specified directory.

        If path is None:
            Documentation is written alongside the logs directory to:
                <project_root>/logduo_docs

        Creates:
            logduo_docs/
                README.txt
                examples/
                    console_rendering.py
                    data_analysis.py
                    first_script.py
                    math_report_notation.py
                    nested_parent_script.py
                    nested_child_script.py

        Existing files are preserved and are not overwritten.

        Example
        -------
            from logduo import log
            log.export_logduo_docs()
            log.export_logduo_docs("~/Desktop/logduo_docs")

        Note
        ----
        Documentation files are not included in the session footer and
        are not tracked as session-generated artifacts.
        """

        _export_logduo_docs(self, path=path)

    # --- join() ---------------------------------------------------------------
    # noinspection PyMethodMayBeStatic
    def join(self) -> Duo:
        """
        Purpose
        -------
        Continue the current logging session from inside an imported script.

        Example
        -------
        1. inside imported script, my_imported_script.py:
            from logduo import log
            log = log.join()
            log("hello world, called from inside my_imported_script.py")
            mylog = log.new_logger("my_imported_script",
                                    to_console=True,
                                    to_main_log=False)
            mylog("hello world, visible in console and my_imported_script.log")

        2. interactive session (using default configuration settings):
            from pathlib import Path
            from logduo import log, run
            log("hello world from interactive session")
            my_script_path = Path("/absolute/path/to/my_script.py")
            run(my_script_path)

        Notes
        -----
        - Imported scripts execute only once per Python session.
        - To rerun an imported script after editing it:
                from logduo import run
                run("my_imported_script")
        - For additional details:
                help(run)

        """
        active_duo = _get_active_duo()

        if active_duo is None:
            raise RuntimeError(
                "No active logduo session exists.\n\n"
                "log.join() can only attach to an existing session created by "
                "log.configure() inside a parent script or an interactive session.\n\n"
            )
        return active_duo

    # --- new_logger() -----------------------------------------------------------
    def new_logger(
        self,
        target: str | Path,
        *,
        # routing
        to_console: bool | _NotGiven = _NOT_GIVEN,
        to_main_log: bool | _NotGiven = _NOT_GIVEN,
        log_verbosity: int | _NotGiven = _NOT_GIVEN,
        # file system
        log_file_mode: str | LogFileModeType | _NotGiven = _NOT_GIVEN,
        # advanced formatting
        log_prefix: PrefixType | _NotGiven = _NOT_GIVEN,
        log_wrap_width: int | str | _NotGiven = _NOT_GIVEN,
        log_header: str | _NotGiven = _NOT_GIVEN,
        log_footer: str | _NotGiven = _NOT_GIVEN,
    ) -> UserSinkCallAdapter:
        """
        Purpose
        -------
        Create a dedicated output file for reports, results,
        assignments, exports, or other content that should remain
        separate from the main session log.

        Example
        -------
        1. The returned callable report() writes messages to assignment_1.log
           (calculation and testing messages can be confined to main log):
            report = log.new_logger("assignment_1", to_console=True, to_main_log=True)
            report("Question 1 answer:")

        2. Create a dedicated log file for an imported or nested script.

                child_log = log.new_logger("child")
                child_log("Processing dataset A")
                child.log contains only messages from the child script.

            This is useful when a parent script or interactive session
            calls a child script and the child script should maintain
            its own log file.

        Required argument
        -----------------
        target : str | Path

            - Absolute path:
                treated as full log file path (must include filename + extension)
                The new log file is saved to this path.

            - Otherwise:
                treated as log file name (".log" added if missing)

                <output_dir_path> is derived from current session
                configuration settings, and the new log file is saved to:
                    <output_dir_path>/<name>.log

        Optional arguments
        ------------------
        to_console : bool
            Also display messages in console output.
        to_main_log : bool
            Also mirror messages in the session's main log file.
        log_verbosity : Literal[1, 2, 3]
            Override main log's verbosity level for new log file:
                - 1 = quiet       (Levels in log: ERROR, CRITICAL, WARNING)
                - 2 = standard    (Levels in log: quiet + SUCCESS, INFO)
                - 3 = verbose     (Levels in log: standard + DEBUG, TRACE)
            - If not specified, log_verbosity inherits the session setting.
            - If the session setting uses log_verbosity=0, new_logger()
                falls back to log_verbosity=2.


        Additional per-logger overrides
        -------------------------------
        The following optional arguments override the corresponding
        global configuration settings for this logger only:
            - log_prefix
            - log_wrap_width
            - log_header
            - log_footer

        Refer to config_table.txt for detailed descriptions of
        global configuration settings and allowed values.

        Notes
        -----
            - Each logger writes to its own dedicated log file.
            - Messages may also be mirrored to console and/or the main log file.
            - Logduo's per-message arguments are still available for new loggers.
                  Example:
                        report(
                            "message",
                            log_wrap_width=120,
                            no_prefix=True,
                            console_style="blue",
                        )
        """
        # NOTE: internally new_logger is called user_sink (to match main_sink)
        # _initialize_user_sink() calls new_logger_args_resolver(),
        # and stores resolved UserSinkConfig (defined in runtime_classes.py)

        self._ensure_initialized()

        new_logger_args = {
            # identity, internal name is sink
            "sink": target,
            # routing
            "to_console": to_console,
            "to_main_log": to_main_log,
            "log_verbosity": log_verbosity,
            # file system
            "log_file_mode": log_file_mode,
            # formatting
            "log_prefix": log_prefix,
            "log_wrap_width": log_wrap_width,
            "log_header": log_header,
            "log_footer": log_footer,
        }

        sink_adapter = _initialize_user_sink(duo=self, new_logger_args=new_logger_args)

        return sink_adapter


    # --- new_loguru_sink() ----------------------------------------------------
    def new_loguru_sink(
        self,
        sink: str | Path,
        *,
        file_mode: str | LogFileModeType | _NotGiven = _NOT_GIVEN,
        **kwargs: Any,
    ) -> int | None:
        """
        Purpose
        -------
        Attach a native Loguru sink via loguru.logger.add().

        Logduo resolves and manages file paths before attaching the sink.
        All logging behavior after attachment is controlled by Loguru.

        Unlike log.new_logger(), this method does not create a new
        logger. It only adds a new Loguru sink destination.

        Example
        -------
        1. Capture DEBUG+ messages:
            log.new_loguru_sink(
                "debug.log",
                level="DEBUG",
            )

        2. Capture INFO+ messages from the "report" sink only (no DEBUG or TRACE):.
            log.new_loguru_sink(
                "report_summary.log",
                level="INFO",
                filter=lambda r: r["extra"].get("sink_name") == "report",
            )

        Required argument
        -----------------
        sink : str | Path

            - Absolute path:
                treated as full file path (must include filename + extension)

            - Otherwise:
                treated as log file name (".log" added if missing)

                The file is created in the current session's output directory.

        Optional arguments
        ------------------
        file_mode : {"append", "write", "timestamped"}
            Controls file initialization behavior:
                - "append"      -> preserve existing contents
                - "write"       -> overwrite existing contents
                - "timestamped" -> append timestamp to filename

        **kwargs
            Passed directly to loguru.logger.add().
            Logduo validates and forwards supported Loguru add()
            arguments for the currently supported Loguru version.

            This includes advanced features such as filters,
            custom formats, rotation, retention, compression,
            serialization, and callable hooks.

        Returns
        -------
        int | None
            Loguru sink id returned by loguru.logger.add().
            This identifier may be useful for debugging, inspection,
            or future sink-management operations.

        Notes
        -----
            - Parent directories are created automatically.
            - Duplicate file paths are rejected.
            - Created files are tracked for session reporting.
            - Logduo formatting, headers, footers, wrapping,
              verbosity filtering, and routing rules are not applied.
            - Messages are emitted according to normal Loguru behavior.

        """
        self._ensure_initialized()

        return _initialize_new_loguru_sink(self, sink, file_mode=file_mode, **kwargs)

    # --- new_level() -------------------------------------------------------
    def new_level(
            self,
            label: str,
            *,
            console_style: str | _NotGiven = _NOT_GIVEN,
            level: str  = "INFO",
    ) -> Callable[..., None]:
        """
        Purpose
        -------
        Create a custom labeled logging function (e.g., TIP, NOTE).

        Example
        -------
        1. Custom label treated as level = INFO
            log.new_level(
                "TIP",
                console_style="purple",
            )
            log.tip("Example tip message")

        2. Custom label treated as level = CRITICAL
            log.new_level(
                "ANNOUNCE",
                console_style="cyan",
                level="CRITICAL",
            )
            log.announce(
                "Uses CRITICAL gating behavior for verbosity filtering"
            )

        3. Conditional usage
            SHOW_NOTES = True
            log.new_level(
                "NOTE",
                console_style="purple",
            )
            def log_note(msg):
                if SHOW_NOTES:
                    log.note(msg)
            log_note("Example note message")

        Required arguments
        ------------------
        label : str
            Display label shown in console and log output.

        console_style:
            Rich style string.
            Example: "italic blue", "bold red", "underline"

        Optional arguments
        ------------------
        level : str
            Controls verbosity gating and Loguru level routing.
            Default: "INFO"

        Notes
        -----
            - Reserved level names (INFO, WARNING, ERROR, etc.)
              cannot be used as custom labels.
            - Custom labels behave like their assigned level for
              verbosity filtering and Loguru integration.
        """
        return _create_custom_level_label(
            self,
            label,
            level=level,
            console_style=console_style,
        )


    # --- main_log_file_path() -------------------------------------------------
    @property
    def main_log_file_path(self) -> Path | None:
        """
        Purpose
        -------
        Absolute path to the main log file for the current session.

        Example
        -------
            log_file_path = log.main_log_file_path
            log.close()

            if log_file_path:
                print(f"Name of log file created: {Path(log_file_path).name}")

        Returns
        -------
        Path | None

        """
        return self._runtime.main_sink_log_file_path_abs


    # --- output_dir_path() ----------------------------------------------------
    @property
    def output_dir_path(self) -> Path | None:
        """
        Purpose
        -------
        Absolute directory where the current session writes file output.

        Example
        -------
        1. Save a matplotlib figure alongside log files
            import matplotlib.pyplot as plt
            fig, ax = plt.subplots()
            ax.plot([1, 2, 3], [1, 4, 9])

            if log.output_dir_path:
                fig_path = log.output_dir_path / "figure1.png"
                fig.savefig(fig_path)
                log(f"Saved figure to {fig_path.name}" )

        Returns
        -------
        Path | None
            Path to the current session's output directory.

        Notes
        -----
            - Does not create directories.
            - Safe to combine with custom filenames when saving:
                - plots
                - CSV files
                - reports
                - exported artifacts

        """
        return self._runtime.main_sink_log_dir_path_abs




    # --- close() --------------------------------------------------------------
    def close(self) -> None:
        """
        Purpose
        -------
        Optionally manually close the logging session.

        Example
        -------
        1. Basic usage
            log.close()

        Notes
        -----
            - Performs final cleanup:
                - writes per-sink footers
                - emits console footer (if enabled)
                - writes JSONL session_end record (if enabled)
                - emits prune summary message (if applicable)
            - If the session was started by a script,
              log.close() is called automatically at script exit.
            - After log.close(), a new session may be started with
              log.configure() or by emitting another log message.

        """
        _close_session(self)


    # === Levels ===============================================================
    # NOTE:
    # Standard log level methods are intentionally defined explicitly
    # (instead of relying solely on __getattr__) to preserve:
    #     - IDE autocomplete
    #     - per-level docstrings/help()
    #     - beginner discoverability
    #     - compatibility with limited editor environments
    #
    # __getattr__ remains responsible for:
    #     - dynamic custom levels
    #     - fallback level resolution to INFO

    # --- exception (ERROR + Traceback ) ---
    def exception(
            self,
            message: object | None = None,
            **kwargs: Any,
    ) -> None:
        """
        Purpose
        -------
        Log an error message and the active traceback.

        Displays:
            - the user-provided error message
            - traceback block (detail depends on verbosity level)


        Example
        -------
        1. Basic exception logging
            try:
                risky_operation()
            except Exception:
                log.exception("Operation failed")

        2. Override console style and wrapping for this message only
            try:
                risky_operation()
            except Exception:
                log.exception(
                    "Operation failed",
                    console_style="bold red",
                    log_wrap_width=120,
                )

        Optional per-message arguments
        ------------------------------
        no_prefix : bool
            Suppress prefix for this message only.
        console_style : str
            Apply Rich console styling to this message only.
            Example: "italic blue", "bold red", "underline"
        log_wrap_width : int | "off"
            Override log wrapping width for this message only.

        """

        _exception_entry(self, message, **kwargs)

    # --- critical()------------------------------------------------------------
    def critical(
        self,
        message: object,
        *,
        no_prefix: bool | _NotGiven = _NOT_GIVEN,
        console_style: str | _NotGiven = _NOT_GIVEN,
        log_wrap_width: int | str | _NotGiven = _NOT_GIVEN,
        **kwargs: Any,
    ) -> None:
        """
        Purpose
        -------
        Log a critical error message.
        Shown if verbosity level >=  1.

        Example
        -------
        1. Basic usage
            log.critical("System failure detected")

        2. Override styling for this message only
            log.critical("System failure detected", console_style="bold red")

        Optional per-message arguments
        ------------------------------
        no_prefix : bool
            Suppress prefix for this message only.
        console_style : str
            Apply Rich console styling to this message only.
            Example: "italic blue", "bold red", "underline"
        log_wrap_width : int | "off"
            Override log wrapping width for this message only.

        """
        _level_entry(
            self,
            message=message,
            level="CRITICAL",
            no_prefix=no_prefix,
            console_style=console_style,
            log_wrap_width=log_wrap_width,
            **kwargs,
        )

    # --- error()---------------------------------------------------------------
    def error(
        self,
        message: object,
        *,
        no_prefix: bool | _NotGiven = _NOT_GIVEN,
        console_style: str | _NotGiven = _NOT_GIVEN,
        log_wrap_width: int | str | _NotGiven = _NOT_GIVEN,
        **kwargs: Any,
    ) -> None:
        """
        Purpose
        -------
        Log an error message.
        Shown if verbosity level >= 1 .

        Example
        -------
        1. Basic usage
            log.error("file path not detected")

        2. Override styling for this message only
            log.error("file path not found", console_style="red")

        Optional per-message arguments
        ------------------------------
        no_prefix : bool
            Suppress prefix for this message only.
        console_style : str
            Apply Rich console styling to this message only.
            Example: "italic blue", "bold red", "underline"
        log_wrap_width : int | "off"
            Override log wrapping width for this message only.

        """
        _level_entry(
            self,
            message=message,
            level="ERROR",
            no_prefix=no_prefix,
            console_style=console_style,
            log_wrap_width=log_wrap_width,
            **kwargs,
        )

    # --- warning() ------------------------------------------------------------
    def warning(
        self,
        message: object,
        *,
        no_prefix: bool | _NotGiven = _NOT_GIVEN,
        console_style: str | _NotGiven = _NOT_GIVEN,
        log_wrap_width: int | str | _NotGiven = _NOT_GIVEN,
        **kwargs: Any,
    ) -> None:
        """
        Purpose
        -------
        Log a warning message.
        Shown if verbosity level >= 1.

        Example
        -------
        1. Basic usage
            log.warning("name truncated")

        2. Override styling for this message only
            log.warning("name truncated", console_style="orange")

        Optional per-message arguments
        ------------------------------
        no_prefix : bool
            Suppress prefix for this message only.
        console_style : str
            Apply Rich console styling to this message only.
            Example: "italic blue", "bold red", "underline"
        log_wrap_width : int | "off"
            Override log wrapping width for this message only.

        """
        _level_entry(
            self,
            message=message,
            level="WARNING",
            no_prefix=no_prefix,
            console_style=console_style,
            log_wrap_width=log_wrap_width,
            **kwargs,
        )

    # --- info()----------------------------------------------------------------
    def info(
        self,
        message: object,
        *,
        no_prefix: bool | _NotGiven = _NOT_GIVEN,
        console_style: str | _NotGiven = _NOT_GIVEN,
        log_wrap_width: int | str | _NotGiven = _NOT_GIVEN,
        **kwargs: Any,
    ) -> None:
        """
        Purpose
        -------
        Log an information message.
        Shown if verbosity level >= 2.

        Example
        -------
        1. Basic usage
            log("hello world")

        2. Override styling for this message only
            log("hello world", console_style ="italic blue")

        Optional per-message arguments
        ------------------------------
        no_prefix : bool
            Suppress prefix for this message only.
        console_style : str
            Apply Rich console styling to this message only.
            Example: "italic blue", "bold red", "underline"
        log_wrap_width : int | "off"
            Override log wrapping width for this message only.

        """
        _level_entry(
            self,
            message=message,
            level="INFO",
            no_prefix=no_prefix,
            console_style=console_style,
            log_wrap_width=log_wrap_width,
            **kwargs,
        )

    # --- success()-------------------------------------------------------------
    def success(
        self,
        message: object,
        *,
        no_prefix: bool | _NotGiven = _NOT_GIVEN,
        console_style: str | _NotGiven = _NOT_GIVEN,
        log_wrap_width: int | str | _NotGiven = _NOT_GIVEN,
        **kwargs: Any,
    ) -> None:
        """
        Purpose
        -------
        Log a success message.
        Shown if verbosity level >= 2.

        Example
        -------
        1. Basic usage -
            log.success("Completed round 1")

        2. Override styling for this message only
            log.success("Completed round 1", console_style ="green")

        Optional per-message arguments
        ------------------------------
        no_prefix : bool
            Suppress prefix for this message only.
        console_style : str
            Apply Rich console styling to this message only.
            Example: "italic blue", "bold red", "underline"
        log_wrap_width : int | "off"
            Override log wrapping width for this message only.

        """
        _level_entry(
            self,
            message=message,
            level="SUCCESS",
            no_prefix=no_prefix,
            console_style=console_style,
            log_wrap_width=log_wrap_width,
            **kwargs,
        )

    # --- debug() --------------------------------------------------------------
    def debug(
        self,
        message: object,
        *,
        no_prefix: bool | _NotGiven = _NOT_GIVEN,
        console_style: str | _NotGiven = _NOT_GIVEN,
        log_wrap_width: int | str | _NotGiven = _NOT_GIVEN,
        **kwargs: Any,
    ) -> None:
        """
        Purpose
        -------
        Log a debug message.
        Shown if verbosity level >= 3.

        If show_debug_source is enabled in the config, and if the message was generated
        in a script (i.e., not in interactive session), then the prefix of
        debug messages will display:
                file_name:line_number

        Example
        -------
        1. Basic usage -
            log.debug("made it to here")

        Optional per-message arguments
        ------------------------------
        no_prefix : bool
            Suppress prefix for this message only.
        console_style : str
            Apply Rich console styling to this message only.
            Example: "italic blue", "bold red", "underline"
        log_wrap_width : int | "off"
            Override log wrapping width for this message only.

        """
        _level_entry(
            self,
            message=message,
            level="DEBUG",
            no_prefix=no_prefix,
            console_style=console_style,
            log_wrap_width=log_wrap_width,
            **kwargs,
        )

    # --- trace() --------------------------------------------------------------
    def trace(
        self,
        message: object,
        *,
        no_prefix: bool | _NotGiven = _NOT_GIVEN,
        console_style: str | _NotGiven = _NOT_GIVEN,
        log_wrap_width: int | str | _NotGiven = _NOT_GIVEN,
        **kwargs: Any,
    ) -> None:
        """
        Purpose
        -------
        Log a trace message.
        Shown if verbosity level >= 3.


        Example
        -------
        1. Basic usage -
            i = 0
            while i < 100:
                log.trace(f"i = {i}")
                i += 1


        Optional per-message arguments
        ------------------------------
        no_prefix : bool
            Suppress prefix for this message only.
        console_style : str
            Apply Rich console styling to this message only.
            Example: "italic blue", "bold red", "underline"
        log_wrap_width : int | "off"
            Override log wrapping width for this message only.

        """
        _level_entry(
            self,
            message=message,
            level="TRACE",
            no_prefix=no_prefix,
            console_style=console_style,
            log_wrap_width=log_wrap_width,
            **kwargs,
        )

    # === Internal helpers =====================================================

    # --- Process ID (PID) management ------------------------------------------
    def _refresh_pid(self) -> None:
        """Detect process forks and refresh PID/instance-bound state."""
        runtime = self._runtime
        cur = os.getpid()

        # --- First run OR fork detected ---
        if runtime.pid != cur:
            runtime.pid = cur

            # Assign per-PID instance index
            next_idx = _PID_INSTANCE_COUNTER.get(cur, 0) + 1
            _PID_INSTANCE_COUNTER[cur] = next_idx

            runtime.instance_index = next_idx



    # --- _ensure_initialized() ------------------------------------------------
    def _ensure_initialized(self) -> None:
        if self._initialized:
            return

        self._auto_configured = True
        try:
            self._initialize_session(configure_args={})
        except Exception as e:
            raise RuntimeError(
                "Logduo failed to initialize automatically. "
                "Call log.configure(...) once at the start of your logging session."
            ) from e


    # --- _initialize_session() ------------------------------------------------
    @property
    def initialized(self) -> bool:
        return self._initialized

    def _initialize_session(
            self,
            *,
            configure_args: dict[str, object] | None = None,
    ) -> SessionConfig:
        return _start_session(self, configure_args=configure_args)

    # --- __call__()  ----------------------------------------------------------
    def __call__(
        self,
        message: object,
        *args: object,
        no_prefix: bool | _NotGiven = _NOT_GIVEN,
        log_wrap_width: int | str | _NotGiven = _NOT_GIVEN,
        console_style: str | _NotGiven = _NOT_GIVEN,
        **kwargs: Any,
    ) -> None:
        """
        Convenience entrypoint: allows `log("message")` as shorthand
        for `log.info("message")`.

        Users should call explicit methods like `log.warning(...)`
        or `log.error(...)` when using a different level.

        NOTE:
            This method name (`__call__`) is Python-defined behavior.
            Do not rename.
        """
        if args:
            raise TypeError(
                "Logduo accepts a single positional message argument. "
                "Optional arguments must be passed by keyword "
                "(no_prefix, log_wrap_width, console_style)."
            )

        self.info(
            message=message,
            no_prefix=no_prefix,
            log_wrap_width=log_wrap_width,
            console_style=console_style,
            **kwargs,
        )

    # --- __getattr__() --------------------------------------------------------
    def __getattr__(self, name: str) -> Callable[..., None]:
        """
        Fallback handler for unresolved log methods/attributes.

        Behavior
        --------
            - If `name` matches a built-in log level (INFO, WARNING, etc.),
              returns a callable that routes messages through the logging
              pipeline.
            - If `name` matches a custom label created via log.new_level(),
              returns a callable that routes messages through the logging
              pipeline using the configured label and severity.
            - Otherwise, raises AttributeError.

        Notes
        -----
            - This method is invoked only when normal attribute lookup fails.
            - It provides dynamic support for log levels and custom labels.
            - exception() is implemented as a dedicated method and is
                therefore not resolved through __getattr__().
        """
        name_upper = name.upper()
        label_key = name.lower()
        valid_levels = _VALID_LEVELS

        # --- standard levels ---
        if name_upper in valid_levels:
            return lambda message, **kwargs: _level_entry(
                self, message=message, level=name_upper, label=name_upper, **kwargs
            )

        # --- custom labels ---
        if label_key in self._runtime.new_levels:
            try:
                label, _, level = self._runtime.new_levels[label_key]
            except Exception as exc:
                raise RuntimeError(
                    "LOGDUO INTERNAL ERROR: Invalid new_levels entry."
                ) from exc

            def _call(
                message: object,
                **kwargs: Any,
            ) -> None:
                _level_entry(self, message=message, level=level, label=label, **kwargs)

            return _call

        # --- error message ---
        raise AttributeError(
            f"Unknown Logduo method or attribute '{name}'\n"
            f"Level/label logging calls:\n"
            f"  critical(), error(), warning(), success(), info(), debug(), trace()\n"
            f"Special logging call:\n"
            f"  exception()  -> ERROR + traceback\n"
            f"Methods:\n"
            f"  configure(), close(), join()\n"
            f"  new_logger(), new_level(), new_loguru_sink()\n"
            f"Attributes:\n"
            f"  session_config, output_dir_path, main_log_file_path\n"
            f"For help: help(log.<method_name>)\n\n"
        )

    # --- _register_close_on_exit() --------------------------------------------
    def _register_close_on_exit(self) -> None:
        if not self._atexit_registered:
            atexit.register(self.close)
            self._atexit_registered = True


logduo = Duo()
