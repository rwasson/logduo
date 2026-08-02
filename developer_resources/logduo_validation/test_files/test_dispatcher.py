"""
test_dispatcher.py

Last edited: 2026-06-11
"""

import pytest

from logduo.internals.engine.dispatcher import (
    _get_cfr_by_kind,
    _needs_callsite,
    _should_route_to_sink,
)

# === Fake Classes ===================================================================

class FakeCFR:

    def __init__(
        self,
        *,
        file_kind,
        log_prefix="timestamp",
    ):
        self.file_kind = file_kind
        self.log_prefix = log_prefix


class FakeUserSinkConfig:
    def __init__(
        self,
        *,
        to_console=True,
        to_main_log=True,
        log_verbosity=2,
    ):
        self.to_console = to_console
        self.to_main_log = to_main_log
        self.log_verbosity = log_verbosity


class FakeRuntime:
    def __init__(self, cfr_list):
        self._cfr_list = cfr_list

    def _get_file_list_in_cfr(self):
        return self._cfr_list


class FakeSessionConfig:
    def __init__(self):
        self.write_jsonl = False
        self.console_prefix = "timestamp"
        self.show_debug_source = False
        self.console_verbosity = 2
        self.log_verbosity = 2


class FakeDuo:
    def __init__(self):
        self.session_config = FakeSessionConfig()


# === _get_cfr_by_kind() ======================================================

# --- test_01_get_cfr_by_kind_found() -----------------------------------------
def test_01_get_cfr_by_kind_found():

    runtime = FakeRuntime([
        FakeCFR(file_kind="main_sink_log"),
        FakeCFR(file_kind="jsonl"),
    ])

    result = _get_cfr_by_kind(runtime, "jsonl")

    assert result.file_kind == "jsonl"


# --- test_02_get_cfr_by_kind_missing() ---------------------------------------
def test_02_get_cfr_by_kind_missing():

    runtime = FakeRuntime([])

    assert _get_cfr_by_kind(runtime, "jsonl") is None


# === _needs_callsite() ========================================================

# --- test_03_needs_callsite_jsonl() ------------------------------------------
def test_03_needs_callsite_jsonl():

    duo = FakeDuo()
    duo.session_config.write_jsonl = True

    assert (
        _needs_callsite(
            duo,
            level="INFO",
            main_sink_log_cfr=None,
            jsonl_cfr=FakeCFR(file_kind="jsonl"),
            user_sink_log_cfr=None,
            user_sink_config=None,
        )
        is True
    )


# --- test_04_needs_callsite_console_source_prefix() --------------------------
def test_04_needs_callsite_console_source_prefix():

    duo = FakeDuo()
    duo.session_config.console_prefix = "source"

    assert (
        _needs_callsite(
            duo,
            level="INFO",
            main_sink_log_cfr=None,
            jsonl_cfr=None,
            user_sink_log_cfr=None,
            user_sink_config=None,
        )
        is True
    )


# --- test_05_needs_callsite_main_log_source_prefix() -------------------------
def test_05_needs_callsite_main_log_source_prefix():

    assert (
        _needs_callsite(
            FakeDuo(),
            level="INFO",
            main_sink_log_cfr=FakeCFR(
                file_kind="main_sink_log",
                log_prefix="source",
            ),
            jsonl_cfr=None,
            user_sink_log_cfr=None,
            user_sink_config=None,
        )
        is True
    )


# --- test_06_needs_callsite_user_sink_source_prefix() ------------------------
def test_06_needs_callsite_user_sink_source_prefix():

    assert (
        _needs_callsite(
            FakeDuo(),
            level="INFO",
            main_sink_log_cfr=None,
            jsonl_cfr=None,
            user_sink_log_cfr=FakeCFR(
                file_kind="user_sink_log",
                log_prefix="source",
            ),
            user_sink_config=None,
        )
        is True
    )


# --- test_07_needs_callsite_debug_source_enabled() ---------------------------
def test_07_needs_callsite_debug_source_enabled():

    duo = FakeDuo()
    duo.session_config.show_debug_source = True
    duo.session_config.console_verbosity = 3

    assert (
        _needs_callsite(
            duo,
            level="DEBUG",
            main_sink_log_cfr=None,
            jsonl_cfr=None,
            user_sink_log_cfr=None,
            user_sink_config=None,
        )
        is True
    )


# --- test_08_needs_callsite_not_needed() -------------------------------------
def test_08_needs_callsite_not_needed():

    assert (
        _needs_callsite(
            FakeDuo(),
            level="INFO",
            main_sink_log_cfr=None,
            jsonl_cfr=None,
            user_sink_log_cfr=None,
            user_sink_config=None,
        )
        is False
    )


# === _should_route_to_sink() ==================================================

# --- test_09_should_route_console_main_sink() --------------------------------
def test_09_should_route_console_main_sink():

    assert (
        _should_route_to_sink(
            rank=2,
            destination="console",
            user_sink_config=None,
            console_verbosity=2,
            main_sink_log_verbosity=2,
        )
        is True
    )


# --- test_10_should_not_route_console_due_to_verbosity() ---------------------
def test_10_should_not_route_console_due_to_verbosity():

    assert (
        _should_route_to_sink(
            rank=3,
            destination="console",
            user_sink_config=None,
            console_verbosity=2,
            main_sink_log_verbosity=2,
        )
        is False
    )


# --- test_11_should_not_route_console_user_sink_disabled() -------------------
def test_11_should_not_route_console_user_sink_disabled():

    assert (
        _should_route_to_sink(
            rank=2,
            destination="console",
            user_sink_config=FakeUserSinkConfig(
                to_console=False,
            ),
            console_verbosity=2,
            main_sink_log_verbosity=2,
        )
        is False
    )


# --- test_12_should_route_main_log() -----------------------------------------
def test_12_should_route_main_log():

    assert (
        _should_route_to_sink(
            rank=2,
            destination="main_sink_log",
            user_sink_config=None,
            console_verbosity=2,
            main_sink_log_verbosity=2,
        )
        is True
    )


# --- test_13_should_not_route_main_log_user_sink_disabled() ------------------
def test_13_should_not_route_main_log_user_sink_disabled():

    assert (
        _should_route_to_sink(
            rank=2,
            destination="main_sink_log",
            user_sink_config=FakeUserSinkConfig(
                to_main_log=False,
            ),
            console_verbosity=2,
            main_sink_log_verbosity=2,
        )
        is False
    )


# --- test_14_should_route_user_sink() ----------------------------------------
def test_14_should_route_user_sink():

    assert (
        _should_route_to_sink(
            rank=2,
            destination="user_sink_log",
            user_sink_config=FakeUserSinkConfig(
                log_verbosity=2,
            ),
            console_verbosity=2,
            main_sink_log_verbosity=2,
        )
        is True
    )


# --- test_15_should_not_route_user_sink_for_main_sink() ----------------------
def test_15_should_not_route_user_sink_for_main_sink():

    assert (
        _should_route_to_sink(
            rank=2,
            destination="user_sink_log",
            user_sink_config=None,
            console_verbosity=2,
            main_sink_log_verbosity=2,
        )
        is False
    )


# --- test_16_should_not_route_user_sink_due_to_verbosity() -------------------
def test_16_should_not_route_user_sink_due_to_verbosity():

    assert (
        _should_route_to_sink(
            rank=3,
            destination="user_sink_log",
            user_sink_config=FakeUserSinkConfig(
                log_verbosity=2,
            ),
            console_verbosity=2,
            main_sink_log_verbosity=2,
        )
        is False
    )


# --- test_17_should_raise_unknown_destination() ------------------------------
def test_17_should_raise_unknown_destination():

    with pytest.raises(RuntimeError):

        _should_route_to_sink(
            rank=2,
            destination="banana",
            user_sink_config=None,
            console_verbosity=2,
            main_sink_log_verbosity=2,
        )

