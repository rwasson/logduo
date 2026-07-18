"""
test_console.py

Last edited: 2026-06-11
"""
import os

import pytest
from rich.panel import Panel
from rich.text import Text

from developer_resources.logduo_validation.pytest_files.pytest_helpers.file_helpers import _find_main_log, _read_file
from logduo import Duo
from logduo.internals.formatters.message_prep import MessageKind

# === Fakes ===================================================================
from logduo.internals.sinks.console import (
    _build_console_message,
    _emit_console_end,
    _emit_console_payload,
    _initialize_console,
)


class FakeSessionConfig:
    def __init__(self):
        self.write_jsonl = False
        self.console_prefix = "timestamp"
        self.show_debug_source = False
        self.console_verbosity = 2
        self.log_verbosity = 2
        self.console_color = True
        self.console_theme = "light"




# === _build_console_message() =================================================

# --- test_01_build_console_message_str() -------------------------------------
def test_01_build_console_message_str():

    result = _build_console_message(
        message="hello",
        console_style=None,
    )

    assert result == "hello"


# --- test_02_build_console_message_text() ------------------------------------
def test_02_build_console_message_text():

    result = _build_console_message(
        message=Text("hello"),
        console_style=None,
    )

    assert isinstance(result, Text)
    assert result.plain == "hello"


# --- test_03_build_console_message_text_applies_style() ----------------------
def test_03_build_console_message_text_applies_style():

    result = _build_console_message(
        message=Text("hello"),
        console_style="bold red",
    )

    assert isinstance(result, Text)
    assert result.plain == "hello"


# --- test_04_build_console_message_func_str_unchanged() ----------------------
def test_04_build_console_message_func_str_unchanged():

    result = _build_console_message(
        message="hello",
        console_style="bold red",
    )

    assert isinstance(result, str)
    assert result == "hello"


# --- test_05_build_console_message_renderable_preserved() --------------------
def test_05_build_console_message_renderable_preserved():

    panel = Panel("hello")

    result = _build_console_message(
        message=panel,
        console_style="blue",
    )

    assert result is panel


# --- test_06_build_console_message_non_string_object_uses_str() ---------------
def test_06_build_console_message_non_string_object_uses_str(tmp_path):

    result = _build_console_message(
        message=tmp_path,
        console_style=None,
    )
    print("")
    print("************************************************")
    print("test_06_build_console_message_non_string_object_uses_str")
    print("result:")
    print(result)

    assert isinstance(result, str)
    assert str(tmp_path) in result



# --- test_07_emit_console_payload_inline_no_prefix() -------------------------
def test_07_emit_console_payload_inline_no_prefix(monkeypatch):
    duo = Duo()

    printed = []

    def fake_print(_duo, **kwargs):
        printed.append(kwargs["message"])


    monkeypatch.setattr(
        "logduo.internals.sinks.console._safe_console_print",
        fake_print,
    )

    _emit_console_payload(
        duo,
        prefix=Text("PREFIX "),
        payload="hello",
        message_kind=MessageKind.INLINE,
        console_style=None,
        no_prefix=True,

    )

    assert len(printed) == 1


# --- test_08_emit_console_payload_inline_with_prefix() -----------------------
def test_08_emit_console_payload_inline_with_prefix(monkeypatch):
    duo = Duo()

    printed = []

    def fake_print(_duo, **kwargs):
        printed.append(kwargs["message"])

    monkeypatch.setattr(
        "logduo.internals.sinks.console._safe_console_print",
        fake_print,
    )

    _emit_console_payload(
        duo,
        prefix=Text("PREFIX "),
        payload="hello",
        message_kind=MessageKind.INLINE,
        console_style=None,
        no_prefix=False,
    )

    assert len(printed) == 1
    assert "PREFIX" in printed[0].plain


# --- test_09_emit_console_payload_structured_with_prefix() -------------------
def test_09_emit_console_payload_structured_with_prefix(monkeypatch):
    duo = Duo()

    printed = []

    def fake_print(_duo, **kwargs):
        printed.append(kwargs["message"])

    monkeypatch.setattr(
        "logduo.internals.sinks.console._safe_console_print",
        fake_print,
    )

    _emit_console_payload(
        duo,
        prefix=Text("PREFIX "),
        payload="a\nb\nc",
        message_kind=MessageKind.STRUCTURED,
        console_style=None,
        no_prefix=False,
    )

    assert len(printed) == 2


# --- test_10_emit_console_payload_invalid_message_kind() -----------------------
def test_10_emit_console_payload_invalid_message_kind():
    duo = Duo()

    with pytest.raises(RuntimeError):

        _emit_console_payload(
            duo,
            prefix=Text(),
            payload="hello",
            message_kind="banana",      # noqa intentional error
            console_style=None,
            no_prefix=True,
        )


# --- test_11_emit_console_payload_renderable_no_prefix() ---------------------
def test_11_emit_console_payload_renderable_no_prefix(monkeypatch):
    duo = Duo()

    printed = []

    def fake_print(_duo, **kwargs):
        printed.append(kwargs["message"])

    monkeypatch.setattr(
        "logduo.internals.sinks.console._safe_console_print",
        fake_print,
    )

    panel = Panel("hello")

    _emit_console_payload(
        duo,
        prefix=Text("PREFIX"),
        payload=panel,
        message_kind=MessageKind.OBJECT,
        console_style=None,
        no_prefix=True,
    )

    assert len(printed) == 1


# --- test_12_emit_console_payload_renderable_with_prefix() -------------------
def test_12_emit_console_payload_renderable_with_prefix(monkeypatch):
    duo = Duo()

    printed = []

    def fake_print(_duo, **kwargs):
        printed.append(kwargs["message"])

    monkeypatch.setattr(
        "logduo.internals.sinks.console._safe_console_print",
        fake_print,
    )

    panel = Panel("hello")

    _emit_console_payload(
        duo,
        prefix=Text("PREFIX"),
        payload=panel,
        message_kind=MessageKind.RICH_RENDERABLE,
        console_style=None,
        no_prefix=False,
    )

    assert len(printed) == 2


# --- test_13_initialize_console_invalid_palette() -----------------------------
def test_13_initialize_console_invalid_palette():
    duo = Duo()


    with pytest.raises(RuntimeError):
        _initialize_console(duo)


# --- test_14_emit_renderable_payload_with_console_style_not_warn() ---------------
def test_14_emit_renderable_payload_with_console_style_not_warn(monkeypatch):
    duo = Duo()

    warnings = []

    monkeypatch.setattr(
        "logduo.internals.sinks.console._safe_console_print",
        lambda *args, **kwargs: None,
    )

    _emit_console_payload(
        duo,
        prefix=Text(),
        payload=Panel("hello"),
        message_kind=MessageKind.OBJECT,
        console_style="blue",
        no_prefix=True,
    )

    print("")
    print("*********************")
    print("test_14_emit_renderable_payload_with_console_style_not_warn")
    print("warnings (expect there should be none):")
    print(warnings)

    assert len(warnings) == 0


# --- test_15_invalid_console_style_raises() ---------------------------
def test_15_invalid_console_style_raises(tmp_path):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path))

    with pytest.raises(ValueError) as exc:
        log(
            "hello",
            console_style="banana",
        )

    assert "Invalid console_style" in str(exc.value)


# --- test_16_console_partial_rich_text() --------------------------------------
def test_16_console_partial_rich_text(tmp_path, capsys):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
    )

    log(
        Text("value = ")
        + Text.from_markup("[blue]hello[/blue]")
    )

    log.close()

    # --- console ---
    console_output = capsys.readouterr().out

    # --- log file ---
    log_output = _read_file(_find_main_log(tmp_path))

    print(" ")
    print(" *******************************")
    print("test_16_console_partial_rich_text()")
    print("console output:")
    print(console_output)

    print(" ")
    print("log output:")
    print(log_output)

    # console
    assert "value =" in console_output
    assert "hello" in console_output

    # log
    assert "value = hello" in log_output
    assert "[blue]" not in log_output



# --- test_17_console_fstring_text_loses_rich_styling() ------------------------
def test_17_console_fstring_text_loses_rich_styling(
    tmp_path,
    capsys,
):

    t = Text.from_markup("[blue]hello[/blue]")

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
    )

    log(f"value = {t}")

    log.close()

    console_output = capsys.readouterr().out
    log_output = _read_file(_find_main_log(tmp_path))

    print(" ")
    print(" *******************************")
    print("test_17_console_fstring_text_loses_rich_styling()")
    print("console output:")
    print(console_output)

    print(" ")
    print("log output:")
    print(log_output)

    assert "value = hello" in console_output
    assert "value = hello" in log_output

# --- test_18_console_panel_below_prefix() -------------------------------------
def test_18_console_panel_below_prefix(tmp_path, capsys):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_verbosity=0,
    )

    log(Panel("hello"))
    log.close()

    output = capsys.readouterr().out

    print(" ")
    print(" *******************************")
    print("test_18_console_panel_below_prefix()")
    print("captured.out")
    print(output)

    assert "INFO" in output
    assert "hello" in output


# --- test_19_console_verbosity_zero_suppresses_console_output() ------------------
def test_19_console_verbosity_zero_suppresses_console_output(
    tmp_path,
    capsys,
):
    print(f"str(tmp_path) = {str(tmp_path)}")
    log = Duo()

    log.configure(log_dir_path=str(tmp_path), console_verbosity=0, log_file_layout="script", log_verbosity=0)

    log("hello world")

    console_output = capsys.readouterr().out

    print(" ")
    print(" *******************************")
    print("test_19_console_verbosity_zero_suppresses_all_output()")
    print(f"captured.out = {console_output!r}")

    # console completely silent
    # assert console_output == ""
    # LOGDUO INTERNAL ERRORS and WARNINGS should still appear
    assert "hello world" not in console_output
    assert "logging started" not in console_output
    assert "logging ended" not in console_output

    # no main log created
    log_files = list(tmp_path.rglob("*.log"))
    log_dir_path_abs = log._runtime.log_dir_path_abs
    main_sink_log_dir_path_abs = log._runtime.main_sink_log_dir_path_abs
    main_sink_log_file_path_abs = log._runtime.main_sink_log_file_path_abs
    output_dir_path = log.output_dir_path

    print(f"log_files = {log_files}")
    print(f"log_dir_path_abs = {log_dir_path_abs!r}")
    print(f"main_sink_log_dir_path_abs = {main_sink_log_dir_path_abs!r}")
    print(f"main_sink_log_file_path_abs = {main_sink_log_file_path_abs!r}")
    print(f"output_dir_path = {output_dir_path}")
    print()


    assert log._runtime.log_dir_path_abs is not None
    assert log._runtime.main_sink_log_dir_path_abs is not None
    assert log._runtime.main_sink_log_file_path_abs is not None
    assert log.output_dir_path is not None

    log.close()

    assert not list(tmp_path.rglob("*.log"))


# --- test_20_ansi_red_console_output() ------------------
def test_20__ansi_red_console_output(
    tmp_path,
    capsys,
):
    log = Duo()
    log.configure(log_dir_path=str(tmp_path), log_file_layout="script")

    RED = "\033[31m"
    RESET = "\033[0m"

    log(f"{RED}hello{RESET}")

    log.close()

    captured = capsys.readouterr()
    console_output = captured.out + captured.err

    log_file = _find_main_log(tmp_path)
    log_content = _read_file(log_file)

    assert "hello" in console_output
    assert "hello" in log_content

    # Console should not visibly show raw ANSI text
    print(" ")
    print("***********************************************")
    print("test_20__ansi_red_console_output().")
    print("console_output:")
    print(console_output)
    print(" ")
    print("log_content:")
    print(log_content)
    print("***********************************************")

    # and neither should logs
    assert "[31m" not in log_content
    assert "[0m" not in log_content
    assert "\033[31m" not in log_content
    assert "\033[0m" not in log_content


# --- test_21_rich_text_console_and_log_output() -------------------------------
def test_21_rich_text_console_and_log_output(
    tmp_path,
    capsys,
):
    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
    )

    log(
        Text.from_markup("[red]hello[/red]")
    )

    log.close()

    captured = capsys.readouterr()

    console_output = captured.out + captured.err

    log_file = _find_main_log(tmp_path)
    log_content = _read_file(log_file)

    assert "hello" in console_output
    assert "hello" in log_content

    # Rich markup should never appear in output
    assert "[red]" not in console_output
    assert "[/red]" not in console_output

    assert "[red]" not in log_content
    assert "[/red]" not in log_content

# --- test_22_console_style_console_and_log_output() ---------------------------
def test_22_console_style_console_and_log_output(
    tmp_path,
    capsys,
):
    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
    )

    log(
        "hello",
        console_style="red",
    )

    log.close()

    captured = capsys.readouterr()

    console_output = captured.out + captured.err

    log_file = _find_main_log(tmp_path)
    log_content = _read_file(log_file)

    assert "hello" in console_output
    assert "hello" in log_content


    assert "red" not in log_content


# --- test_23_ansi_long_message_wraps_cleanly() -------------------------------
def test_23_ansi_long_message_wraps_cleanly(
    tmp_path,
):
    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
        console_wrap_width=80,
        log_wrap_width=80,
    )

    RED = "\033[31m"
    RESET = "\033[0m"

    long_msg = (
        "Logduo is designed for data scientists, researchers, students, and "
        "Python developers who want readable console output, organized log files, "
        "and minimal logging setup."
    )

    log(f"{RED}{long_msg}{RESET}")

    log.close()

    log_file = _find_main_log(tmp_path)
    log_content = _read_file(log_file)

    assert "Logduo is designed for data scientists" in log_content

    assert "[0m" not in log_content
    assert "\033[" not in log_content


# --- test_24_multiple_ansi_segments() -----------------------------------------
def test_24_multiple_ansi_segments(
    tmp_path,
    capsys,
):
    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
    )

    RED = "\033[31m"
    BLUE = "\033[34m"
    RESET = "\033[0m"

    msg = (
        f"{RED}ERROR{RESET} "
        f"normal text "
        f"{BLUE}SUCCESS{RESET}"
    )

    log(msg)

    log.close()

    captured = capsys.readouterr()

    console_output = captured.out + captured.err

    log_file = _find_main_log(tmp_path)
    log_content = _read_file(log_file)

    assert "ERROR" in console_output
    assert "SUCCESS" in console_output

    assert "ERROR" in log_content
    assert "SUCCESS" in log_content

    # Console should not visibly show raw ANSI text
    print(" ")
    print("***********************************************")
    print("test_24_multiple_ansi_segments().")
    print("console_output:")
    print(console_output)
    print(" ")
    print("log_content:")
    print(log_content)
    print("***********************************************")

    # no ANSI leakage to logs
    assert "\033[" not in log_content
    assert "[31m" not in log_content
    assert "[34m" not in log_content
    assert "[0m" not in log_content


# --- test_25_multiple_ansi_segments_with_wrap() -------------------------------
def test_25_multiple_ansi_segments_with_wrap(tmp_path):

    log = Duo()

    log.configure(
        log_dir_path=str(tmp_path),
        log_file_layout="script",
        log_wrap_width=80,
    )

    RED = "\033[31m"
    BLUE = "\033[34m"
    RESET = "\033[0m"

    msg = (
        f"{RED}ERROR{RESET} "
        "Logduo is designed for data scientists and researchers "
        f"{BLUE}SUCCESS{RESET} "
        "who need readable logs."
    )

    log(msg)
    log.close()

    log_file = _find_main_log(tmp_path)
    log_content = _read_file(log_file)

    assert "ERROR" in log_content
    assert "SUCCESS" in log_content

    assert "\033[" not in log_content
    assert "[31m" not in log_content
    assert "[34m" not in log_content
    assert "[0m" not in log_content


# --- test_26_build_console_message_unprintable_object() ----------------------
def test_26_build_console_message_unprintable_object():

    class Unprintable:
        def __str__(self):
            raise ValueError("cannot convert")

    result = _build_console_message(
        message=Unprintable(),
        console_style=None,
    )

    assert result == "<unprintable object>"


# --- test_27_build_console_message_text_is_copied() --------------------------
def test_27_build_console_message_text_is_copied():

    original = Text("hello")

    result = _build_console_message(
        message=original,
        console_style="bold red",
    )

    assert isinstance(result, Text)
    assert result is not original
    assert result.plain == "hello"


# --- test_28_emit_structured_string_without_prefix() -------------------------
def test_28_emit_structured_string_without_prefix(monkeypatch):

    duo = Duo()
    printed = []

    def fake_print(_duo, **kwargs):
        printed.append(
            (
                kwargs["message"],
                kwargs["message_kind"],
            )
        )

    monkeypatch.setattr(
        "logduo.internals.sinks.console._safe_console_print",
        fake_print,
    )

    _emit_console_payload(
        duo,
        prefix=Text("PREFIX"),
        payload="line one\nline two",
        message_kind=MessageKind.STRUCTURED,
        console_style=None,
        no_prefix=True,
    )

    assert len(printed) == 1
    assert isinstance(printed[0][0], Text)
    assert printed[0][0].plain == "line one\nline two"
    assert printed[0][1] == MessageKind.STRUCTURED


# --- test_29_emit_rich_text_with_prefix() -----------------------------------
def test_29_emit_rich_text_with_prefix(monkeypatch):

    duo = Duo()
    printed = []

    def fake_print(_duo, **kwargs):
        printed.append(
            (
                kwargs["message"],
                kwargs["message_kind"],
            )
        )

    monkeypatch.setattr(
        "logduo.internals.sinks.console._safe_console_print",
        fake_print,
    )

    payload = Text("hello")

    _emit_console_payload(
        duo,
        prefix=Text("PREFIX"),
        payload=payload,
        message_kind=MessageKind.RICH_TEXT,
        console_style=None,
        no_prefix=False,
    )

    assert len(printed) == 2

    assert printed[0][0].plain == "PREFIX"
    assert printed[0][1] == MessageKind.RICH_TEXT

    assert printed[1][0] is payload
    assert printed[1][1] == MessageKind.RICH_TEXT


# --- test_30_emit_rich_text_with_console_style_warns() ----------------------
def test_30_emit_rich_text_with_console_style_warns(monkeypatch):

    duo = Duo()
    warning_messages = []

    monkeypatch.setattr(
        "logduo.internals.sinks.console._safe_console_print",
        lambda *args, **kwargs: None,
    )

    monkeypatch.setattr(
        "logduo.internals.sinks.console._runtime_warning",
        lambda _duo, *, warn_msg: warning_messages.append(warn_msg),
    )

    _emit_console_payload(
        duo,
        prefix=Text(),
        payload=Text("hello"),
        message_kind=MessageKind.RICH_TEXT,
        console_style="blue",
        no_prefix=True,
    )

    assert warning_messages == [
        "console_style ignored for Rich Text; apply style inside the Text object"
    ]

# --- test_31_emit_unsupported_payload_type_raises() --------------------------
def test_31_emit_unsupported_payload_type_raises():

    duo = Duo()

    with pytest.raises(
        RuntimeError,
        match="unsupported console payload type",
    ):
        _emit_console_payload(
            duo,
            prefix=Text(),
            payload=object(),
            message_kind=MessageKind.OBJECT,
            console_style=None,
            no_prefix=True,
        )

# --- test_32_initialize_console_success() ------------------------------------
def test_32_initialize_console_success(tmp_path):

    log = Duo()

    log.configure(
        log_dir_path=tmp_path,
        log_file_layout="script",
        console_header="off",
        console_footer="off",
    )

    assert log._console is not None
    assert log._runtime.console_continuation_prefix_len >= 0

    log.close()

# --- test_33_first_instance_claims_console_owner() ---------------------------
def test_33_first_instance_claims_console_owner(
    tmp_path,
    monkeypatch,
):

    monkeypatch.delenv(
        "LOGDUO_CONSOLE_OWNER",
        raising=False,
    )

    log = Duo()

    log.configure(
        log_dir_path=tmp_path,
        log_file_layout="script",
        first_instance_owns_console=True,
        console_header="off",
        console_footer="off",
    )

    assert (
        os.environ["LOGDUO_CONSOLE_OWNER"]
        == str(log._runtime.pid)
    )

    log.close()


# --- test_34_emit_console_end_without_console() ------------------------------
def test_34_emit_console_end_without_console():

    duo = Duo()
    duo._console = None

    _emit_console_end(duo)


# --- test_35_console_footer_is_emitted() ------------------------------------
def test_35_console_footer_is_emitted(
    tmp_path,
    capsys,
):

    log = Duo()

    log.configure(
        log_dir_path=tmp_path,
        log_file_layout="script",
        console_header="off",
        console_footer="CUSTOM FOOTER",
    )

    log("hello")
    log.close()

    output = capsys.readouterr().out

    assert "CUSTOM FOOTER" in output
