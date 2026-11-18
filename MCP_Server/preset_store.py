"""Resolve the one routing-preset file both halves of AbleBridgePlus use.

The MCP tools in ``tools/output_routing.py`` WRITE presets here with
``save_output_preset``; the remote script inside Live (``AbleBridgePlus/
handlers/profile.py``) READS the same file when an AbleSet canvas button sends
``/profile/pc`` or ``/profile/wing``. They must agree on one path.

Until v0.9.2 both sides hardcoded ``~/.ableton-bridge/routing-presets.json``,
which is machine-local: copying an AbleSet project to another Mac did not carry
the presets. From v0.9.3 the path is configurable so the file can live inside
the project's ``AbleSet/AudioProfiles/`` folder and travel with the project.

Resolution order (first match wins):

1. ``ABLETON_BRIDGE_PRESET_PATH``  - full path to ``routing-presets.json``.
2. ``ABLETON_BRIDGE_PRESET_DIR``   - directory holding that file.
3. ``~/.ableton-bridge/config.json`` - keys ``routing_presets_path`` (full path)
   or ``routing_presets_dir`` (directory). ``scripts/setup.sh`` in
   ``mhzsajan/ableset-show-profile`` writes this on each Mac.
4. Legacy ``~/.ableton-bridge/routing-presets.json`` - keeps existing setups
   working and is used when no project-local path has been configured.

The path is resolved at every call (not once at import) so a freshly copied
project starts working without restarting the MCP server.
"""
from __future__ import annotations

import json
import os

_HOME = os.path.expanduser("~")
CONFIG_PATH = os.path.join(_HOME, ".ableton-bridge", "config.json")
LEGACY_PATH = os.path.join(_HOME, ".ableton-bridge", "routing-presets.json")
FILENAME = "routing-presets.json"


def _from_dir(directory):
    """Directory (absolute or ~/...) -> full preset file path."""
    if directory:
        return os.path.join(os.path.expanduser(directory), FILENAME)
    return None


def resolve_preset_path():
    """Return the absolute path to ``routing-presets.json`` (first match wins)."""
    explicit = os.environ.get("ABLETON_BRIDGE_PRESET_PATH")
    if explicit and explicit.strip():
        return os.path.expanduser(explicit.strip())

    env_dir = os.environ.get("ABLETON_BRIDGE_PRESET_DIR")
    if env_dir and env_dir.strip():
        return _from_dir(env_dir.strip())

    try:
        with open(CONFIG_PATH, encoding="utf-8") as handle:
            config = json.load(handle)
        if isinstance(config, dict):
            path = config.get("routing_presets_path")
            if isinstance(path, str) and path.strip():
                return os.path.expanduser(path.strip())
            directory = config.get("routing_presets_dir")
            if isinstance(directory, str) and directory.strip():
                return _from_dir(directory.strip())
    except (OSError, ValueError):
        pass

    return LEGACY_PATH


def resolve_preset_dir():
    """Return the directory that holds the resolved preset file.

    Handy for creating the folder before the first save.
    """
    return os.path.dirname(resolve_preset_path())
