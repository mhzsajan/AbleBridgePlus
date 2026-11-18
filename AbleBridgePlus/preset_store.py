"""Resolve the routing-preset file (remote-script side, inside Ableton Live).

Keep this in sync with ``MCP_Server/preset_store.py`` - both halves must read
and write the SAME file. Python 2.7 compatible (Live 10's embedded Python) as
well as Python 3.x (Live 11/12): no f-strings, no annotations, no pathlib.

Resolution order (first match wins):

1. ``ABLETON_BRIDGE_PRESET_PATH``  - full path to ``routing-presets.json``.
2. ``ABLETON_BRIDGE_PRESET_DIR``   - directory holding that file.
3. ``~/.ableton-bridge/config.json`` - ``routing_presets_path`` / ``routing_presets_dir``.
4. Legacy ``~/.ableton-bridge/routing-presets.json``.

Ableton inherits these environment variables from the shell that launched it,
and the config file is written by ``scripts/setup.sh`` on each Mac. That is
what makes the presets portable: the file itself lives in the AbleSet project
folder and travels with it.
"""
from __future__ import absolute_import, print_function, unicode_literals

import io
import json
import os

_HOME = os.path.expanduser("~")
CONFIG_PATH = os.path.join(_HOME, ".ableton-bridge", "config.json")
LEGACY_PATH = os.path.join(_HOME, ".ableton-bridge", "routing-presets.json")
FILENAME = "routing-presets.json"

try:  # Python 2 has basestring, Python 3 does not.
    _STRING_TYPES = (basestring,)  # noqa: F821
except NameError:
    _STRING_TYPES = (str,)


def _from_dir(directory):
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
        with io.open(CONFIG_PATH, "r", encoding="utf-8") as handle:
            config = json.load(handle)
        if isinstance(config, dict):
            path = config.get("routing_presets_path")
            if isinstance(path, _STRING_TYPES) and path.strip():
                return os.path.expanduser(path.strip())
            directory = config.get("routing_presets_dir")
            if isinstance(directory, _STRING_TYPES) and directory.strip():
                return _from_dir(directory.strip())
    except (IOError, OSError, ValueError):
        pass

    return LEGACY_PATH
