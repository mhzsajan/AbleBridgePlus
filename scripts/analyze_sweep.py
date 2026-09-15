"""Analyze a sweep report: bucket handled errors by message type."""
import json
import re
import sys
from collections import Counter

path = sys.argv[1] if len(sys.argv) > 1 else 'tool_test_report.txt'
txt = open(path, encoding='utf-8').read()

# --- Stats line ---
m = re.search(r'OK: (\d+)  ERROR\(handled\): (\d+)  EXCEPTION: (\d+)  TIMEOUT: (\d+)  SKIPPED\(destructive\): (\d+)', txt)
if m:
    print(f"STATS ok={m.group(1)} err={m.group(2)} exc={m.group(3)} to={m.group(4)} skip={m.group(5)}")

# --- Exceptions ---
print("\n=== EXCEPTIONS ===")
exc = re.search(r'--- EXCEPTIONS \(likely bugs\) ---\n(.*?)\n\n--- TIMEOUTS', txt, re.S)
if exc:
    for line in exc.group(1).strip().splitlines():
        print(' ', line[:150])

# --- Timeouts ---
print("\n=== TIMEOUTS ===")
to = re.search(r'--- TIMEOUTS ---\n(.*?)\n\n--- HANDLED', txt, re.S)
if to:
    for line in to.group(1).strip().splitlines():
        print(' ', line)

# --- Handled errors ---
print("\n=== HANDLED ERROR BUCKETS ===")
herr = re.search(r'--- HANDLED ERRORS \(check if expected\) ---\n(.*?)\n\n--- OK', txt, re.S)
buckets = Counter()
toolmap = {}
if herr:
    sec = herr.group(1)
    # entries: name {json} -> { ...json... }
    for name, args, body in re.findall(r'(\S+) (\{.*?\}) -> (\{.*\})', sec):
        try:
            msg = json.loads(body).get('message', '')
        except Exception:
            msg = body[:80]
        if 'missing' in msg:
            b = 'MISSING ARGS (stub tool / empty schema)'
        elif 'not found' in msg or msg.startswith('No '):
            b = 'NOT FOUND (bad test arg)'
        elif 'connection' in msg.lower() or 'Ableton' in msg:
            b = 'CONNECTION'
        elif 'invalid' in msg.lower():
            b = 'INVALID INPUT'
        elif 'requires' in msg:
            b = 'REQUIRES (bad test arg)'
        else:
            b = msg[:60]
        buckets[b] += 1
        toolmap.setdefault(b, []).append(name)
for b, c in buckets.most_common():
    print(f"{c:4d}  {b}")
    if c < 15:
        print(f"        tools: {', '.join(toolmap[b])}")

# --- OK tools ---
oks = re.findall(r'^(get_|set_|create_|delete_|list_|save_|load_|fire_|stop_|start_|arm_|disarm_|select_|refresh_|ping_|search_|analyze_|snapshot_|restore_|morph_|compare_|export_|track_|play_|jump_|panic_|activate_|backup_|configure_|assign_|send_|quantize_|transpose_|capture_|manage_|simpler_|sliced_|audio_to_midi|duplicate_|group_|freeze_|unfreeze_|crop_|reverse_|nudge_|tap_|continue_|trigger_|undo|redo)[\w]* -> .*?$', txt, re.M)
print(f"\nOK tools: {len(oks)}")