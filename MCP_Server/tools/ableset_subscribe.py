"""Tools to ask AbleSet to push its show-state OSC to the bridge.

AbleSet owns the show state (song name, section, start/end, playing flag). The
bridge already has a listener (``start_ableset_listener`` / ``get_ableset_state``
in ``live_show_bridge.py``) but no way to *request* the subscription: AbleSet
normally has to be told to subscribe, and in practice its own UI is the most
reliable way to do that.

These tools send ``/subscribe`` (and ``/unsubscribe``) to AbleSet over OSC and
then actually check whether state arrived. They deliberately report failure
honestly instead of claiming success when AbleSet ignores the message.

The shared OSC helper is imported from live_show_bridge — this module does not
modify that file.
"""
from __future__ import annotations

import json
import time
from typing import Any, Dict

from mcp.server.fastmcp import Context

from MCP_Server.tools._base import _tool_handler
from MCP_Server.tools.live_show_bridge import (
    _ableset_snapshot,
    _send_osc_message,
    _start_ableset_listener,
)

try:
    from pythonosc.udp_client import SimpleUDPClient
except ImportError:  # pragma: no cover - dependency is declared in pyproject
    SimpleUDPClient = None

_MANUAL_STEPS = (
    "Open http://127.0.0.1/settings/osc → OSC Command Tester and send "
    "`/subscribe 127.0.0.1 39052 AbleBridgePC` manually; an OSC connection "
    "with Send Address 127.0.0.1:39052 may also be required."
)


def _valid_port(value: Any, label: str) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError):
        raise ValueError("{0} must be an integer port".format(label))
    if not 1 <= port <= 65535:
        raise ValueError("{0} must be between 1 and 65535".format(label))
    return port


def _send_int_tagged_subscribe(host: str, port: int, listen_port: int,
                               name: str, fine: bool) -> Dict[str, Any]:
    """Retry with python-osc's native ``,i`` tag for the port number.

    ``live_show_bridge._send_osc_message`` coerces ints to floats for the WING
    console (which ignores ``,i``). AbleSet may expect the opposite — an
    integer port tag — so this best-effort retry sends the same message with
    the port left as a Python int. It is used only if the first attempt did not
    produce state.
    """
    if SimpleUDPClient is None:
        return {"sent": False,
                "error": "python-osc is not installed (python-osc>=1.8.0 required)"}
    args = [int(listen_port), str(name)] + ([True] if fine else [])
    try:
        SimpleUDPClient(str(host), int(port)).send_message("/subscribe", args)
        return {"sent": True, "error": None, "args": args, "type_tag_port": "i"}
    except Exception as exc:
        return {"sent": False,
                "error": "{0}: {1}".format(type(exc).__name__, exc)}


def register_tools(mcp):
    @mcp.tool()
    @_tool_handler("subscribing AbleSet to the bridge listener")
    def subscribe_ableset(ctx: Context, host: str = "127.0.0.1",
                          port: int = 39051, name: str = "AbleBridge",
                          fine: bool = False, listen_port: int = 39052) -> str:
        """Ask AbleSet to push show-state OSC to the bridge's listener.

        Sends ``/subscribe <listen_port> <name>`` (plus ``true`` when ``fine``)
        to AbleSet, then waits briefly and reads the listener snapshot to see
        whether state ACTUALLY arrived. If nothing arrived the result says so
        and gives the manual AbleSet UI recipe — this tool does not pretend the
        subscription worked.

        Parameters:
        - host: AbleSet host (default 127.0.0.1)
        - port: AbleSet's OSC listen port (default 39051 — do NOT use 39052)
        - name: subscription name AbleSet should use (default 'AbleBridge')
        - fine: request fine-grained updates
        - listen_port: bridge listener port (default 39052)
        """
        port = _valid_port(port, "port")
        listen_port = _valid_port(listen_port, "listen_port")
        name = str(name).strip()
        if not name:
            raise ValueError("name must not be empty")

        before = _ableset_snapshot()
        before_count = len(before.get("state") or {})
        listener = _start_ableset_listener(listen_port)

        args: list = [listen_port, name] + ([True] if fine else [])
        primary = _send_osc_message(host, port, "/subscribe", args)

        time.sleep(1.5)
        after = _ableset_snapshot()
        after_count = len(after.get("state") or {})

        retry = None
        if after_count == 0 and primary.get("sent"):
            # The shared helper coerces the port to a float for the WING; some
            # AbleSet builds only accept an integer-tagged port. Try that once.
            retry = _send_int_tagged_subscribe(host, port, listen_port, name, fine)
            if retry.get("sent"):
                time.sleep(1.5)
                after = _ableset_snapshot()
                after_count = len(after.get("state") or {})

        got_state = after_count > 0
        already = before_count > 0 and not got_state
        if got_state:
            message = ("AbleSet is pushing state to the bridge "
                       "({0} OSC address(es) received).".format(after_count))
        elif already:
            message = ("State was already in the listener before this call; "
                       "the subscription appears to be established.")
        else:
            message = ("subscribe command sent, but AbleSet did not push state "
                       "— " + _MANUAL_STEPS)

        return json.dumps({
            "status": "ok" if got_state or already else "no_data",
            "message": message,
            "target": "{0}:{1}".format(host, port),
            "address": "/subscribe",
            "args": args,
            "primary_send": primary,
            "int_tagged_retry": retry,
            "listener_start": listener,
            "state_addresses_before": before_count,
            "state_addresses_after": after_count,
            "snapshot": after,
            "manual_steps": _MANUAL_STEPS,
            "note": ("The bridge can send /subscribe but cannot configure "
                     "AbleSet; the manual UI steps are often required."),
        })

    @mcp.tool()
    @_tool_handler("unsubscribing AbleSet from the bridge listener")
    def unsubscribe_ableset(ctx: Context, host: str = "127.0.0.1",
                            port: int = 39051, name: str = "AbleBridge") -> str:
        """Ask AbleSet to stop pushing show-state OSC to the bridge.

        Sends ``/unsubscribe <name>`` to AbleSet's OSC port. AbleSet's exact
        argument shape for /unsubscribe is not guaranteed — verify in its OSC
        Command Tester if the state keeps arriving.

        Parameters:
        - host: AbleSet host (default 127.0.0.1)
        - port: AbleSet's OSC listen port (default 39051)
        - name: subscription name to remove
        """
        port = _valid_port(port, "port")
        name = str(name).strip()
        if not name:
            raise ValueError("name must not be empty")
        sent = _send_osc_message(host, port, "/unsubscribe", [name])
        return json.dumps({
            "status": "ok" if sent.get("sent") else "error",
            "message": ("/unsubscribe sent to {0}:{1}".format(host, port)
                        if sent.get("sent") else
                        "Could not send /unsubscribe: {0}".format(sent.get("error"))),
            "target": "{0}:{1}".format(host, port),
            "address": "/unsubscribe",
            "args": [name],
            "send_result": sent,
            "note": "Check the AbleSet OSC Command Tester if state keeps arriving.",
        })
