"""
test_new_loguru_sink.py

Tests:
    new_loguru_sink.py

Last edited: 2026-06-10
"""

from pathlib import Path

from loguru import logger as _loguru_logger
import pytest

from logduo import Duo
from logduo.internals.sinks import new_loguru_sink
from developer_resources.pytest_toolkit.test_utils import (
    _find_file,
)


# --- test_01_new_loguru_creates_file() ----------------------------------------
def test_01_new_loguru_creates_file(tmp_path: Path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    sink_id = log.new_loguru_sink(
        "audit.log",
    )

    log.close()

    assert isinstance(sink_id, int)

    audit_log = _find_file(tmp_path, "audit.log")

    assert audit_log.exists()


# --- test_02_new_loguru_write_mode_overwrites_file() --------------------------
def test_02_new_loguru_write_mode_overwrites_file(tmp_path: Path):

    audit_log = tmp_path / "audit.log"

    audit_log.write_text(
        "OLD CONTENT",
        encoding="utf-8",
    )

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    log.new_loguru_sink(
        audit_log,
        file_mode="write",
    )

    log.close()

    text = audit_log.read_text(encoding="utf-8")

    assert "OLD CONTENT" not in text


# --- test_03_new_loguru_append_mode_preserves_file() --------------------------
def test_03_new_loguru_append_mode_preserves_file(tmp_path: Path):

    audit_log = tmp_path / "audit.log"

    audit_log.write_text(
        "OLD CONTENT\n",
        encoding="utf-8",
    )

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    log.new_loguru_sink(
        audit_log,
        file_mode="append",
    )

    log.close()

    text = audit_log.read_text(encoding="utf-8")

    assert "OLD CONTENT" in text


# --- test_04_new_loguru_duplicate_file_raises() -------------------------------
def test_04_new_loguru_duplicate_file_raises(tmp_path: Path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    log.new_loguru_sink("audit.log")

    with pytest.raises(ValueError):
        log.new_loguru_sink("audit.log")

    log.close()


# --- test_05_new_loguru_timestamped_mode_creates_timestamped_file() -----------
def test_05_new_loguru_timestamped_mode_creates_timestamped_file(
    tmp_path: Path,
):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    log.new_loguru_sink(
        "audit.log",
        file_mode="timestamped",
    )

    log.close()

    files = list(tmp_path.rglob("audit*.log"))

    assert files
    assert len(files) == 1

    assert files[0].name != "audit.log"


# --- test_06_invalid_kwargs_emit_warning() ------------------------------------
def test_06_invalid_kwargs_emit_warning(
    tmp_path: Path,
    capsys,
):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    log.new_loguru_sink(
        "audit.log",
        bad_kwarg=True,
    )

    captured = capsys.readouterr()

    console_output = captured.out + captured.err

    assert "Ignored invalid loguru kwargs" in console_output

    log.close()


# --- test_07_invalid_kwargs_not_passed_to_loguru() ----------------------------
def test_07_invalid_kwargs_not_passed_to_loguru(
    tmp_path: Path,
    monkeypatch,
):
    """ Will fail if change contract """

    captured_kwargs = {}

    def fake_add(*args, **kwargs):       # noqa
        captured_kwargs.update(kwargs)
        return 123



    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    monkeypatch.setattr(
        new_loguru_sink._loguru_logger,
        "add",
        fake_add,
    )

    log.new_loguru_sink(
        "audit.log",
        rotation="10 MB",
        enqueue=False,
        bad_kwarg="ignore_me",
    )

    log.close()

    assert "rotation" in captured_kwargs
    assert "enqueue" in captured_kwargs

    assert "bad_kwarg" not in captured_kwargs



# --- test_08_invalid_kwargs_emit_warning_and_sink_still_works() --------------
def test_08_invalid_kwargs_emit_warning_and_sink_still_works(
    tmp_path: Path,
    capsys,
):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    sink_id = log.new_loguru_sink(
        "audit.log",
        bad_kwarg="ignore_me",
    )

    captured = capsys.readouterr()

    console_output = captured.out + captured.err

    assert sink_id is not None

    assert "Ignored invalid loguru kwargs" in console_output

    audit_log = _find_file(tmp_path, "audit.log")

    assert audit_log.exists()

    log.close()


# --- test_09_cfr_record_registered() ------------------------------------------
def test_09_cfr_record_registered(
    tmp_path: Path,
):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    sink_id = log.new_loguru_sink("audit.log")


    cfrs = log._runtime._get_file_list_in_cfr()

    matching = [
        cfrs
        for cfr in cfrs
        if cfr.path.name == "audit.log"
    ]

    assert len(matching) == 1
    assert isinstance(sink_id, int)

    log.close()


# --- test_10_duplicate_absolute_path_raises() --------------------------------
def test_10_duplicate_absolute_path_raises(
    tmp_path: Path,
):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    audit_path = tmp_path / "audit.log"

    log.new_loguru_sink(
        audit_path,
    )

    with pytest.raises(ValueError):
        log.new_loguru_sink(
            audit_path.resolve(),
        )

    log.close()


# --- test_11_loguru_sink_id_stored_in_cfr() ----------------------------------
def test_11_loguru_sink_id_stored_in_cfr(
    tmp_path: Path,
):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    sink_id = log.new_loguru_sink(
        "audit.log",
    )

    cfrs = log._runtime._get_file_list_in_cfr()

    matching = [
        cfr
        for cfr in cfrs
        if cfr.path.name == "audit.log"
    ]

    assert len(matching) == 1

    cfr = matching[0]

    assert cfr.sink_id == sink_id

    log.close()


# --- test_12_timestamped_mode_creates_timestamped_file() ----------------------
def test_12_timestamped_mode_creates_timestamped_file(tmp_path: Path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    sink_id = log.new_loguru_sink(
        "audit.log",
        file_mode="timestamped",
    )

    assert sink_id is not None

    log.close()

    files = list(tmp_path.rglob("*audit*.log"))

    assert files
    assert len(files) == 1

    file_name = files[0].name

    print(f"timestamped file_name = {file_name}")

    assert file_name != "audit.log"
    assert "audit" in file_name



# --- test_13_write_mode_overwrites_existing_file() ----------------------------
def test_13_write_mode_overwrites_existing_file(tmp_path: Path):

    existing_file = tmp_path / "audit.log"

    existing_file.write_text(
        "OLD CONTENT",
        encoding="utf-8",
    )

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    sink_id = log.new_loguru_sink(
        existing_file,
        file_mode="write",
    )

    assert sink_id is not None

    log.close()

    text = existing_file.read_text(encoding="utf-8")

    assert "OLD CONTENT" not in text



# --- test_14_append_mode_preserves_existing_file() ----------------------------
def test_14_append_mode_preserves_existing_file(tmp_path: Path):

    existing_file = tmp_path / "audit.log"

    existing_file.write_text(
        "OLD CONTENT\n",
        encoding="utf-8",
    )

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    sink_id = log.new_loguru_sink(
        existing_file,
        file_mode="append",
    )

    assert sink_id is not None

    log.close()

    text = existing_file.read_text(encoding="utf-8")

    assert "OLD CONTENT" in text



# --- test_15_absolute_path_creates_file() -------------------------------------
def test_15_absolute_path_creates_file(tmp_path: Path):

    absolute_file = (
        tmp_path
        / "nested"
        / "folder"
        / "audit.log"
    )

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    sink_id = log.new_loguru_sink(
        absolute_file,
    )

    assert sink_id is not None

    log.close()

    assert absolute_file.exists()


# --- test_16_duplicate_path_raises() ------------------------------------------
def test_16_duplicate_path_raises(tmp_path: Path):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    log.new_loguru_sink("audit.log")

    with pytest.raises(ValueError):
        log.new_loguru_sink("audit.log")

    log.close()


# --- test_17_loguru_sink_id_stored_in_cfr() -----------------------------------
def test_17_loguru_sink_id_stored_in_cfr(tmp_path: Path):

    log = Duo()
    log.configure(
        log_dir_path=str(tmp_path),
        log_dir_layout="script",
    )

    sink_id = log.new_loguru_sink("audit.log")
    cfrs = log._runtime._get_file_list_in_cfr()

    matching = [
        cfr
        for cfr in cfrs
        if cfr.path.name == "audit.log"
    ]

    assert len(matching) == 1
    cfr = matching[0]
    assert cfr.sink_id == sink_id

    log.close()


# --- test_18_new_loguru_mkdir_failure_returns_none() -------------------------
def test_18_new_loguru_mkdir_failure_returns_none(
    tmp_path,
    monkeypatch,
):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
    )

    def boom(*args, **kwargs):
        raise OSError("forced mkdir failure")

    monkeypatch.setattr(
        Path,
        "mkdir",
        boom,
    )

    sink_id = log.new_loguru_sink(
        "audit.log",
    )

    assert sink_id is None

    log.close()


# --- test_19_new_loguru_write_mode_file_init_failure() -----------------------
def test_19_new_loguru_write_mode_file_init_failure(
    tmp_path,
    monkeypatch,
):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    original_open = Path.open

    def fake_open(self, *args, **kwargs):
        if self.name == "audit.log":
            raise OSError("forced open failure")
        return original_open(self, *args, **kwargs)

    monkeypatch.setattr(
        Path,
        "open",
        fake_open,
    )

    sink_id = log.new_loguru_sink(
        "audit.log",
        file_mode="write",
    )

    assert sink_id is None

    log.close()


# --- test_20_new_loguru_add_failure_returns_none() ---------------------------
def test_20_new_loguru_add_failure_returns_none(
    tmp_path,
    monkeypatch,
):

    def boom(*args, **kwargs):
        raise ValueError("forced add failure")


    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    monkeypatch.setattr(
        new_loguru_sink._loguru_logger,
        "add",
        boom,
    )

    sink_id = log.new_loguru_sink("audit.log")
    assert sink_id is None

    log.close()


# --- test_21_register_cfr_failure_non_fatal() -------------------------------
def test_21_register_cfr_failure_non_fatal(
    tmp_path,
    monkeypatch,
):

    def boom(*args, **kwargs):
        raise ValueError("forced cfr failure")

    monkeypatch.setattr(
        new_loguru_sink,
        "_register_created_file_record",
        boom,
    )

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    sink_id = log.new_loguru_sink("audit.log")
    assert isinstance(sink_id, int)

    log.close()


# --- test_22_serialize_non_primitive_value() -------------------------------
def test_22_serialize_non_primitive_value():

    result = (
        new_loguru_sink
        ._serialize_new_loguru_kwargs_for_cfr_field(
            {
                "rotation": "10 MB",
                "filter": lambda x: x,
            }
        )
    )

    assert result["rotation"] == "10 MB"
    assert result["filter"] == "<function>"


# --- test_23_new_loguru_sink_respects_user_format() ---------------------------
def test_23_new_loguru_sink_respects_user_format(tmp_path):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    sink_path = tmp_path / "custom.log"

    sink_id = log.new_loguru_sink(
        sink_path,
        format="PREFIX | {message}",
    )

    _loguru_logger.info("hello")

    _loguru_logger.remove(sink_id)

    content = sink_path.read_text()

    assert "PREFIX | hello" in content


# --- test_24_new_loguru_sink_handles_braces_and_angle_brackets() --------------
def test_24_new_loguru_sink_handles_braces_and_angle_brackets(tmp_path):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    sink_path = tmp_path / "custom.log"

    sink_id = log.new_loguru_sink(sink_path)

    _loguru_logger.info("<input>")
    _loguru_logger.info("{hello}")
    _loguru_logger.info("{{hello}}")

    _loguru_logger.remove(sink_id)

    content = sink_path.read_text()

    assert "<input>" in content
    assert "{hello}" in content
    assert "{{hello}}" in content


# --- test_25_callable_filter() ------------------------------------------------
def test_25_callable_filter(tmp_path):

    log = Duo()
    log.configure(log_dir_path=str(tmp_path))
    sink_path = tmp_path / "errors.log"

    sink_id = log.new_loguru_sink(
        sink_path,
        filter=lambda r: r["level"].name == "ERROR",
    )

    _loguru_logger.info("info")
    _loguru_logger.error("error")

    _loguru_logger.remove(sink_id)

    content = sink_path.read_text()

    assert "error" in content
    assert "info" not in content
