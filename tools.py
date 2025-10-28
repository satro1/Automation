import os
import shlex
import subprocess
from typing import List


def get_weather(city: str) -> str:
    """Get weather for a given city."""
    return f"It's always sunny in {city}!"


def run_cmd(command: str, timeout: int = 30) -> str:
    """Run a shell command and return its stdout/stderr.

    WARNING: All previous safety checks (environment guard and blacklist)
    have been removed. This will execute the provided command directly in
    the system shell. Use with extreme caution.
    """
    try:
        # Execute via the system shell so the agent can run arbitrary commands.
        completed = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        out = completed.stdout.strip()
        err = completed.stderr.strip()
        return (out + ("\n" + err if err else "")).strip() or "(no output)"
    except subprocess.TimeoutExpired:
        return "Command timed out"
    except Exception as e:
        return f"Failed to execute command: {e}"


tools = [get_weather, run_cmd]