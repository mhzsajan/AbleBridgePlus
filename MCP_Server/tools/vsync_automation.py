"""Videosync2 show automation tools (v0.8).

Videosync2 maps Live track mixers to layer visibility: volume = opacity,
mute = hidden. These tools write arrangement-level mixer automation so
the whole video show is baked into the timeline — zero buttons for the
baseline show, MIDI buttons only for exceptions, AI optional (and
replaceable later by a local-AI rig).
"""
import json

from mcp.server.fastmcp import Context

from MCP_Server.tools._base import _tool_handler
from MCP_Server.connections.ableton import get_ableton_connection


def register_vsync_tools(mcp):
    @mcp.tool()
    @_tool_handler("programming song video automation")
    def program_song_video_automation(ctx: Context, song_name: str,
                                      backdrop_volume: float = 0.85,
                                      sections: list = None) -> str:
        """Bake one song's video automation into the timeline.

        For the locator region matching `song_name`: Main Backdrop gets a
        2-bar fade-in, full level, 2-bar fade-out; Lyrics Video and Live
        Cam are carried silent (hidden) for the whole song. Optional
        `sections` add in-song exceptions, e.g.
        [{"name": "chorus", "at_bar": 57, "layers": {"cam": 0.85}}].

        This is the 'auto-VJ' pass — after running it for every song the
        video show plays itself from the AbleSet jump points.
        """
        ableton = get_ableton_connection()
        return json.dumps(ableton.send_command("program_song_video_automation", {
            "song_name": song_name,
            "backdrop_volume": backdrop_volume,
            "sections": sections or [],
        }))

    @mcp.tool()
    @_tool_handler("setting arrangement mixer automation")
    def set_arrangement_mixer_automation(ctx: Context, track_index: int,
                                         points: list,
                                         parameter_name: str = "volume") -> str:
        """Write arrangement-level automation points for a track mixer
        parameter (volume/panning). points: [{"time": <abs beats>,
        "value": 0..1}]. Creates a 0-beat carrier clip when no clip
        covers the time — envelope host without audible footprint."""
        ableton = get_ableton_connection()
        return json.dumps(ableton.send_command("set_arrangement_mixer_automation", {
            "track_index": track_index,
            "parameter_name": parameter_name,
            "points": points,
        }))

    @mcp.tool()
    @_tool_handler("reading arrangement mixer automation")
    def get_arrangement_mixer_automation(ctx: Context, track_index: int,
                                         parameter_name: str = "volume") -> str:
        """Read back arrangement mixer automation envelopes (diagnostics
        for the video automation pass)."""
        ableton = get_ableton_connection()
        return json.dumps(ableton.send_command("get_arrangement_mixer_automation", {
            "track_index": track_index, "parameter_name": parameter_name}))

    @mcp.tool()
    @_tool_handler("clearing arrangement mixer automation")
    def clear_arrangement_mixer_automation(ctx: Context, track_index: int,
                                           parameter_name: str = "volume") -> str:
        """Remove the mixer automation envelope from every arrangement
        clip on the track (undo an automation pass)."""
        ableton = get_ableton_connection()
        return json.dumps(ableton.send_command("clear_arrangement_mixer_automation", {
            "track_index": track_index, "parameter_name": parameter_name}))

    @mcp.tool()
    @_tool_handler("switching to the backup video path")
    def video_failover(ctx: Context, to_backup: bool = True) -> str:
        """Panic switch between the two video paths: backup default-player
        track (VIDEO, track 0) and the VSync2 Group. Refuses if the backup
        track has no clips. Returns verified mute states."""
        ableton = get_ableton_connection()
        return json.dumps(ableton.send_command("video_failover", {
            "to_backup": bool(to_backup)}))

    @mcp.tool()
    @_tool_handler("setting a video layer level")
    def set_video_layer(ctx: Context, layer: str, level: float) -> str:
        """Manual level (0..1) for a Videosync2 layer: 'backdrop',
        'lyrics', 'cam' or 'all'. NOTE: clip-envelope automation overrides
        manual moves during playback inside its span — clear automation
        first for fully manual control."""
        ableton = get_ableton_connection()
        return json.dumps(ableton.send_command("set_video_layer", {
            "layer": layer, "level": float(level)}))


# The server loop calls module.register_tools(mcp) only.
register_tools = register_vsync_tools
