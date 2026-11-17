"""Read-only capability probes for Live Object Model (LOM) surfaces.

These handlers answer "does this Live version expose X?" without ever calling
a mutating API. They rely on ``dir()`` introspection and read-only attribute
lookups, guarded so a missing attribute reports ABSENT instead of raising.
Nothing here changes song state - a probe is evidence, not a promise.
"""

from __future__ import absolute_import, print_function, unicode_literals

_TOKENS = ("envelope", "cc", "automation_target")


def _interesting_attrs(obj):
    """Sorted attribute names on *obj* matching the CC/envelope token list."""
    try:
        names = dir(obj)
    except Exception:
        return []
    return sorted(a for a in names
                  if any(tok in a.lower() for tok in _TOKENS))


def _is_midi_clip(clip):
    """Best-effort, read-only MIDI-clip test. Never assumes the flag exists."""
    flag = getattr(clip, "is_midi_clip", None)
    if isinstance(flag, bool):
        return flag
    # Fallback: Live's MidiClip class name. Pure introspection.
    try:
        return "MidiClip" in type(clip).__name__
    except Exception:
        return False


def probe_midi_cc_envelope_surface(song, track_index, clip_index=0, ctrl=None):
    """Report the envelope / CC / automation-target surface of a MIDI clip.

    Prefers an Arrangement clip (``clip_index`` into ``track.arrangement_clips``);
    if that is not a MIDI clip, falls back to the first Session clip slot that
    holds a clip. Uses ``dir()`` only for the capability lists - no method on
    the clip or its envelopes is ever called, and no state is changed.

    Returns a JSON-serializable dict of attribute-name lists plus a
    ``midi_clip_found`` flag. Missing data is reported as ABSENT / None rather
    than assumed, so an empty list means "this Live does not expose it", not
    "CC envelopes definitely do not exist".
    """
    out = {
        "track_index": track_index,
        "clip_index": clip_index,
        "midi_clip_found": False,
        "clip_source": None,
        "clip_type": None,
        "envelope_count": None,
        "clip_attrs": [],
        "envelope_attrs": [],
        "envelope_objects": [],
        "error": None,
    }
    try:
        track = song.tracks[track_index]
    except Exception as e:
        out["error"] = "Invalid track index {0}: {1}".format(track_index, e)
        if ctrl:
            ctrl.log_message("MIDI CC envelope probe: " + str(e))
        return out

    clip = None
    # 1) Preferred: Arrangement clip at clip_index.
    try:
        ac = list(track.arrangement_clips)
        if 0 <= clip_index < len(ac) and _is_midi_clip(ac[clip_index]):
            clip = ac[clip_index]
            out["clip_source"] = "arrangement"
    except Exception as e:
        out["error"] = "arrangement_clips lookup failed: {0}".format(e)

    # 2) Fallback: first Session clip slot holding a (MIDI) clip.
    if clip is None:
        try:
            for slot in track.clip_slots:
                if getattr(slot, "has_clip", False):
                    candidate = getattr(slot, "clip", None)
                    if candidate is not None and _is_midi_clip(candidate):
                        clip = candidate
                        out["clip_source"] = "session"
                        break
        except Exception as e:
            out["error"] = (out["error"] or "") + " clip_slots scan failed: {0}".format(e)

    if clip is None:
        out["error"] = (out["error"] or "") + " no MIDI clip found on this track"
        return out

    out["midi_clip_found"] = True
    try:
        out["clip_type"] = type(clip).__name__
    except Exception:
        out["clip_type"] = "unknown"

    # dir() of the clip itself - which envelope/CC names exist at all?
    out["clip_attrs"] = _interesting_attrs(clip)

    # Envelope objects: enumerate read-only, then dir() each one.
    try:
        envelopes = getattr(clip, "envelopes", None)
        if envelopes is not None:
            env_list = list(envelopes)
            out["envelope_count"] = len(env_list)
            for env in env_list:
                entry = {
                    "type": type(env).__name__,
                    "attrs": _interesting_attrs(env),
                    "automation_target": None,
                }
                try:
                    target = getattr(env, "automation_target", None)
                    if target is not None:
                        entry["automation_target"] = {
                            "type": type(target).__name__,
                            "name": getattr(target, "name", None),
                            "attrs": _interesting_attrs(target),
                        }
                except Exception:
                    pass
                out["envelope_objects"].append(entry)
            # Union of every envelope's interesting attrs for an at-a-glance list.
            seen = set()
            for entry in out["envelope_objects"]:
                for a in entry["attrs"]:
                    seen.add(a)
                target = entry.get("automation_target")
                if target:
                    for a in target.get("attrs", []):
                        seen.add(a)
            out["envelope_attrs"] = sorted(seen)
    except Exception as e:
        out["error"] = (out["error"] or "") + " envelope enumeration failed: {0}".format(e)

    return out
