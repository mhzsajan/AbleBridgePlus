"""
Input Validation for AbleBridge++ MCP Server.
"""

from typing import Any, Dict, List, Optional, Union
from MCP_Server.constants import (
    MIDI_NOTE_MIN, MIDI_NOTE_MAX,
    MIDI_VELOCITY_MIN, MIDI_VELOCITY_MAX,
    MIDI_CC_MIN, MIDI_CC_MAX,
    MAX_NOTES_PER_CALL, MAX_AUTOMATION_POINTS,
    MAX_BATCH_PARAMETERS, MAX_BATCH_TRACKS
)


class ValidationError(Exception):
    """Validation error exception."""
    
    def __init__(self, message: str, code: int = -32602):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            code: Error code
        """
        super().__init__(message)
        self.code = code
        self.message = message


def validate_track_index(track_index: Any, allow_negative: bool = False) -> int:
    """
    Validate track index.
    
    Args:
        track_index: Track index to validate
        allow_negative: Allow negative indices (-1 for end of list)
        
    Returns:
        Validated track index
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(track_index, int):
        raise ValidationError(f"Track index must be an integer, got {type(track_index).__name__}")
    
    if not allow_negative and track_index < 0:
        raise ValidationError(f"Track index must be non-negative, got {track_index}")
    
    return track_index


def validate_clip_index(clip_index: Any) -> int:
    """
    Validate clip index.
    
    Args:
        clip_index: Clip index to validate
        
    Returns:
        Validated clip index
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(clip_index, int):
        raise ValidationError(f"Clip index must be an integer, got {type(clip_index).__name__}")
    
    if clip_index < 0:
        raise ValidationError(f"Clip index must be non-negative, got {clip_index}")
    
    return clip_index


def validate_device_index(device_index: Any) -> int:
    """
    Validate device index.
    
    Args:
        device_index: Device index to validate
        
    Returns:
        Validated device index
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(device_index, int):
        raise ValidationError(f"Device index must be an integer, got {type(device_index).__name__}")
    
    if device_index < 0:
        raise ValidationError(f"Device index must be non-negative, got {device_index}")
    
    return device_index


def validate_midi_note(note: Any) -> int:
    """
    Validate MIDI note number.
    
    Args:
        note: MIDI note to validate
        
    Returns:
        Validated MIDI note
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(note, int):
        raise ValidationError(f"MIDI note must be an integer, got {type(note).__name__}")
    
    if note < MIDI_NOTE_MIN or note > MIDI_NOTE_MAX:
        raise ValidationError(f"MIDI note must be between {MIDI_NOTE_MIN} and {MIDI_NOTE_MAX}, got {note}")
    
    return note


def validate_velocity(velocity: Any) -> int:
    """
    Validate MIDI velocity.
    
    Args:
        velocity: Velocity to validate
        
    Returns:
        Validated velocity
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(velocity, int):
        raise ValidationError(f"Velocity must be an integer, got {type(velocity).__name__}")
    
    if velocity < MIDI_VELOCITY_MIN or velocity > MIDI_VELOCITY_MAX:
        raise ValidationError(f"Velocity must be between {MIDI_VELOCITY_MIN} and {MIDI_VELOCITY_MAX}, got {velocity}")
    
    return velocity


def validate_cc(cc: Any) -> int:
    """
    Validate MIDI CC number.
    
    Args:
        cc: CC number to validate
        
    Returns:
        Validated CC number
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(cc, int):
        raise ValidationError(f"MIDI CC must be an integer, got {type(cc).__name__}")
    
    if cc < MIDI_CC_MIN or cc > MIDI_CC_MAX:
        raise ValidationError(f"MIDI CC must be between {MIDI_CC_MIN} and {MIDI_CC_MAX}, got {cc}")
    
    return cc


def validate_value(value: Any, min_val: float, max_val: float, name: str = "value") -> float:
    """
    Validate a numeric value within a range.
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        name: Name of the value for error messages
        
    Returns:
        Validated value
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be a number, got {type(value).__name__}")
    
    if value < min_val or value > max_val:
        raise ValidationError(f"{name} must be between {min_val} and {max_val}, got {value}")
    
    return float(value)


def validate_time(time: Any, name: str = "time") -> float:
    """
    Validate a time value (must be non-negative).
    
    Args:
        time: Time value to validate
        name: Name of the time value for error messages
        
    Returns:
        Validated time value
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(time, (int, float)):
        raise ValidationError(f"{name} must be a number, got {type(time).__name__}")
    
    if time < 0:
        raise ValidationError(f"{name} must be non-negative, got {time}")
    
    return float(time)


def validate_duration(duration: Any) -> float:
    """
    Validate a duration value (must be positive).
    
    Args:
        duration: Duration to validate
        
    Returns:
        Validated duration
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(duration, (int, float)):
        raise ValidationError(f"Duration must be a number, got {type(duration).__name__}")
    
    if duration <= 0:
        raise ValidationError(f"Duration must be positive, got {duration}")
    
    return float(duration)


def validate_notes(notes: Any) -> List[Dict]:
    """
    Validate a list of notes.
    
    Args:
        notes: List of note dictionaries to validate
        
    Returns:
        Validated notes
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(notes, list):
        raise ValidationError(f"Notes must be a list, got {type(notes).__name__}")
    
    if len(notes) > MAX_NOTES_PER_CALL:
        raise ValidationError(f"Too many notes: {len(notes)} (max {MAX_NOTES_PER_CALL})")
    
    validated_notes = []
    for i, note in enumerate(notes):
        if not isinstance(note, dict):
            raise ValidationError(f"Note {i} must be a dictionary")
        
        # Required fields
        if 'pitch' not in note:
            raise ValidationError(f"Note {i} missing required field 'pitch'")
        if 'start_time' not in note:
            raise ValidationError(f"Note {i} missing required field 'start_time'")
        if 'duration' not in note:
            raise ValidationError(f"Note {i} missing required field 'duration'")
        if 'velocity' not in note:
            raise ValidationError(f"Note {i} missing required field 'velocity'")
        
        # Validate fields
        validated_note = {
            'pitch': validate_midi_note(note['pitch']),
            'start_time': validate_time(note['start_time'], f"Note {i} start_time"),
            'duration': validate_duration(note['duration']),
            'velocity': validate_velocity(note['velocity'])
        }
        
        # Optional fields
        if 'mute' in note:
            validated_note['mute'] = bool(note['mute'])
        if 'probability' in note:
            validated_note['probability'] = validate_value(note['probability'], 0.0, 1.0, f"Note {i} probability")
        if 'velocity_deviation' in note:
            validated_note['velocity_deviation'] = validate_value(note['velocity_deviation'], -127, 127, f"Note {i} velocity_deviation")
        if 'release_velocity' in note:
            validated_note['release_velocity'] = validate_velocity(note['release_velocity'])
        
        validated_notes.append(validated_note)
    
    return validated_notes


def validate_automation_points(points: Any) -> List[Dict]:
    """
    Validate automation points.
    
    Args:
        points: List of automation point dictionaries
        
    Returns:
        Validated automation points
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(points, list):
        raise ValidationError(f"Automation points must be a list, got {type(points).__name__}")
    
    if len(points) > MAX_AUTOMATION_POINTS:
        raise ValidationError(f"Too many automation points: {len(points)} (max {MAX_AUTOMATION_POINTS})")
    
    validated_points = []
    for i, point in enumerate(points):
        if not isinstance(point, dict):
            raise ValidationError(f"Automation point {i} must be a dictionary")
        
        if 'time' not in point:
            raise ValidationError(f"Automation point {i} missing required field 'time'")
        if 'value' not in point:
            raise ValidationError(f"Automation point {i} missing required field 'value'")
        
        validated_point = {
            'time': validate_time(point['time'], f"Automation point {i} time"),
            'value': float(point['value'])
        }
        
        validated_points.append(validated_point)
    
    return validated_points


def validate_parameters(parameters: Any) -> Dict[str, Any]:
    """
    Validate device parameters.
    
    Args:
        parameters: Dictionary of parameter names and values
        
    Returns:
        Validated parameters
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(parameters, dict):
        raise ValidationError(f"Parameters must be a dictionary, got {type(parameters).__name__}")
    
    if len(parameters) > MAX_BATCH_PARAMETERS:
        raise ValidationError(f"Too many parameters: {len(parameters)} (max {MAX_BATCH_PARAMETERS})")
    
    validated_params = {}
    for name, value in parameters.items():
        if not isinstance(name, str):
            raise ValidationError(f"Parameter name must be a string")
        
        if not isinstance(value, (int, float, bool)):
            raise ValidationError(f"Parameter value must be a number or boolean")
        
        validated_params[name] = value
    
    return validated_params


def validate_batch_tracks(tracks: Any) -> List[int]:
    """
    Validate a list of track indices for batch operations.
    
    Args:
        tracks: List of track indices
        
    Returns:
        Validated track indices
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(tracks, list):
        raise ValidationError(f"Tracks must be a list, got {type(tracks).__name__}")
    
    if len(tracks) > MAX_BATCH_TRACKS:
        raise ValidationError(f"Too many tracks: {len(tracks)} (max {MAX_BATCH_TRACKS})")
    
    validated_tracks = []
    for i, track in enumerate(tracks):
        if not isinstance(track, int):
            raise ValidationError(f"Track {i} must be an integer")
        
        validated_tracks.append(track)
    
    return validated_tracks


def validate_string(value: Any, name: str = "value", min_length: int = 0, max_length: int = 1000) -> str:
    """
    Validate a string value.
    
    Args:
        value: String to validate
        name: Name of the value for error messages
        min_length: Minimum length
        max_length: Maximum length
        
    Returns:
        Validated string
        
    Raises:
        ValidationError: If validation fails
    """
    if not isinstance(value, str):
        raise ValidationError(f"{name} must be a string, got {type(value).__name__}")
    
    if len(value) < min_length:
        raise ValidationError(f"{name} must be at least {min_length} characters long")
    
    if len(value) > max_length:
        raise ValidationError(f"{name} must be at most {max_length} characters long")
    
    return value


def validate_optional(value: Any, validator_func, default: Any = None) -> Any:
    """
    Validate an optional value.
    
    Args:
        value: Value to validate (can be None)
        validator_func: Validation function to use
        default: Default value if None
        
    Returns:
        Validated value or default
        
    Raises:
        ValidationError: If validation fails
    """
    if value is None:
        return default
    
    return validator_func(value)


# ---------------------------------------------------------------------------
# Backward-compatible aliases used by the ported tool modules (register_tools
# pattern). Kept alongside the canonical validators so both tool styles work.
# ---------------------------------------------------------------------------


def _validate_index(value: Any, name: str = "index") -> int:
    """Alias for validate_track_index: generic non-negative index check."""
    if not isinstance(value, int):
        raise ValidationError(f"{name} must be an integer, got {type(value).__name__}")
    if value < 0:
        raise ValidationError(f"{name} must be non-negative, got {value}")
    return value


def _validate_index_allow_negative(value: Any, name: str = "index") -> int:
    """Alias for validate_track_index with allow_negative=True."""
    if not isinstance(value, int):
        raise ValidationError(f"{name} must be an integer, got {type(value).__name__}")
    return value


def _validate_range(value: Any, name: str = "value", min_val: float = 0, max_val: float = 1) -> float:
    """Alias for validate_value: numeric range check."""
    return validate_value(value, min_val, max_val, name)


def _validate_notes(notes: Any) -> List[Dict]:
    """Alias for validate_notes."""
    return validate_notes(notes)


def _validate_automation_points(points: Any) -> List[Dict]:
    """Alias for validate_automation_points."""
    return validate_automation_points(points)


def _reduce_automation_points(points: List[Dict], max_points: int = MAX_AUTOMATION_POINTS) -> List[Dict]:
    """
    Reduce automation points for performance by even decimation.

    Returns the list unchanged if it is already within the limit.
    """
    if len(points) <= max_points:
        return points
    step = len(points) / max_points
    return [points[int(i * step)] for i in range(max_points)]
