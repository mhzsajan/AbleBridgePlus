"""Import every module and report all ImportErrors to find missing glue."""
import importlib
import sys
import traceback

sys.path.insert(0, '.')

modules = [
    'MCP_Server.server',
    'MCP_Server.state',
    'MCP_Server.validation',
    'MCP_Server.connections.ableton',
    'MCP_Server.connections.m4l',
    'MCP_Server.cache.browser',
    'MCP_Server.tools._base',
    'MCP_Server.tools.tracks',
    'MCP_Server.tools.clips',
    'MCP_Server.tools.devices',
    'MCP_Server.tools.mixer',
    'MCP_Server.tools.browser',
    'MCP_Server.tools.automation',
    'MCP_Server.tools.arrangement',
    'MCP_Server.tools.creative',
    'MCP_Server.tools.grid',
    'MCP_Server.tools.m4l_tools',
    'MCP_Server.tools.midi_cc',
    'MCP_Server.tools.scenes',
    'MCP_Server.tools.session',
    'MCP_Server.tools.snapshots',
    'MCP_Server.tools.workflows',
    'MCP_Server.tools.midi_mapping',
    'MCP_Server.tools.plugin_management',
    'MCP_Server.tools.video_routing',
    'MCP_Server.tools.setlist_management',
    'MCP_Server.tools.performance',
    'MCP_Server.tools.quick_presets',
    'MCP_Server.tools.audio_analysis',
    'MCP_Server.tools.template_system',
    'MCP_Server.tools.advanced_routing',
    'MCP_Server.tools.ai_integration',
    'MCP_Server.tools.show_clock',
    'MCP_Server.tools.emergency_control',
    'MCP_Server.tools.session_backup',
    'MCP_Server.tools.performance_analytics',
    'MCP_Server.tools.audio_presets',
    'MCP_Server.tools.video_lighting',
    'MCP_Server.tools.ai_enhancement',
    'MCP_Server.tools.scene_macros',
    'MCP_Server.tools.backup_presets',
]

ok = True
for name in modules:
    try:
        importlib.import_module(name)
        print(f"OK   {name}")
    except Exception as e:
        ok = False
        print(f"FAIL {name}: {type(e).__name__}: {e}")
        tb = traceback.format_exc().splitlines()
        for line in tb[-4:]:
            print("     " + line.strip())

print()
print("ALL OK" if ok else "SOME FAILED")