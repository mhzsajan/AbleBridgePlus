"""
AI Enhancement Tools for AbleBridgePlus MCP Server.

Provides smart suggestions and intelligent automation for mixing and sound design.
"""

import json
from typing import Any, Dict, List, Optional
from . import tool


class AIEnhancement:
    """AI enhancement manager."""
    
    def __init__(self):
        """Initialize AI enhancement."""
        self.genre_rules = {
            "rock": {
                "eq_suggestions": {"bass": "boost_low_mids", "guitar": "cut_mids", "vocals": "presence_boost"},
                "compression": {"drums": "medium_ratio", "bass": "light_compression"},
                "effects": {"guitar": "slight_reverb", "vocals": "plate_reverb"}
            },
            "electronic": {
                "eq_suggestions": {"synth": "bright", "bass": "sub_focus", "drums": "punchy"},
                "compression": {"synth": "heavy_sidechain", "drums": "parallel"},
                "effects": {"synth": "delay", "vocals": "chorus"}
            },
            "jazz": {
                "eq_suggestions": {"piano": "natural", "bass": "warm", "drums": "brush_friendly"},
                "compression": {"piano": "light", "bass": "minimal"},
                "effects": {"piano": "room_reverb", "sax": "plate_reverb"}
            },
            "pop": {
                "eq_suggestions": {"vocals": "presence", "synth": "bright", "bass": "punchy"},
                "compression": {"vocals": "consistent", "drums": "punchy"},
                "effects": {"vocals": "auto_tune", "synth": "chorus"}
            }
        }
    
    def get_genre_suggestions(self, genre: str, track_type: str) -> Dict[str, Any]:
        """Get genre-based mixing suggestions."""
        genre_lower = genre.lower()
        
        if genre_lower not in self.genre_rules:
            return {
                "status": "no_suggestions",
                "message": f"No suggestions available for genre: {genre}"
            }
        
        rules = self.genre_rules[genre_lower]
        suggestions = {}
        
        if track_type in rules.get("eq_suggestions", {}):
            suggestions["eq"] = rules["eq_suggestions"][track_type]
        
        if track_type in rules.get("compression", {}):
            suggestions["compression"] = rules["compression"][track_type]
        
        if track_type in rules.get("effects", {}):
            suggestions["effects"] = rules["effects"][track_type]
        
        return {
            "status": "suggestions_ready",
            "genre": genre,
            "track_type": track_type,
            "suggestions": suggestions
        }
    
    def get_arrangement_suggestions(self, song_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Get arrangement suggestions."""
        suggestions = []
        
        # Analyze song structure (accept sections as dicts or plain strings)
        sections = song_structure.get("sections", []) if isinstance(song_structure, dict) else []
        normalized = []
        for s in sections:
            if isinstance(s, dict):
                normalized.append(s)
            elif isinstance(s, str):
                normalized.append({"name": s})
        sections = normalized
        if len(sections) < 3:
            suggestions.append("Consider adding more sections for better dynamics")
        
        # Check for intro/outro
        has_intro = any(s.get("name", "").lower() == "intro" for s in sections)
        has_outro = any(s.get("name", "").lower() == "outro" for s in sections)
        
        if not has_intro:
            suggestions.append("Add an intro to ease listeners into the song")
        if not has_outro:
            suggestions.append("Add an outro to properly end the song")
        
        # Check for chorus repetition
        chorus_count = sum(1 for s in sections if s.get("name", "").lower() == "chorus")
        if chorus_count < 2:
            suggestions.append("Consider repeating the chorus for better catchiness")
        
        return {
            "status": "suggestions_ready",
            "suggestions": suggestions
        }
    
    def get_sound_design_help(self, sound_type: str, style: str) -> Dict[str, Any]:
        """Get sound design assistance."""
        tips = {
            "bass": {
                "deep": ["Use a low-pass filter", "Add sub-oscillator", "Use long attack"],
                "punchy": ["Use fast attack", "Add compression", "Use mid-range harmonics"],
                "warm": ["Use analog-style synth", "Add slight saturation", "Use low-pass filter"]
            },
            "lead": {
                "bright": ["Use high-pass filter", "Add chorus", "Use detuned oscillators"],
                "dark": ["Use low-pass filter", "Add reverb", "Use fewer harmonics"],
                "aggressive": ["Use distortion", "Add compression", "Use sawtooth wave"]
            },
            "pad": {
                "lush": ["Use chorus", "Add reverb", "Use multiple oscillators"],
                "dark": ["Use low-pass filter", "Add tape saturation", "Use slow attack"],
                "airy": ["Use high-pass filter", "Add shimmer reverb", "Use sine wave"]
            }
        }
        
        if sound_type not in tips:
            return {"status": "error", "message": f"No tips for sound type: {sound_type}"}
        
        if style not in tips[sound_type]:
            return {"status": "error", "message": f"No tips for style: {style}"}
        
        return {
            "status": "tips_ready",
            "sound_type": sound_type,
            "style": style,
            "tips": tips[sound_type][style]
        }
    
    def analyze_mix_quality(self, mix_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze mix quality and provide suggestions."""
        issues = []
        suggestions = []
        
        # Check for frequency balance
        low_energy = mix_data.get("low_energy", 0)
        mid_energy = mix_data.get("mid_energy", 0)
        high_energy = mix_data.get("high_energy", 0)
        
        total = low_energy + mid_energy + high_energy
        if total > 0:
            low_ratio = low_energy / total
            mid_ratio = mid_energy / total
            high_ratio = high_energy / total
            
            if low_ratio > 0.5:
                issues.append("Too much low frequency energy")
                suggestions.append("Consider high-pass filtering some tracks")
            
            if high_ratio < 0.1:
                issues.append("Not enough high frequency content")
                suggestions.append("Add brightness with EQ or exciter")
        
        # Check for dynamic range
        dynamic_range = mix_data.get("dynamic_range", 0)
        if dynamic_range < 6:
            issues.append("Mix may be over-compressed")
            suggestions.append("Reduce compression to preserve dynamics")
        elif dynamic_range > 20:
            issues.append("Mix may lack cohesion")
            suggestions.append("Add bus compression to glue tracks together")
        
        return {
            "status": "analysis_complete",
            "issues": issues,
            "suggestions": suggestions,
            "quality_score": max(0, 100 - len(issues) * 20)
        }
    
    def auto_gain_stage(self, tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Auto gain staging for tracks."""
        adjustments = []
        
        for track in tracks:
            track_index = track.get("index")
            current_level = track.get("level", 0)
            target_level = track.get("target_level", -12)  # -12 dB target
            
            # Calculate adjustment
            adjustment = target_level - current_level
            
            adjustments.append({
                "track_index": track_index,
                "current_level": current_level,
                "target_level": target_level,
                "adjustment": adjustment
            })
        
        return {
            "status": "gain_staging_ready",
            "adjustments": adjustments
        }


# Global instance
_ai_enhancement = AIEnhancement()


@tool(
    name="get_genre_suggestions",
    description="Get genre-based mixing suggestions",
    input_schema={
        "type": "object",
        "properties": {
            "genre": {
                "type": "string",
                "description": "Music genre (rock, electronic, jazz, pop)"
            },
            "track_type": {
                "type": "string",
                "description": "Track type (bass, guitar, vocals, drums, etc.)"
            }
        },
        "required": ["genre", "track_type"]
    }
)
async def get_genre_suggestions(genre: str, track_type: str) -> Dict[str, Any]:
    """Get genre-based mixing suggestions."""
    return _ai_enhancement.get_genre_suggestions(genre, track_type)


@tool(
    name="get_arrangement_suggestions",
    description="Get arrangement suggestions based on song structure",
    input_schema={
        "type": "object",
        "properties": {
            "song_structure": {
                "type": "object",
                "description": "Song structure with sections"
            }
        },
        "required": ["song_structure"]
    }
)
async def get_arrangement_suggestions(song_structure: Dict[str, Any]) -> Dict[str, Any]:
    """Get arrangement suggestions based on song structure."""
    return _ai_enhancement.get_arrangement_suggestions(song_structure)


@tool(
    name="get_sound_design_help",
    description="Get sound design assistance",
    input_schema={
        "type": "object",
        "properties": {
            "sound_type": {
                "type": "string",
                "description": "Type of sound (bass, lead, pad)"
            },
            "style": {
                "type": "string",
                "description": "Desired style (deep, bright, punchy, etc.)"
            }
        },
        "required": ["sound_type", "style"]
    }
)
async def get_sound_design_help(sound_type: str, style: str) -> Dict[str, Any]:
    """Get sound design assistance."""
    return _ai_enhancement.get_sound_design_help(sound_type, style)


@tool(
    name="analyze_mix_quality",
    description="Analyze mix quality and provide suggestions",
    input_schema={
        "type": "object",
        "properties": {
            "mix_data": {
                "type": "object",
                "description": "Mix data with frequency and dynamic information"
            }
        },
        "required": ["mix_data"]
    }
)
async def analyze_mix_quality(mix_data: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze mix quality and provide suggestions."""
    return _ai_enhancement.analyze_mix_quality(mix_data)


@tool(
    name="auto_gain_stage",
    description="Auto gain staging for tracks",
    input_schema={
        "type": "object",
        "properties": {
            "tracks": {
                "type": "array",
                "description": "List of tracks with current levels"
            }
        },
        "required": ["tracks"]
    }
)
async def auto_gain_stage(tracks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Auto gain staging for tracks."""
    return _ai_enhancement.auto_gain_stage(tracks)
