"""The release version is written down in four places; none may drift.

A version mismatch here is not cosmetic: `doctor` compares the version the
remote script reports from inside Ableton against `EXPECTED_SCRIPT_VERSION`
and warns about "script drift", and the status bar tells the user which build
they are running. Bumping one file and forgetting the others produces exactly
the confusing state this project is trying to eliminate (the old AbletonBridge
4.0.0 vs AbleBridgePlus 0.8.0 version-number reset).

Run with the rest of the suite:  uv run --with pytest pytest tests/ -q
"""

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Every place a release version may be declared, and the literal that anchors it.
VERSION_SOURCES = {
    "pyproject.toml": r'^version\s*=\s*"([^"]+)"',
    "MCP_Server/version.py": r'^__version__\s*=\s*"([^"]+)"',
    "AbleBridgePlus/version.py": r'^SCRIPT_VERSION\s*=\s*"([^"]+)"',
    "MCP_Server/tools/doctor.py": r"^EXPECTED_SCRIPT_VERSION\s*=\s*\"([^\"]+)\"",
}


def _read(rel_path):
    return (ROOT / rel_path).read_text(encoding="utf-8")


def _declared_version(rel_path):
    match = re.search(VERSION_SOURCES[rel_path], _read(rel_path), re.M)
    assert match, "no version literal found in {0}".format(rel_path)
    return match.group(1)


def test_release_version_is_declared_once():
    versions = {path: _declared_version(path) for path in VERSION_SOURCES}
    assert len(set(versions.values())) == 1, (
        "release version drift - these must all match: {0}".format(versions)
    )


def test_remote_script_displays_version_inside_live():
    """The version must actually reach the user's eyes inside Ableton."""
    init_py = _read("AbleBridgePlus/__init__.py")
    assert "from .version import SCRIPT_VERSION" in init_py
    # show_message() writes to Live's status bar - it has to carry the version,
    # not just the ports.
    assert re.search(r"show_message\([^)]*SCRIPT_VERSION", init_py), (
        "AbleBridgePlus/__init__.py no longer shows the version in Live's "
        "status bar"
    )
    # The get_session_info reply (what `doctor` reads) re-exports the same
    # constant instead of carrying its own literal.
    session_py = _read("AbleBridgePlus/handlers/session.py")
    assert "from ..version import SCRIPT_VERSION" in session_py


def test_remote_script_has_no_duplicate_version_literals():
    """The script folder must read its version from version.py only."""
    for rel_path in ("AbleBridgePlus/__init__.py",
                     "AbleBridgePlus/handlers/session.py"):
        assert not re.search(r"\"\d+\.\d+\.\d+\"", _read(rel_path)), (
            "{0} hardcodes a version literal; use SCRIPT_VERSION from "
            "AbleBridgePlus/version.py".format(rel_path)
        )
