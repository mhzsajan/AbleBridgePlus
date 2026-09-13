"""
Tests for Enhanced AbletonBridge validation module.
"""

import pytest
from MCP_Server.validation import (
    validate_track_index,
    validate_clip_index,
    validate_device_index,
    validate_midi_note,
    validate_velocity,
    validate_cc,
    validate_value,
    validate_time,
    validate_duration,
    validate_notes,
    validate_automation_points,
    validate_parameters,
    validate_string,
    ValidationError
)


class TestTrackIndex:
    """Tests for track index validation."""
    
    def test_valid_track_index(self):
        assert validate_track_index(0) == 0
        assert validate_track_index(5) == 5
    
    def test_negative_track_index_with_allow(self):
        assert validate_track_index(-1, allow_negative=True) == -1
    
    def test_negative_track_index_without_allow(self):
        with pytest.raises(ValidationError):
            validate_track_index(-1, allow_negative=False)
    
    def test_non_integer_track_index(self):
        with pytest.raises(ValidationError):
            validate_track_index("0")


class TestClipIndex:
    """Tests for clip index validation."""
    
    def test_valid_clip_index(self):
        assert validate_clip_index(0) == 0
        assert validate_clip_index(3) == 3
    
    def test_negative_clip_index(self):
        with pytest.raises(ValidationError):
            validate_clip_index(-1)
    
    def test_non_integer_clip_index(self):
        with pytest.raises(ValidationError):
            validate_clip_index("0")


class TestMidiNote:
    """Tests for MIDI note validation."""
    
    def test_valid_midi_note(self):
        assert validate_midi_note(0) == 0
        assert validate_midi_note(60) == 60
        assert validate_midi_note(127) == 127
    
    def test_invalid_midi_note_low(self):
        with pytest.raises(ValidationError):
            validate_midi_note(-1)
    
    def test_invalid_midi_note_high(self):
        with pytest.raises(ValidationError):
            validate_midi_note(128)
    
    def test_non_integer_midi_note(self):
        with pytest.raises(ValidationError):
            validate_midi_note("60")


class TestVelocity:
    """Tests for velocity validation."""
    
    def test_valid_velocity(self):
        assert validate_velocity(1) == 1
        assert validate_velocity(64) == 64
        assert validate_velocity(127) == 127
    
    def test_invalid_velocity_low(self):
        with pytest.raises(ValidationError):
            validate_velocity(0)
    
    def test_invalid_velocity_high(self):
        with pytest.raises(ValidationError):
            validate_velocity(128)


class TestValue:
    """Tests for value validation."""
    
    def test_valid_value(self):
        assert validate_value(0.5, 0.0, 1.0) == 0.5
        assert validate_value(0.0, 0.0, 1.0) == 0.0
        assert validate_value(1.0, 0.0, 1.0) == 1.0
    
    def test_invalid_value_low(self):
        with pytest.raises(ValidationError):
            validate_value(-0.1, 0.0, 1.0)
    
    def test_invalid_value_high(self):
        with pytest.raises(ValidationError):
            validate_value(1.1, 0.0, 1.0)
    
    def test_non_numeric_value(self):
        with pytest.raises(ValidationError):
            validate_value("0.5", 0.0, 1.0)


class TestNotes:
    """Tests for notes validation."""
    
    def test_valid_notes(self):
        notes = [
            {
                'pitch': 60,
                'start_time': 0.0,
                'duration': 1.0,
                'velocity': 100
            }
        ]
        result = validate_notes(notes)
        assert len(result) == 1
        assert result[0]['pitch'] == 60
    
    def test_empty_notes(self):
        result = validate_notes([])
        assert len(result) == 0
    
    def test_invalid_notes_type(self):
        with pytest.raises(ValidationError):
            validate_notes("not a list")
    
    def test_note_missing_pitch(self):
        notes = [
            {
                'start_time': 0.0,
                'duration': 1.0,
                'velocity': 100
            }
        ]
        with pytest.raises(ValidationError):
            validate_notes(notes)
    
    def test_note_missing_start_time(self):
        notes = [
            {
                'pitch': 60,
                'duration': 1.0,
                'velocity': 100
            }
        ]
        with pytest.raises(ValidationError):
            validate_notes(notes)
    
    def test_note_missing_duration(self):
        notes = [
            {
                'pitch': 60,
                'start_time': 0.0,
                'velocity': 100
            }
        ]
        with pytest.raises(ValidationError):
            validate_notes(notes)
    
    def test_note_missing_velocity(self):
        notes = [
            {
                'pitch': 60,
                'start_time': 0.0,
                'duration': 1.0
            }
        ]
        with pytest.raises(ValidationError):
            validate_notes(notes)


class TestString:
    """Tests for string validation."""
    
    def test_valid_string(self):
        assert validate_string("hello") == "hello"
        assert validate_string("") == ""
    
    def test_string_too_short(self):
        with pytest.raises(ValidationError):
            validate_string("hi", min_length=3)
    
    def test_string_too_long(self):
        with pytest.raises(ValidationError):
            validate_string("hello", max_length=3)
    
    def test_non_string_value(self):
        with pytest.raises(ValidationError):
            validate_string(123)


if __name__ == '__main__':
    pytest.main([__file__])
