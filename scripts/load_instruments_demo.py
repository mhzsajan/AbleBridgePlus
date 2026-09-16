"""Load instruments onto the AI tracks: refresh browser cache, resolve URIs, load, verify."""
import asyncio
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from MCP_Server.server import MCPServer  # noqa: E402


async def call(server, name, args=None):
    r = await server.handle_request({'method': 'tools/call', 'params': {
        'name': name, 'arguments': args or {}}})
    return r.get('content', [{}])[0].get('text', '')


def pick_uri(raw, want):
    """Parse search_browser output lines, pick exact-name match or first .adg preset."""
    try:
        msg = json.loads(raw).get('message', '')
    except Exception:
        msg = raw
    items = []
    lines = msg.split('\n')
    for i, ln in enumerate(lines):
        if '[loadable]' in ln:
            name = ln.split('[loadable]')[0].strip().lstrip('*-').strip()
            uri = None
            for j in range(i + 1, min(i + 5, len(lines))):
                if lines[j].strip().startswith('URI:'):
                    uri = lines[j].split('URI:')[1].strip()
                    break
            if uri:
                items.append((name, uri))
    for name, uri in items:
        if name.lower() == want.lower():
            return uri
    for name, uri in items:
        if '.adg' in name.lower():
            return uri
    return items[0][1] if items else None


async def main():
    server = MCPServer()

    # 1. Refresh browser cache in THIS process (it dies with the process otherwise)
    await call(server, 'refresh_browser_cache_tool', {})
    for _ in range(60):
        await asyncio.sleep(5)
        status = await call(server, 'get_browser_cache_status', {})
        if 'scan in progress' not in status:
            print("cache:", status[:160])
            break

    # 2. Search + load instruments
    loads = [(5, 'Drift', 'AI Chords'), (6, 'Analog', 'AI Bass'), (7, 'Operator', 'AI Melody')]
    for idx, instr, nm in loads:
        raw = await call(server, 'search_browser', {'query': instr, 'category': 'instruments'})
        uri = pick_uri(raw, instr)
        if not uri:
            print(f"{nm} <- {instr}: NO URI FOUND in search results")
            continue
        r = await call(server, 'load_instrument_or_effect', {'track_index': idx, 'uri': uri})
        print(f"{nm} <- {instr} [{uri[:48]}]: {r[:100]}")

    # 3. Verify devices landed
    for idx, nm in [(5, 'AI Chords'), (6, 'AI Bass'), (7, 'AI Melody')]:
        dev = await call(server, 'get_track_devices', {'track_index': idx})
        print(f"devices on {nm}:", dev[:150])

    # 4. Fire the clips (session-view clips need firing, not just transport play)
    print("play:", (await call(server, 'start_playback'))[:60])
    for idx in (5, 6, 7):
        print(f"fire {idx}:", (await call(server, 'fire_clip', {'track_index': idx, 'clip_index': 0}))[:70])


if __name__ == '__main__':
    asyncio.run(main())
