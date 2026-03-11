# core/version.py

import json
import subprocess
from pathlib import Path

VERSION_FILE = Path(__file__).parent.parent / "version.json"


def _read() -> dict:
    with open(VERSION_FILE, "r") as f:
        return json.load(f)


def _write(data: dict):
    with open(VERSION_FILE, "w") as f:
        json.dump(data, f, indent=4)
        f.write("\n")


def get_version() -> str:
    return _read()["version"]


def get_info() -> dict:
    return _read()


def bump(part: str = "patch") -> str:
    """
    Bump versi berdasarkan part: major, minor, atau patch.
    Contoh: 1.0.0 -> patch -> 1.0.1
             1.0.0 -> minor -> 1.1.0
             1.0.0 -> major -> 2.0.0
    """
    data = _read()
    major, minor, patch = map(int, data["version"].split("."))

    if part == "major":
        major += 1
        minor = 0
        patch = 0
    elif part == "minor":
        minor += 1
        patch = 0
    else:
        patch += 1

    new_version = f"{major}.{minor}.{patch}"
    data["version"] = new_version
    _write(data)
    return new_version


def git_push_version(version: str, message: str = None) -> tuple[bool, str]:
    """
    Commit version.json dan push ke GitHub.
    Returns (success, output_or_error).
    """
    msg = message or f"v{version}"

    try:
        cmds = [
            ["git", "add", "version.json"],
            ["git", "commit", "-m", msg],
            ["git", "tag", f"v{version}"],
            ["git", "push"],
            ["git", "push", "--tags"],
        ]

        output_lines = []
        for cmd in cmds:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=VERSION_FILE.parent
            )
            if result.stdout:
                output_lines.append(result.stdout.strip())
            if result.returncode != 0 and result.stderr:
                # git push output sering ke stderr meskipun sukses
                if "error" in result.stderr.lower() or "fatal" in result.stderr.lower():
                    return False, result.stderr.strip()
                output_lines.append(result.stderr.strip())

        return True, "\n".join(output_lines)

    except FileNotFoundError:
        return False, "Git tidak ditemukan. Pastikan git terinstall."
    except Exception as e:
        return False, str(e)
