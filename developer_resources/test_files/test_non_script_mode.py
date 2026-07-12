"""
test_non_script_mode.py

Last edited: 2026-07-11
"""

import subprocess
import sys


# --- test_interactive_like_session_uses_session_name() -----------------------
"""
test_non_script_mode.py
"""

import subprocess
import sys
import textwrap


# --- test_python_c_uses_session_name() ----------------------------------------
def test_python_c_uses_session_name(tmp_path):
    code = textwrap.dedent(
        f"""
        import sys

        from logduo import Duo

        assert sys.argv[0] == "-c"

        log = Duo()
        log.configure(
            log_dir_path={str(tmp_path)!r},
            log_file_layout="script",
        )

        log("hello")
        print(log.main_log_file_path)
        log.close()
        """
    )

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, (
        "Python -c subprocess failed.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )

    expected_log_path = tmp_path / "session" / "session.log"

    assert expected_log_path.is_file()

    text = expected_log_path.read_text(encoding="utf-8")

    assert "hello" in text
