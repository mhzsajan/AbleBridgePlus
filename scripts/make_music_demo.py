"""Music demo: build Chords + Bass + Melody tracks via AbleBridgePlus tools."""
import asyncio
import json
import re
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from MCP_Server.server import MCPServer  # noqa: E402


async def call(server, name, args=None):
    r = await server.handle_request({'method': 'tools/call', 'params': {
        'name': name, 'arguments': args or {}}})
    return r.get('content', [{}])[0].get('text', '')


def midi_note(pitch, start, dur, vel=100):
    return {"pitch": pitch, "start_time": start, "duration": dur, "velocity": vel, "mute": False}


async def find_track_index(server, name):
    """Find a track index by name from get_all_tracks_info output."""
    txt = await call(server, 'get_all_tracks_info')
    for m in re.finditer(r'[Tt]rack\s*(\d+)[^"]*?"?[^"\n]*', txt):
        pass
    # Robust: look for "index": N near the name, or name near index
    idx_matches = [(m.start(), int(m.group(1))) for m in re.finditer(r'"?index"?\s*[:=]\s*(\d+)', txt)]
    for pos, idx in idx_matches:
        window = txt[max(0, pos - 300): pos + 300]
        if name.lower() in window.lower():
            return idx
    return None


async def main():
    server = MCPServer()

    info = await call(server, 'get_session_info')
    print("session:", info[:200])

    # 1. Create three fresh MIDI tracks at the end
    for _ in range(3):
        print("create:", (await call(server, 'create_midi_track', {'index': -1}))[:100])

    # 2. Rename them (they are the last three)
    all_txt = await call(server, 'get_all_tracks_info')
    n = len(re.findall(r'"?index"?\s*[:=]', all_txt))
    print("total tracks now:", n)
    names = ['AI Chords', 'AI Bass', 'AI Melody']
    for i, nm in enumerate(names):
        idx = n - 3 + i
        print(f"rename {idx} -> {nm}:", (await call(server, 'set_track_name', {'track_index': idx, 'name': nm}))[:80])

    # 3. Resolve indices by name
    chord_i = await find_track_index(server, 'AI Chords')
    bass_i = await find_track_index(server, 'AI Bass')
    mel_i = await find_track_index(server, 'AI Melody')
    print("resolved indices:", chord_i, bass_i, mel_i)
    if chord_i is None:
        chord_i, bass_i, mel_i = n - 3, n - 2, n - 1
        print("fallback indices:", chord_i, bass_i, mel_i)

    # 4. Compose: Am | F | C | G — 2 bars of 4/4 (8 beats)
    chords = [(57, [57, 60, 64]), (53, [53, 57, 60]), (48, [48, 52, 55]), (55, [55, 59, 62])]
    chord_notes = []
    for ci, (_, ch) in enumerate(chords):
        for p in ch:
            chord_notes.append(midi_note(p, ci * 2.0, 1.6, vel=88))
    # Melody: A minor pentatonic hook
    mel = [(69, 0.0, 0.75), (72, 0.75, 0.5), (76, 1.25, 0.75), (74, 2.0, 1.5),
           (72, 3.5, 0.5), (69, 4.0, 0.75), (67, 4.75, 1.25), (64, 6.0, 1.0), (67, 7.0, 1.0)]
    mel_notes = [midi_note(p, s, d, vel=108) for p, s, d in mel]
    # Bass: pumping eighths on roots A1 F1 C1 G1
    bass_roots = [33, 29, 24, 31]
    bass_notes = []
    for ci, root in enumerate(bass_roots):
        for e in range(4):
            bass_notes.append(midi_note(root, ci * 2.0 + e * 0.5, 0.45, vel=105 if e % 2 == 0 else 85))

    # 5. Clips + notes
    for idx, slot, length, label, notes, nm in [
        (chord_i, 0, 8.0, "chords", chord_notes, 'AI Chords - Am F C G'),
        (bass_i, 0, 8.0, "bass", bass_notes, 'AI Bassline'),
        (mel_i, 0, 8.0, "melody", mel_notes, 'AI Melody Hook'),
    ]:
        r = await call(server, 'create_clip', {'track_index': idx, 'clip_index': slot, 'length': length})
        print(f"create_clip {label}:", r[:90])
        r = await call(server, 'add_notes_to_clip', {'track_index': idx, 'clip_index': slot, 'notes': notes})
        print(f"notes {label}:", r[:90])
        await call(server, 'set_clip_name', {'track_index': idx, 'clip_index': slot, 'name': nm})

    # 6. Tempo, play, and FIRE the clips (session-view clips don't play until fired)
    print("tempo:", (await call(server, 'set_tempo', {'tempo': 110}))[:80])
    print("play:", (await call(server, 'start_playback'))[:80])
    for idx in (chord_i, bass_i, mel_i):
        print(f"fire track {idx}:", (await call(server, 'fire_clip', {'track_index': idx, 'clip_index': 0}))[:70])
    print("DONE - 3 AI tracks created with a 2-bar Am-F-C-G loop @110 BPM, playing now.")


if __name__ == '__main__':
    asyncio.run(main())
