"""
single_test.py

Deep debugging

Last edited: 2026-06-11
"""

from logduo import Duo





# --- test_21_console_verbosity_zero_suppresses_console_output() ------------------
def test_21_console_verbosity_zero_suppresses_console_output(
    tmp_path,
    capsys,
):
    print(f"str(tmp_path) = {str(tmp_path)}")
    log = Duo()

    log.configure(log_dir_path=str(tmp_path), console_verbosity=0, log_dir_layout="script", log_verbosity=0)

    log("hello world")

    console_output = capsys.readouterr().out

    print(" ")
    print(" *******************************")
    print("test_21_console_verbosity_zero_suppresses_all_output()")
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


