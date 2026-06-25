"""
test_non_script_mode.py

Last edited: 2026-06-12
"""

import subprocess
import sys


# --- test_interactive_like_session_uses_session_name() -----------------------
def test_interactive_like_session_uses_session_name(tmp_path):


    code = f"""
import os    
import coverage

print("COVERAGE_PROCESS_START =", os.getenv("COVERAGE_PROCESS_START"))

print("coverage version:", coverage.__version__)

from logduo import Duo

log = Duo()

log.configure(log_dir_path={str(tmp_path)}, log_dir_layout="script")

log("hello")
out = log.main_log_file_path
print(f"out = {{out}}")
log.close()
"""

    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True,
        text=True,
    )
    print("STDOUT:")

    print(result.stdout)

    print("STDERR:")

    print(result.stderr)

    assert result.returncode == 0

    out = tmp_path / "session" / "session.log"
    print(out)

    text = out.read_text()
    print(text)
    print("text should contain 'hello' and 'session'")

    assert "hello" in text
    assert "session" in text     # assert "python -c" not treated as script