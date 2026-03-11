# core/version.py

import json
import os
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


def _run_git(*args) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args],
        capture_output=True, text=True, cwd=VERSION_FILE.parent
    )


def git_push_version(version: str, message: str = None) -> tuple[bool, str]:
    """
    Commit version.json dan push ke GitHub via Personal Access Token.
    Token diambil dari env var GITHUB_TOKEN.
    """
    msg = message or f"v{version}"
    token = os.getenv("GITHUB_TOKEN")

    if not token:
        return False, "GITHUB_TOKEN tidak ditemukan di .env"

    try:
        # Ambil repo info dari version.json
        info = _read()
        repo = info.get("repository", "")
        if not repo:
            return False, "Repository tidak ditemukan di version.json"

        auth_url = f"https://{token}@github.com/{repo}.git"

        # Commit
        _run_git("add", "version.json")
        result = _run_git("commit", "-m", msg)
        if result.returncode != 0 and "nothing to commit" in result.stdout:
            return False, "Tidak ada perubahan untuk di-commit."

        # Tag
        _run_git("tag", f"v{version}")

        # Push dengan token
        result = _run_git("push", auth_url, "HEAD")
        if result.returncode != 0:
            err = result.stderr.strip().replace(token, "***")
            if "fatal" in err.lower() or "error" in err.lower():
                return False, err

        # Push tags
        result = _run_git("push", auth_url, "--tags")
        if result.returncode != 0:
            err = result.stderr.strip().replace(token, "***")
            if "fatal" in err.lower() or "error" in err.lower():
                return False, err

        return True, f"Pushed v{version} to {repo}"

    except FileNotFoundError:
        return False, "Git tidak ditemukan. Pastikan git terinstall."
    except Exception as e:
        return False, str(e)

