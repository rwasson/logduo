"""
test_created_file_record.py

Test: created_file_record_builders.py, created_file_record_registration.py,
   and runtime.py
"""
from pathlib import Path

import pytest

from developer_resources.pytest_toolkit.test_utils import _new_test_log
from logduo import Duo
from logduo.internals.engine.runtime_classes import CreatedFileRecord, RuntimeRecord, UserSinkConfig
from logduo.internals.filesystem.created_file_record_builders import (
    _build_artifact_created_file_record,
    _build_cfr_base,
    _build_jsonl_created_file_record,
    _build_loguru_created_file_record,
    _build_main_sink_log_created_file_record,
    _build_user_sink_log_created_file_record,
    _validate_cfr_fields_complete,
)
from logduo.internals.filesystem.created_file_record_registration import _register_created_file_record


# --- test_01_runtime_get_created_file_record_success() ------------------------
def test_01_runtime_get_created_file_record_success():

    runtime = RuntimeRecord()

    cfr = CreatedFileRecord(
        path=Path("a.log"),
        file_name="a.log",
        file_ext="log",
        file_kind="main_sink_log",
        is_log_file=True,
        sink_name="main",
        sink_id=1,
        log_verbosity=2,
        log_file_mode="write",
        log_prefix="off",
        log_wrap_width="off",
        log_header="off",
        log_footer="off",
        show_pid_in_log=False,
        continuation_prefix_len=0,
    )

    runtime.created_file_record_registry[cfr.path] = cfr

    assert (
        runtime._get_created_file_record_by_file_path(cfr.path)
        is cfr
    )


# --- test_02_runtime_get_created_file_record_missing_raises() -----------------
def test_02_runtime_get_created_file_record_missing_raises():

    runtime = RuntimeRecord()

    with pytest.raises(RuntimeError):
        runtime._get_created_file_record_by_file_path(
            Path("missing.log")
        )


# --- test_03_runtime_get_user_sink_record_success() ------------------------------
def test_03_runtime_get_user_sink_record_success():

    runtime = RuntimeRecord()

    sink = UserSinkConfig(
        sink_name="audit",
        to_console=False,
        to_main_log=False,
        log_verbosity=2,
        sink_dir_path=Path("."),
        log_file_path=Path("audit.log"),
        log_file_mode="write",
        log_prefix="off",
        log_wrap_width="off",
        log_header="off",
        log_footer="off",
    )

    runtime.user_sink_config_registry["audit"] = sink

    assert runtime._get_user_sink_record("audit") is sink


# --- test_04_runtime_get_user_sink_record_missing_raises() --------------------
def test_04_runtime_get_user_sink_record_missing_raises():

    runtime = RuntimeRecord()

    with pytest.raises(RuntimeError):
        runtime._get_user_sink_record("missing")


# --- test_05_warning_already_registered() -------------------------------------
def test_05_warning_already_registered():

    runtime = RuntimeRecord()

    runtime.unique_warning_set.add("abc")

    assert runtime.warning_already_registered("abc") is True
    assert runtime.warning_already_registered("xyz") is False


# --- test_06_build_main_sink_log_created_file_record() ------------------------
def test_06_build_main_sink_log_created_file_record(tmp_path):
    log = _new_test_log(tmp_path)

    config = log.session_config

    cfr = _build_main_sink_log_created_file_record(
        config=config,
        file_path=Path("main.log"),
        sink_name="main",
        sink_id=1,
    )

    assert cfr.file_kind == "main_sink_log"
    assert cfr.is_log_file is True
    assert cfr.sink_id == 1


# --- def test_07_build_main_sink_log_created_file_record_bad_config() ---------
def test_07_build_main_sink_log_created_file_record_bad_config():

    with pytest.raises(RuntimeError):

        _build_main_sink_log_created_file_record(
            config={},                       # noqa, intentional
            file_path=Path("main.log"),
            sink_name="main",
            sink_id=1,
        )


# --- test_08_build_user_sink_log_created_file_record_bad_config() -------------
def test_08_build_user_sink_log_created_file_record_bad_config():

    with pytest.raises(RuntimeError):

        _build_user_sink_log_created_file_record(
            config={},                           # noqa intentional
            show_pid_in_log=False,
            file_path=Path("audit.log"),
            sink_name="audit",
            sink_id=1,
        )


# --- test_09_build_jsonl_created_file_record() --------------------------------
def test_09_build_jsonl_created_file_record():

    cfr = _build_jsonl_created_file_record(
        file_path=Path("events.jsonl")
    )

    assert cfr.file_kind == "jsonl"
    assert cfr.is_log_file is False


# --- test_10_build_artifact_created_file_record() -----------------------------
def test_10_build_artifact_created_file_record():

    cfr = _build_artifact_created_file_record(
        file_path=Path("config.txt")
    )

    assert cfr.file_kind == "artifact"
    assert cfr.is_log_file is False


# --- test_11_build_loguru_created_file_record() -------------------------------
def test_11_build_loguru_created_file_record():

    cfr = _build_loguru_created_file_record(
        file_path=Path("audit.log"),
        sink_id=99,
    )

    assert cfr.file_kind == "loguru_log"
    assert cfr.sink_id == 99


# --- test_12_build_cfr_base_requires_path() -----------------------------------
def test_12_build_cfr_base_requires_path():

    with pytest.raises(RuntimeError):

        _build_cfr_base(
            file_path="not_a_path",    # noqa intentional
            sink_name=None,
            sink_id=None,
            file_kind="artifact",
            is_log_file=False,
            log_verbosity=0,
            log_file_mode="write",
            log_prefix="off",
            log_wrap_width="off",
            log_header="off",
            log_footer="off",
            show_pid_in_log=False,
        )


# --- test_13_build_cfr_base_invalid_log_verbosity() ---------------------------
def test_13_build_cfr_base_invalid_log_verbosity():

    with pytest.raises(RuntimeError):

        _build_cfr_base(
            file_path=Path("a.txt"),
            sink_name=None,
            sink_id=None,
            file_kind="artifact",
            is_log_file=False,
            log_verbosity=999,    # noqa intentional error
            log_file_mode="write",
            log_prefix="off",
            log_wrap_width="off",
            log_header="off",
            log_footer="off",
            show_pid_in_log=False,
        )


# --- test_14_validate_cfr_fields_complete_missing_field() ---------------------
def test_14_validate_cfr_fields_complete_missing_field():

    kwargs = {
        "path": Path("a.txt"),
    }

    with pytest.raises(RuntimeError):
        _validate_cfr_fields_complete(kwargs)


# --- test_15_register_created_file_record_duplicate_path_raises() ------------
def test_15_register_created_file_record_duplicate_path_raises(tmp_path):

    log = Duo()
    runtime = log._runtime
    path = (tmp_path / "a.log").resolve()

    cfr1 = _build_artifact_created_file_record(file_path=path,)
    cfr2 = _build_artifact_created_file_record(file_path=path,)

    runtime.created_file_record_registry[path] = cfr1

    with pytest.raises(ValueError):
        _register_created_file_record(
            log,
            cfr2,
        )


# --- test_16_register_created_file_record_requires_resolved_path() -----------
def test_16_register_created_file_record_requires_resolved_path(tmp_path):

    log = Duo()

    unresolved = Path("relative.log")

    cfr = _build_artifact_created_file_record(file_path=unresolved)

    with pytest.raises(RuntimeError):
        _register_created_file_record(
            log,
            cfr,
        )


# --- test_17_register_created_file_record_success() --------------------------
def test_17_register_created_file_record_success(tmp_path):
    log = _new_test_log(tmp_path)

    path = (tmp_path / "artifact.txt").resolve()

    cfr = _build_artifact_created_file_record(file_path=path)
    result = _register_created_file_record(log, cfr)

    assert result is cfr
    assert path in log._runtime.created_file_record_registry



# --- test_18_register_created_file_record_jsonl_failure_warns() -------------
def test_18_register_created_file_record_jsonl_failure_warns(
    monkeypatch,
    tmp_path,
):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        write_jsonl=True)

    print(log.session_config.write_jsonl)

    path = (tmp_path / "artifact.txt").resolve()

    cfr = _build_artifact_created_file_record(file_path=path)

    def boom(*args, **kwargs):                       # noqa intentional
        raise RuntimeError("forced test failure")

    monkeypatch.setattr(
        "logduo.internals.sinks.jsonl._emit_jsonl_file_registration",
        boom,
    )

    _register_created_file_record(log, cfr)

    assert any(
        "JSONL file registration event failed"
        in msg
        for msg in log._runtime.unique_warning_set
    )


# --- test_19_runtime_get_file_list_in_cfr() ---------------------------------
def test_19_runtime_get_file_list_in_cfr():
    runtime = RuntimeRecord()
    assert runtime._get_file_list_in_cfr() == []
