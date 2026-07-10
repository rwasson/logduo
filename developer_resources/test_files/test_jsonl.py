"""
test_jsonl.py

Tests: jsonl.py
"""

import json
from pathlib import Path

import pytest

from logduo import Duo
from logduo.internals.engine.runtime_classes import CreatedFileRecord, EmitEvent
from logduo.internals.filesystem.created_file_record_builders import (
    _build_artifact_created_file_record,
)
from logduo.internals.formatters.message_prep import MessageKind
from logduo.internals.sinks.jsonl import (
    _build_files_created_entry,
    _build_jsonl_payload,
    _emit_jsonl,
    _emit_jsonl_end,
    _emit_jsonl_file_registration,
    _emit_jsonl_payload,
    _initialize_jsonl,
)

# --- helpers -----------------------------------------------------------------

def _read_jsonl(path: Path) -> list[dict]:

    lines = path.read_text(
        encoding="utf-8"
    ).splitlines()

    return [
        json.loads(line)
        for line in lines
        if line.strip()
    ]


def _fake_emit_event(**overrides):
    return EmitEvent(
        # sink_name="main_sink",
        target_kind="jsonl",
        # level="INFO",
        # label="INFO",
        # message="hello",
        # resolved_call_args={},
        # callsite="test.py:1",
        created_file_record=None,
        # warn_key=None,
        # event_type="message",
        sink_tag=None,
        # output_targets=["jsonl"],
        message_kind=MessageKind.INLINE,
        **overrides,
    )

def _fake_cfr(path: Path):
    return CreatedFileRecord(
        path=path,
        file_name=path.name,
        file_ext="log",
        file_kind="user_sink_log",
        is_log_file=True,
        sink_name="audit",
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


# --- test_01_initialize_jsonl_disabled() -------------------------------------
def test_01_initialize_jsonl_disabled(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), write_jsonl=False)

    _initialize_jsonl(log)


    assert log._runtime.jsonl_path_abs is None


# --- test_02_initialize_jsonl_creates_file() ---------------------------------
def test_02_initialize_jsonl_creates_file(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), write_jsonl=True)


    records = _read_jsonl(log._runtime.jsonl_path_abs)
    print(" ")
    print("**************************")
    print("test_02_initialize_jsonl_creates_file")
    print("records")
    print(records)

    assert log._runtime.jsonl_path_abs.exists()
    assert any(
        r["event_type"] == "session_file_registration"
        for r in records
    )
    assert any(
        r["event_type"] == "session_start"
        for r in records
    )


# --- test_03_emit_jsonl_message_written() ------------------------------------
def test_03_emit_jsonl_message_written(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), write_jsonl=True)


    event = _fake_emit_event(
        event_type="message",
        sink_name="main_sink",
        level="INFO",
        label="INFO",
        message="hello",
        output_targets=["jsonl"],
        resolved_call_args={},
        callsite="test.py:1",
        warn_key=None,
    )

    _emit_jsonl(log, event=event)

    records = _read_jsonl(log._runtime.jsonl_path_abs)

    assert any(
        r.get("message") == "hello"
        for r in records
    )


# --- test_05_emit_jsonl_blank_message_normalized() ---------------------------
def test_05_emit_jsonl_blank_message_normalized(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), write_jsonl=True)


    event = _fake_emit_event(
        event_type="message",
        sink_name="main_sink",
        level="INFO",
        label="INFO",
        message="   ",
        output_targets=["jsonl"],
        resolved_call_args={},
        callsite="test.py:1",
        warn_key=None,
    )

    _emit_jsonl(
        log,
        event=event,
    )

    records = _read_jsonl(
        log._runtime.jsonl_path_abs
    )

    msg_record = records[-1]

    assert msg_record["message"] == ""


# --- test_06_emit_jsonl_file_registration() ---------------------------------
def test_06_emit_jsonl_file_registration(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), write_jsonl=True)


    cfr = _build_artifact_created_file_record(
        file_path=(tmp_path / "artifact.txt").resolve()
    )

    _emit_jsonl_file_registration(
        log,
        cfr,
    )

    records = _read_jsonl(
        log._runtime.jsonl_path_abs
    )

    assert any(
        r["event_type"] == "session_file_registration"
        for r in records
    )


# --- test_07_emit_jsonl_end_written() ----------------------------------------
def test_07_emit_jsonl_end_written(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), write_jsonl=True)


    _emit_jsonl_end(log)

    records = _read_jsonl(
        log._runtime.jsonl_path_abs
    )

    assert records[-1]["event_type"] == "session_end"


# --- test_08_build_jsonl_payload_warn_key() ----------------------------------
def test_08_build_jsonl_payload_warn_key(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), write_jsonl=True)

    event = _fake_emit_event(
        event_type="message",
        sink_name="main_sink",
        level="WARNING",
        label="WARNING",
        message="hello",
        output_targets=["jsonl"],
        resolved_call_args={},
        callsite="test.py:1",
        warn_key="MY_KEY",
    )

    payload = _build_jsonl_payload(
        log,
        event=event,
        message_text="hello",
    )

    assert payload["warn_key"] == "MY_KEY"


# --- test_09_emit_jsonl_payload_invalid_event_type() -------------------------
def test_09_emit_jsonl_payload_invalid_event_type(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), write_jsonl=True)

    with pytest.raises(ValueError):

        _emit_jsonl_payload(
            log,
            event_type="bad_event",
            payload={},
        )


# --- test_10_emit_jsonl_payload_invalid_output_targets() ---------------------
def test_10_emit_jsonl_payload_invalid_output_targets(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), write_jsonl=True)


    with pytest.raises(ValueError):

        _emit_jsonl_payload(
            log,
            event_type="session_start",
            payload={},
            output_targets="jsonl",      # noqa
        )


# --- test_11_emit_jsonl_payload_missing_required_field() ---------------------
def test_11_emit_jsonl_payload_missing_required_field(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), write_jsonl=True)

    with pytest.raises(ValueError):

        _emit_jsonl_payload(
            log,
            event_type="session_end",
            payload={},
        )


# --- test_12_emit_jsonl_payload_message_requires_sink_name() -----------------
def test_12_emit_jsonl_payload_message_requires_sink_name(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), write_jsonl=True)


    with pytest.raises(RuntimeError):

        _emit_jsonl_payload(
            log,
            event_type="message",
            payload={
                "callsite": "x",
                "level": "INFO",
                "label": "INFO",
                "message": "hello",
                "resolved_call_args": {},
                "pid": 1,
                "instance_index": 1,
            },
            sink_name="",
        )


# --- test_13_build_files_created_entry() -------------------------------------
def test_13_build_files_created_entry(tmp_path):

    cfr = _build_artifact_created_file_record(
        file_path=(tmp_path / "artifact.txt").resolve()
    )

    entry = _build_files_created_entry(cfr)

    assert entry["file_name"] == "artifact.txt"
    assert entry["file_kind"] == "artifact"


# --- test_14_emit_jsonl_payload_no_path_returns() ----------------------------
def test_14_emit_jsonl_payload_no_path_returns(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), write_jsonl=False)

    assert log._runtime.jsonl_path_abs is None

    _emit_jsonl_payload(
        log,
        event_type="session_start",
        payload={
            "script_name": None,
            "script_path": None,
            "run_id_iso": None,
            "session_timestamp": None,
            "pid": None,
            "instance_index": None,
            "os_name": None,
            "python_version": None,
            "log_file_mode": None,
            "log_file_layout": None,
            "log_verbosity": None,
            "console_verbosity": None,
            "log_dir_path": None,
            "main_sink_log_dir_path": None,
            "main_sink_log_file_path": None,
            "write_config_json": None,
            "jsonl_schema_version": 1,
        },
    )


# --- test_15_initialize_jsonl_duplicate_warns() -----------------------------
def test_15_initialize_jsonl_duplicate_warns(tmp_path):
    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        write_jsonl=True,
    )

    _initialize_jsonl(log)
    warnings_before = len(log._runtime.unique_warning_set)

    _initialize_jsonl(log)

    assert len(log._runtime.unique_warning_set) == warnings_before
    assert (
            "JSONL already initialized for this session; skipping"
            in log._runtime.unique_warning_set
    )
    assert any(
        "already initialized"
        in msg
        for msg in log._runtime.unique_warning_set
    )


# --- test_16_initialize_jsonl_file_create_failure() ------------------------
def test_16_initialize_jsonl_file_create_failure(
    tmp_path,
    monkeypatch,
):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        write_jsonl=True,
    )

    # force re-run initialization path
    log._runtime.jsonl_path_abs = None
    log._runtime.created_file_record_registry.clear()

    original_open = Path.open

    def fake_open(self, *args, **kwargs):
        if str(self).endswith(".jsonl"):
            raise OSError("forced failure")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(
        Path,
        "open",
        fake_open,
    )

    _initialize_jsonl(log)

    assert any(
        "Could not create JSONL file"
        in msg
        for msg in log._runtime.unique_warning_set
    )

# --- test_17_emit_jsonl_payload_invalid_sink_name_type() -------------------
def test_17_emit_jsonl_payload_invalid_sink_name_type(
    tmp_path,
):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        write_jsonl=True,
    )

    with pytest.raises(TypeError):

        _emit_jsonl_payload(
            log,
            event_type="session_end",
            payload={
                "session_end_iso": None,
                "duration_seconds": None,
                "duration_display": None,
                "total_events": 0,
                "total_files_created": 0,
                "files_created": [],
            },
            sink_name=123,       # noqa intentional
        )


# --- test_18_emit_jsonl_payload_write_failure_warns() ----------------------
def test_18_emit_jsonl_payload_write_failure_warns(
    tmp_path,
    monkeypatch,
):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        write_jsonl=True,
    )

    def boom(*args, **kwargs):               # noqa
        raise OSError("forced write failure")

    monkeypatch.setattr(
        Path,
        "open",
        boom,
    )

    _emit_jsonl_payload(
        log,
        event_type="session_end",
        payload={
            "session_end_iso": None,
            "duration_seconds": None,
            "duration_display": None,
            "event_count": 0,
            "total_files_created": 0,
            "files_created": [],
        },
    )

    assert any(
        "JSONL write failed"
        in msg
        for msg in log._runtime.unique_warning_set
    )
