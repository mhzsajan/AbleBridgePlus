"""ExtensionsSDKClient — optional HTTP client for the Ableton Extensions SDK bridge.

The bridge is a companion Node.js process (AbletonParameterBridge) that communicates
with Ableton Live via the official Extensions SDK introduced in Live 12.4.5 Suite.
It exposes parameter reads/writes via HTTP on port 9883.

When active, parameter tools prefer this bridge over the _Framework Remote Script
because the Extensions SDK uses async LiveAPI calls — more reliable for VST3/AU
plugins, especially on Apple Silicon.

**Setup (optional):**
  1. Build and install AbletonParameterBridge (see docs/extensions_sdk_bridge.md)
  2. Run: npx extensions-cli run --live "/Applications/Ableton Live 12 Beta.app" .
  3. The MCP server detects it automatically on next tool call

**Graceful fallback:**
  If the bridge is not running, all tools fall back to M4L → _Framework automatically.
  Nothing breaks. Use get_bridge_status to check which transport is active.

Requires:
  - Ableton Live 12.4.5+ Suite (beta)
  - Node.js v20+
  - Ableton Extensions SDK (download from ableton.com/beta)
"""

import json
import logging
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

logger = logging.getLogger("AbletonBridge")

# HTTP port for the Extensions SDK bridge (distinct from M4L UDP 9878/9879,
# dashboard 9880, singleton lock 9881, and UDP real-time params 9882)
SDK_BRIDGE_HOST = "127.0.0.1"
SDK_BRIDGE_PORT = 9883


class ExtensionsSDKClient:
    """Thin HTTP client for the AbletonParameterBridge Extensions SDK server."""

    def __init__(self, host: str = SDK_BRIDGE_HOST, port: int = SDK_BRIDGE_PORT):
        self.base_url = f"http://{host}:{port}"

    def _get(self, path: str, timeout: float = 2.0) -> dict:
        with urllib.request.urlopen(f"{self.base_url}{path}", timeout=timeout) as resp:
            return json.loads(resp.read().decode())

    def _post(self, path: str, data: dict, timeout: float = 2.0) -> dict:
        body = json.dumps(data).encode()
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())

    def is_available(self) -> bool:
        """Check if the Extensions SDK bridge is running."""
        try:
            self._get("/health", timeout=1.0)
            return True
        except Exception:
            return False

    def get_status(self) -> Dict[str, Any]:
        """Get bridge status including connection info."""
        try:
            return self._get("/status")
        except Exception as e:
            return {"error": str(e), "available": False}

    def get_device_parameters(self, track_index: int, device_index: int) -> Dict[str, Any]:
        """Get all parameters for a device via the Extensions SDK."""
        try:
            return self._get(f"/device/{track_index}/{device_index}/parameters")
        except Exception as e:
            return {"error": str(e)}

    def set_device_parameter(
        self, track_index: int, device_index: int, parameter_index: int, value: float
    ) -> Dict[str, Any]:
        """Set a device parameter via the Extensions SDK."""
        try:
            return self._post(
                f"/device/{track_index}/{device_index}/parameter/{parameter_index}",
                {"value": value},
            )
        except Exception as e:
            return {"error": str(e)}

    def get_hidden_parameters(self, track_index: int, device_index: int) -> Dict[str, Any]:
        """Get hidden/non-automatable parameters via the Extensions SDK."""
        try:
            return self._get(f"/device/{track_index}/{device_index}/hidden-parameters")
        except Exception as e:
            return {"error": str(e)}


# Singleton instance
_sdk_client: Optional[ExtensionsSDKClient] = None


def get_sdk_client() -> ExtensionsSDKClient:
    """Get or create the Extensions SDK client singleton."""
    global _sdk_client
    if _sdk_client is None:
        _sdk_client = ExtensionsSDKClient()
    return _sdk_client


def is_sdk_available() -> bool:
    """Check if the Extensions SDK bridge is available."""
    return get_sdk_client().is_available()
