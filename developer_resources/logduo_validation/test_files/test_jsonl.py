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

# --- test_19_jsonl_trace_message_written() -----------------------------------
def test_19_jsonl_trace_message_written(tmp_path):

    log = Duo()
    log.configure(
        log_dir_path=tmp_path,
        write_jsonl=True,
        console_verbosity=0,
        log_verbosity=3,
    )

    jsonl_path = log._runtime.jsonl_path_abs

    log.trace("trace JSONL message")
    log.close()

    records = _read_jsonl(jsonl_path)

    trace_records = [
        record
        for record in records
        if record.get("event_type") == "message"
        and record.get("message") == "trace JSONL message"
    ]

    assert len(trace_records) == 1

    trace_record = trace_records[0]

    assert trace_record["level"] == "TRACE"
    assert trace_record["label"] == "TRACE"
    assert trace_record["sink_name"] == "main_sink"


# --- test_20_emit_jsonl_missing_event_type_raises() --------------------------
def test_20_emit_jsonl_missing_event_type_raises(tmp_path):

    log = Duo()
    log.configure(
        log_dir_path=tmp_path,
        write_jsonl=True,
    )

    event = _fake_emit_event(
        event_type=None,
        sink_name="main_sink",
        level="INFO",
        label="INFO",
        message="hello",
        output_targets=["jsonl"],
        resolved_call_args={},
        callsite="test.py:1",
        warn_key=None,
    )

    with pytest.raises(
        RuntimeError,
        match="event_type missing for JSONL event",
    ):
        _emit_jsonl(log, event=event)


# --- test_21_emit_jsonl_plain_message_none_returns() -------------------------
def test_21_emit_jsonl_plain_message_none_returns(
    tmp_path,
    monkeypatch,
):

    log = Duo()
    log.configure(
        log_dir_path=tmp_path,
        write_jsonl=True,
    )

    records_before = _read_jsonl(
        log._runtime.jsonl_path_abs
    )

    monkeypatch.setattr(
        "logduo.internals.sinks.jsonl._build_plain_message",
        lambda message: None,
    )

    event = _fake_emit_event(
        event_type="message",
        sink_name="main_sink",
        level="INFO",
        label="INFO",
        message="ignored",
        output_targets=["jsonl"],
        resolved_call_args={},
        callsite="test.py:1",
        warn_key=None,
    )

    _emit_jsonl(log, event=event)

    records_after = _read_jsonl(
        log._runtime.jsonl_path_abs
    )

    assert records_after == records_before

# --- test_22_emit_jsonl_non_string_plain_message_raises() --------------------
def test_22_emit_jsonl_non_string_plain_message_raises(
    tmp_path,
    monkeypatch,
):

    log = Duo()
    log.configure(
        log_dir_path=tmp_path,
        write_jsonl=True,
    )

    monkeypatch.setattr(
        "logduo.internals.sinks.jsonl._build_plain_message",
        lambda message: 123,
    )

    event = _fake_emit_event(
        event_type="message",
        sink_name="main_sink",
        level="INFO",
        label="INFO",
        message="ignored",
        output_targets=["jsonl"],
        resolved_call_args={},
        callsite="test.py:1",
        warn_key=None,
    )

    with pytest.raises(
        RuntimeError,
        match="_build_plain_message returned non-str: int",
    ):
        _emit_jsonl(log, event=event)


# --- test_23_jsonl_file_registration_includes_extra_fields() ----------------
def test_23_jsonl_file_registration_includes_extra_fields(tmp_path):

    log = Duo()
    log.configure(
        log_dir_path=tmp_path,
        write_jsonl=True,
    )

    cfr = _build_artifact_created_file_record(
        file_path=(tmp_path / "artifact.txt").resolve()
    )

    _emit_jsonl_file_registration(
        log,
        cfr,
        extra={
            "source": "test",
            "sequence": 3,
        },
    )

    records = _read_jsonl(
        log._runtime.jsonl_path_abs
    )

    record = records[-1]

    assert record["event_type"] == "session_file_registration"
    assert record["file_name"] == "artifact.txt"
    assert record["source"] == "test"
    assert record["sequence"] == 3


# --- test_24_emit_jsonl_payload_defaults_output_targets_to_empty_list() -------
def test_24_emit_jsonl_payload_defaults_output_targets_to_empty_list(
    tmp_path,
):

    log = Duo()
    log.configure(
        log_dir_path=tmp_path,
        write_jsonl=True,
    )

    _emit_jsonl_payload(
        log,
        event_type="message",
        payload={
            "callsite": "test.py:1",
            "level": "INFO",
            "label": "INFO",
            "message": "default targets",
            "resolved_call_args": {},
            "pid": log._runtime.pid,
            "instance_index": log._runtime.instance_index,
        },
        sink_name="main_sink",
        output_targets=None,
    )

    records = _read_jsonl(
        log._runtime.jsonl_path_abs
    )

    record = records[-1]

    assert record["message"] == "default targets"
    assert record["output_targets"] == []


# --- test_25_non_message_event_normalizes_jsonl_fields() ---------------------
def test_25_non_message_event_normalizes_jsonl_fields(tmp_path):

    log = Duo()
    log.configure(
        log_dir_path=tmp_path,
        write_jsonl=True,
    )

    payload = {
        "session_end_iso": None,
        "duration_seconds": 1.25,
        "duration_display": "1.25 seconds",
        "event_count": 3,
        "total_files_created": 0,
        "files_created": [],
        # Message-only fields should not be emitted for session_end.
        "callsite": "should disappear",
        "label": "SHOULD_DISAPPEAR",
    }

    _emit_jsonl_payload(
        log,
        event_type="session_end",
        payload=payload,
        sink_name="audit",
        output_targets=["jsonl"],
    )

    records = _read_jsonl(
        log._runtime.jsonl_path_abs
    )

    record = records[-1]

    assert record["event_type"] == "session_end"
    assert record["sink_name"] == "main_sink"
    assert "callsite" not in record
    assert "label" not in record

