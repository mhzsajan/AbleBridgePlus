"""Verify Ritu lyric clips on the live set vs the rendered video's timing map.

Video map: 21 sung lines starting at set-beat 11504 (video frame 0 = beat 11488
= bar 2872.0), 105 BPM. Lyric clip track = 14, Lyrics Video track = 18.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from MCP_Server.server import MCPServer  # noqa: E402

VIDEO_FIRST_BEAT = 11504.0  # first lyric clip position in the set
WINDOW = (11350, 12100)     # arrangement-beat window to inspect

# The 21 lines baked into the video: (relative beat, duration, text)
VIDEO_LINES = [
    (0, 4, "Farkera aaune chaina"),
    (4, 4, "Ma Kunai Ritu Haina"),
    (8, 4.5, "Mero aasha nagara bitla hai timro jindagi"),
    (31.5, 8, "Farkera aaune chaina Ma kunai ritu haina"),
    (39.5, 8, "Mero aasha nagara bitla hai timro jindagi"),
    (56, 8, "Maya dui tarfi hunch ekohoro hudaina"),
    (64, 8, "Mero bishwas chaina ma aauchu aaudina"),
    (72, 8, "Mero vhaaba lai bhuja Bitla hai timro jindagi"),
    (127.5, 8.5, "Kasai ko maya pauna atti nai garo huncha"),
    (136, 8, "Sajilai maya pauna kahilei sakidaina"),
    (144, 8, "Mero vhaba lai bhuja Bitla hai timro jindagi"),
    (167.5, 8, "Farkera aaune chaina Ma kunai ritu haina"),
    (175.5, 8, "Mero aasha nagara bitla hai timro jindagi"),
    (199.5, 8, "Farkera aaune chaina Ma kunai ritu haina"),
    (207.5, 8, "Mero aasha nagara bitla hai timro jindagi"),
    (224, 8, "Maya dui tarfi hunch ekohoro hudaina"),
    (232, 8, "Mero bishwas chaina ma aauchu aaudina"),
    (240, 8, "Mero vhaba lai bhuja Bitla hai timro jindagi"),
    (320, 8, "Kasai ko maya pauna atti nai garo"),
    (328, 8, "Sajilai maya pauna kahilei sakidaina"),
    (336, 8, "Mero vhaba lai bhuja Bitla hai timro jindagi"),
]


async def call(server, name, args=None):
    r = await server.handle_request({'method': 'tools/call', 'params': {
        'name': name, 'arguments': args or {}}})
    return r.get('content', [{}])[0].get('text', '')


async def main():
    server = MCPServer()

    for track_index, label in ((14, 'MIDI +LYRICS +CC'), (18, 'Lyrics Video')):
        print(f'=== track {track_index} ({label}) arrangement clips ===')
        txt = await call(server, 'get_arrangement_clips',
                         {'track_index': track_index})
        # crude JSON parse for start_time/name
        import json as _json
        try:
            data = _json.loads(txt)
            clips = data.get('clips', data if isinstance(data, list) else [])
            shown = 0
            for c in clips:
                st = c.get('start_time', c.get('start', -1))
                if WINDOW[0] <= st <= WINDOW[1]:
                    print(f"  beat {st:9.2f}  len {c.get('duration', '?'):>6}"
                          f"  {c.get('name', '?')}")
                    shown += 1
            if not shown:
                print('  (no clips in Ritu window)')
        except Exception:
            print(txt[:800])

    print()
    print('=== video map check ===')
    print(f"video line 1 at set-beat {VIDEO_FIRST_BEAT}, "
          f"21 lines, last ends ~beat {VIDEO_FIRST_BEAT + 344}")

asyncio.run(main())
