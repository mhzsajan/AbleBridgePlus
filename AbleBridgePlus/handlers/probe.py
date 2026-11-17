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


# Curated vocabulary used when no search pattern is given. These are the LOM
# names people actually probe for; the rest of dir() is sampled separately.
_INTERESTING_TOKENS = ("envelope", "automation", "clip", "cue", "send",
                       "mute", "volume")
_ATTR_SAMPLE_LIMIT = 40
_ALLOWED_ROOTS = ("song", "track", "clip", "device", "scene", "return")


def _resolve_clip(track, clip_index):
    """Read-only clip lookup: Arrangement first, then Session (as the CC probe does)."""
    try:
        ac = list(track.arrangement_clips)
        if 0 <= clip_index < len(ac):
            return ac[clip_index], None
    except Exception:
        pass
    try:
        slots = list(track.clip_slots)
        if 0 <= clip_index < len(slots):
            clip = getattr(slots[clip_index], "clip", None)
            if clip is not None:
                return clip, None
    except Exception:
        pass
    # Last resort: first Session slot that actually holds a clip.
    try:
        for slot in track.clip_slots:
            if getattr(slot, "has_clip", False):
                clip = getattr(slot, "clip", None)
                if clip is not None:
                    return clip, None
    except Exception:
        pass
    return None, "no clip found at clip_index {0}".format(clip_index)


def _resolve_root(song, root, track_index, clip_index, device_index):
    """Resolve one of the whitelisted roots to a LOM object.

    Returns ``(obj, error)``. Unknown roots and out-of-range indices are
    reported as an error string; nothing is ever evaluated from user input.
    """
    try:
        if root == "song":
            return song, None
        if root == "track":
            return song.tracks[track_index], None
        if root == "return":
            return song.return_tracks[track_index], None
        if root == "scene":
            return song.scenes[clip_index], None
        if root == "clip":
            return _resolve_clip(song.tracks[track_index], clip_index)
        if root == "device":
            track = song.tracks[track_index]
            clip, _clip_err = _resolve_clip(track, clip_index)
            if clip is not None:
                try:
                    devices = list(getattr(clip, "devices", None) or [])
                    if 0 <= device_index < len(devices):
                        return devices[device_index], None
                except Exception:
                    pass
            devices = list(track.devices)
            if 0 <= device_index < len(devices):
                return devices[device_index], None
            return None, "no device found at device_index {0}".format(device_index)
    except Exception as e:
        return None, "failed to resolve root '{0}': {1}".format(root, e)
    return None, "unknown root '{0}'; expected one of: {1}".format(
        root, ", ".join(_ALLOWED_ROOTS))


def probe_lom_capability(song, root="song", track_index=0, clip_index=0,
                         device_index=0, pattern="", ctrl=None):
    """Read-only ``dir()`` probe of a whitelisted Live Object Model surface.

    Never evaluates arbitrary paths: *root* must be one of ``song``, ``track``,
    ``clip``, ``device``, ``scene`` or ``return``. Only ``dir()`` and safe
    ``getattr`` lookups are used, so the probe cannot mutate the set.

    With a non-empty *pattern*, every attribute name containing it (case
    insensitive) is returned. With an empty pattern, a short curated list of
    interesting names is returned together with the first ~40 attribute names
    alphabetically - the full ``dir()`` is deliberately never dumped.

    Returns a JSON-serializable dict with keys: root, pattern, object_type,
    attrs, attr_count and error. Problems are reported in ``error``, never
    raised.
    """
    out = {
        "root": root,
        "pattern": pattern,
        "object_type": None,
        "attrs": [],
        "attr_count": 0,
        "error": None,
    }

    needle = ""
    try:
        if pattern:
            needle = str(pattern).lower()
    except Exception:
        needle = ""

    obj, error = _resolve_root(song, root, track_index, clip_index, device_index)
    if error:
        out["error"] = error
        if ctrl:
            try:
                ctrl.log_message("LOM capability probe: " + str(error))
            except Exception:
                pass
        return out

    try:
        out["object_type"] = type(obj).__name__
    except Exception:
        out["object_type"] = "unknown"

    try:
        names = sorted(dir(obj))
    except Exception as e:
        out["error"] = "dir() failed: {0}".format(e)
        return out

    if needle:
        attrs = [n for n in names if needle in str(n).lower()]
    else:
        interesting = [n for n in names
                       if any(tok in str(n).lower()
                              for tok in _INTERESTING_TOKENS)]
        seen = set()
        attrs = []
        for name in interesting + names[:_ATTR_SAMPLE_LIMIT]:
            if name not in seen:
                seen.add(name)
                attrs.append(name)
        attrs = sorted(attrs)

    out["attrs"] = attrs
    out["attr_count"] = len(attrs)
    return out
