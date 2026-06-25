"""
user_sink_call_adapter.py

Bound log-call adapter for user-created sinks.

Provides:
- standard log level methods
- custom label dispatch
- sink_name injection into _level_entry()

Acts as the public call surface returned by log.new_logger().

Last edited: 2026-5-27
"""
from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from logduo.logduo import Duo

from collections.abc import Callable

from logduo.internals.engine.level_entry import _exception_entry, _level_entry
from logduo.internals.session_config.session_constants import _NOT_GIVEN, _NotGiven


# --- class UserSinkCallAdapter ------------------------------------------------
class UserSinkCallAdapter:
    """Bind sink_name onto standard log call entry methods."""

    def __init__(self, duo: Duo, sink_name: str) -> None:
        self._duo = duo
        self._sink_name = sink_name

    # --- default call ---
    def __call__(self, message: object, **kwargs: Any) -> None:
        self.info(message, **kwargs)

    # --- level methods ---
    def exception(
        self,
        message: object,
        *,
        no_prefix: bool | _NotGiven = _NOT_GIVEN,
        log_wrap_width: int | str | _NotGiven = _NOT_GIVEN,
        console_style: str | _NotGiven = _NOT_GIVEN,
    ) -> None:
        _exception_entry(
            duo=self._duo,
            message=message,
            no_prefix=no_prefix,
            log_wrap_width=log_wrap_width,
            console_style=console_style,
            sink_name=self._sink_name,
        )

    def critical(
        self,
        message: object,
        *,
        no_prefix: bool | _NotGiven = _NOT_GIVEN,
        log_wrap_width: int | str | _NotGiven = _NOT_GIVEN,
        console_style: str | _NotGiven = _NOT_GIVEN,
    ) -> None:
        _level_entry(
            self._duo,
            message=message,
            level="CRITICAL",
            label="CRITICAL",
            no_prefix=no_prefix,
            log_wrap_width=log_wrap_width,
            console_style=console_style,
            sink_name=self._sink_name,
        )

    def error(
        self,
        message: object,
        *,
        no_prefix: bool | _NotGiven = _NOT_GIVEN,
        log_wrap_width: int | str | _NotGiven = _NOT_GIVEN,
        console_style: str | _NotGiven = _NOT_GIVEN,
    ) -> None:
        _level_entry(
            self._duo,
            message=message,
            level="ERROR",
            label="ERROR",
            no_prefix=no_prefix,
            log_wrap_width=log_wrap_width,
            console_style=console_style,
            sink_name=self._sink_name,
        )

    def warning(
        self,
        message: object,
        *,
        no_prefix: bool | _NotGiven = _NOT_GIVEN,
        log_wrap_width: int | str | _NotGiven = _NOT_GIVEN,
        console_style: str | _NotGiven = _NOT_GIVEN,
    ) -> None:
        _level_entry(
            self._duo,
            message=message,
            level="WARNING",
            label="WARNING",
            no_prefix=no_prefix,
            log_wrap_width=log_wrap_width,
            console_style=console_style,
            sink_name=self._sink_name,
        )

    def success(
        self,
        message: object,
        *,
        no_prefix: bool | _NotGiven = _NOT_GIVEN,
        log_wrap_width: int | str | _NotGiven = _NOT_GIVEN,
        console_style: str | _NotGiven = _NOT_GIVEN,
    ) -> None:
        _level_entry(
            self._duo,
            message=message,
            level="SUCCESS",
            label="SUCCESS",
            no_prefix=no_prefix,
            log_wrap_width=log_wrap_width,
            console_style=console_style,
            sink_name=self._sink_name,
        )

    def info(
        self,
        message: object,
        *,
        no_prefix: bool | _NotGiven = _NOT_GIVEN,
        log_wrap_width: int | str | _NotGiven = _NOT_GIVEN,
        console_style: str | _NotGiven = _NOT_GIVEN,
    ) -> None:
        _level_entry(
            self._duo,
            message=message,
            level="INFO",
            label="INFO",
            no_prefix=no_prefix,
            log_wrap_width=log_wrap_width,
            console_style=console_style,
            sink_name=self._sink_name,
        )

    def debug(
        self,
        message: object,
        *,
        no_prefix: bool | _NotGiven = _NOT_GIVEN,
        log_wrap_width: int | str | _NotGiven = _NOT_GIVEN,
        console_style: str | _NotGiven = _NOT_GIVEN,
    ) -> None:
        _level_entry(
            self._duo,
            message=message,
            level="DEBUG",
            label="DEBUG",
            no_prefix=no_prefix,
            log_wrap_width=log_wrap_width,
            console_style=console_style,
            sink_name=self._sink_name,
        )

    def trace(
        self,
        message: object,
        *,
        no_prefix: bool | _NotGiven = _NOT_GIVEN,
        log_wrap_width: int | str | _NotGiven = _NOT_GIVEN,
        console_style: str | _NotGiven = _NOT_GIVEN,
    ) -> None:
        _level_entry(
            self._duo,
            message=message,
            level="TRACE",
            label="TRACE",
            no_prefix=no_prefix,
            log_wrap_width=log_wrap_width,
            console_style=console_style,
            sink_name=self._sink_name,
        )

    def __getattr__(self, name: str) -> Callable[..., None]:
        label_key = name.lower()
        runtime = self._duo._runtime

        # --- custom label ---
        if label_key in runtime.new_levels:
            try:
                label, _, level = runtime.new_levels[label_key]
            except Exception as exc:
                raise RuntimeError(
                    f"LOGDUO INTERNAL ERROR: Invalid new_levels entry for '{label_key}'."
                ) from exc

            def _custom_call(
                message: object,
                *,
                no_prefix: bool | _NotGiven = _NOT_GIVEN,
                log_wrap_width: int | str | _NotGiven = _NOT_GIVEN,
                console_style: str | _NotGiven = _NOT_GIVEN,
            ) -> None:
                _level_entry(
                    self._duo,
                    message,
                    level=level,
                    label=label,
                    no_prefix=no_prefix,
                    log_wrap_width=log_wrap_width,
                    console_style=console_style,
                    sink_name=self._sink_name,
                )

            return _custom_call

        level = name.upper()

        def _level_call(
            message: object,
                *, no_prefix: bool | _NotGiven = _NOT_GIVEN,
                log_wrap_width: int | str | _NotGiven = _NOT_GIVEN,
                console_style: str | _NotGiven = _NOT_GIVEN,
        ) -> None:
            _level_entry(
                self._duo,
                message,
                level=level,
                label=level,
                no_prefix=no_prefix,
                log_wrap_width=log_wrap_width,
                console_style=console_style,
                sink_name=self._sink_name,
            )

        return _level_call
