"""
AbleBridgePlus - AI-integrated live show engineering system for Ableton Live.

Based on AbletonBridge by hidingwill (https://github.com/hidingwill/AbletonBridge).
Enhanced with 440+ tools across 14 categories for live show engineering.

Credits:
- Original AbletonBridge: https://github.com/hidingwill/AbletonBridge
- Original Creator: hidingwill
"""

__version__ = "0.8.0"
__author__ = "Sajan Maharjan"
__license__ = "MIT"
__description__ = "AI-integrated live show engineering system for Ableton Live"
__url__ = "https://github.com/mhzsajan/AbleBridgePlus"


def remote_script_folder(version=None):
    """Folder name the remote script must have in Live's Remote Scripts dir.

    Ableton derives the Preferences > Link, Tempo & MIDI > Control Surface entry
    from the folder name, so embedding the version there is the only way to
    show it in that list. Underscores, never dots: Python splits module names
    on '.', so a folder called "AbleBridgePlus 0.8.0" cannot be imported at all
    (verified on Live 12's Python 3.11: ModuleNotFoundError: No module named
    'AbleBridgePlus 0').

    Because the name changes with every release, Live's saved selection stops
    matching after an upgrade and has to be re-picked once; `doctor` reports
    that instead of leaving you with a silently dead connection.
    """
    if version is None:
        version = __version__
    return "AbleBridgePlus_" + version.replace(".", "_")
