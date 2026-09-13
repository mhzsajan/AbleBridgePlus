"""
Device management tools for Enhanced AbletonBridge.

These tools handle loading instruments, effects, and managing devices on tracks.
"""

from typing import Any, Dict, Optional


def load_instrument_or_effect(track_index: int, uri: str, track_type: str = "track") -> Dict[str, Any]:
    """
    Load an instrument or effect onto a track using its URI or device name.

    Works for instruments, audio effects, MIDI effects, and presets.
    For native-only devices on Live 12.3+, insert_device_by_name is faster.

    Parameters:
    - track_index: The index of the track to load the instrument on
    - uri: The URI of the instrument/effect, OR a device name (resolved automatically).
    - track_type: "track" (default), "return", or "master"

    You can pass any Ableton instrument, audio effect, or MIDI effect name
    directly — no need to call search_browser first. The server resolves the
    name to the correct URI using the browser cache.

    Common examples:
      Instruments: Analog, Drift, Operator, Sampler, Simpler, Wavetable
      Audio Effects: Reverb, Compressor, EQ Eight, Delay, Auto Filter, Limiter
      MIDI Effects: Arpeggiator, Chord, Scale, Velocity

    Examples:
      load_instrument_or_effect(track_index=0, uri="Wavetable")
      load_instrument_or_effect(track_index=2, uri="Reverb")
      load_instrument_or_effect(track_index=1, uri="Compressor")
      load_instrument_or_effect(track_index=0, uri="Reverb", track_type="master")

    For presets or third-party items, use search_browser() to find the full URI.
    """
    if track_type not in ("track", "return", "master"):
        return {"error": "track_type must be 'track', 'return', or 'master'"}
    
    # This is a placeholder - real implementation would connect to Ableton
    return {
        "track_index": track_index,
        "uri": uri,
        "track_type": track_type,
        "message": "Device loading requires connection to Ableton Live"
    }


def get_device_parameters(track_index: int, device_index: int, track_type: str = "track") -> Dict[str, Any]:
    """
    Get all parameters and their current values for a device on a track.

    Parameters:
    - track_index: The index of the track containing the device
    - device_index: The index of the device on the track
    - track_type: Type of track: "track" (default), "return", or "master"
    """
    if track_type not in ("track", "return", "master"):
        return {"error": "track_type must be 'track', 'return', or 'master'"}
    
    # This is a placeholder - real implementation would connect to Ableton
    return {
        "track_index": track_index,
        "device_index": device_index,
        "track_type": track_type,
        "message": "Device parameter retrieval requires connection to Ableton Live"
    }


def set_device_parameter(track_index: int, device_index: int, parameter_name: str, value: float, track_type: str = "track") -> Dict[str, Any]:
    """
    Set a device parameter value.

    Use for a single standard parameter change. For multiple params at once,
    use set_device_parameters instead. For hidden/non-automatable params, use
    set_device_hidden_parameter (requires M4L bridge).

    Parameters:
    - track_index: The index of the track containing the device
    - device_index: The index of the device on the track
    - parameter_name: The name of the parameter to set
    - value: The new value for the parameter (will be clamped to min/max)
    - track_type: Type of track: "track" (default), "return", or "master"
    """
    if track_type not in ("track", "return", "master"):
        return {"error": "track_type must be 'track', 'return', or 'master'"}
    
    # This is a placeholder - real implementation would connect to Ableton
    return {
        "track_index": track_index,
        "device_index": device_index,
        "parameter_name": parameter_name,
        "value": value,
        "track_type": track_type,
        "message": "Device parameter setting requires connection to Ableton Live"
    }
