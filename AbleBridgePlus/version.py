"""Version of the remote script that runs *inside* Ableton Live.

This file lives in the Remote Script folder because the script runs in Live's
embedded Python and cannot import the MCP_Server package. It is the single
source of truth for the script side; `tests/test_version_sync.py` asserts it
agrees with pyproject.toml, MCP_Server/version.py and doctor's
EXPECTED_SCRIPT_VERSION, so a release bump cannot ship a drifting script.

Where the user sees it (inside Ableton):
  * status bar on startup: "AbleBridgePlus v<here> ready - TCP 9877 / UDP 9882"
  * status bar when an AI client connects
  * Live's Log.txt, and the `get_session_info` reply that `doctor` verifies
"""

from __future__ import absolute_import, print_function, unicode_literals

SCRIPT_VERSION = "0.8.0"
