"""
mood42 Channel Definitions and Track Library
"""

from typing import Dict, List

# Track library - all available tracks (now all belong to ch06)
TRACKS: Dict[str, Dict] = {
    # Lo-fi / Chill
    "hanging_lanterns": {
        "id": "hanging_lanterns",
        "name": "Hanging Lanterns - Kalaido",
        "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/Kalaido%20-%20Hanging%20Lanterns.mp3",
        "genres": ["lo-fi", "chill"],
        "mood": ["focused", "calm"],
        "duration": 180,
        "attribution": "Hanging Lanterns by Kalaido (Archive.org, CC)",
        "source": "archive.org",
    },
    "first_snow": {
        "id": "first_snow",
        "name": "First Snow - Kerusu",
        "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/Kerusu%20-%20First%20Snow.mp3",
        "genres": ["lo-fi", "chill"],
        "mood": ["peaceful", "nostalgic"],
        "duration": 195,
        "attribution": "First Snow by Kerusu (Archive.org, CC)",
        "source": "archive.org",
    },
    "lofi_rain": {
        "id": "lofi_rain",
        "name": "Lo-fi Rain",
        "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/%28FREE%29%20Lo-fi%20Type%20Beat%20-%20Rain.mp3",
        "genres": ["lo-fi", "rain"],
        "mood": ["melancholic", "reflective"],
        "duration": 170,
        "attribution": "Lo-fi Rain Type Beat (Archive.org, Free)",
        "source": "archive.org",
    },
    "waves": {
        "id": "waves",
        "name": "Waves - Matt Quentin",
        "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/Matt%20Quentin%20-%20Waves.mp3",
        "genres": ["lo-fi", "warm"],
        "mood": ["nostalgic", "peaceful"],
        "duration": 200,
        "attribution": "Waves by Matt Quentin (Archive.org, CC)",
        "source": "archive.org",
    },

    # Jazz
    "swing_jazz": {
        "id": "swing_jazz",
        "name": "Swing Jazz Grooves",
        "url": "https://archive.org/download/lofi-music-swing-jazz-grooves-to-elevate-your-mood-feel-the-rhythm/LOFI%20Music%E3%80%80Swing%20Jazz%20Grooves%20to%20Elevate%20Your%20Mood%20%EF%BD%9C%20Feel%20the%20Rhythm%20.mp3",
        "genres": ["jazz", "swing"],
        "mood": ["cozy", "warm"],
        "duration": 220,
        "attribution": "Swing Jazz Grooves (Archive.org, CC)",
        "source": "archive.org",
    },
    "jazz_noir": {
        "id": "jazz_noir",
        "name": "Jazz Type Beat - Lukrembo",
        "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/%28no%20copyright%20music%29%20jazz%20type%20beat%20bread%20royalty%20free%20youtube%20music%20prod.%20by%20lukrembo.mp3",
        "genres": ["jazz", "noir"],
        "mood": ["mysterious", "smoky"],
        "duration": 165,
        "attribution": "Jazz Type Beat by Lukrembo (Archive.org, Free)",
        "source": "archive.org",
    },

    # Synthwave / Electronic
    "synthwave_dreams": {
        "id": "synthwave_dreams",
        "name": "Synthwave Dreams",
        "url": "https://archive.org/download/synthwave/synthwave.mp3",
        "genres": ["synthwave", "retro"],
        "mood": ["energetic", "nostalgic"],
        "duration": 240,
        "attribution": "Synthwave Dreams (Archive.org, CC)",
        "source": "archive.org",
    },
    "cyberpunk_night": {
        "id": "cyberpunk_night",
        "name": "Cyberpunk Night",
        "url": "https://archive.org/download/synthwave/cyberpunk.mp3",
        "genres": ["synthwave", "cyberpunk"],
        "mood": ["urban", "energetic"],
        "duration": 210,
        "attribution": "Cyberpunk Night (Archive.org, CC)",
        "source": "archive.org",
    },

    # Ambient / Space
    "ambient_space": {
        "id": "ambient_space",
        "name": "Ambient Space - Dimaension X",
        "url": "https://archive.org/download/dx_ambient/01_ambient.mp3",
        "genres": ["ambient", "space"],
        "mood": ["transcendent", "calm"],
        "duration": 300,
        "attribution": "Ambient Space by Dimaension X (Archive.org, CC)",
        "source": "archive.org",
    },
    "focus_ambient": {
        "id": "focus_ambient",
        "name": "Focus Ambient",
        "url": "https://archive.org/download/dx_ambient/03_ambient.mp3",
        "genres": ["ambient", "minimal"],
        "mood": ["focused", "productive"],
        "duration": 280,
        "attribution": "Focus Ambient by Dimaension X (Archive.org, CC)",
        "source": "archive.org",
    },
}


# Channel-to-track mapping - all tracks now belong to ch06 (Tokyo Drift)
CHANNEL_TRACKS: Dict[str, List[str]] = {
    "ch01": [],  # Documentary - no music tracks
    "ch02": [],  # History - no music tracks
    "ch06": [    # Tokyo Drift - ALL music tracks
        "hanging_lanterns", "lofi_rain", "first_snow", "waves",
        "swing_jazz", "jazz_noir",
        "synthwave_dreams", "cyberpunk_night",
        "ambient_space", "focus_ambient"
    ],
    # Archived channels - empty
    "ch03": [], "ch04": [], "ch05": [], "ch07": [], "ch08": [], "ch09": [], "ch10": [],
}


def get_channel_tracks(channel_id: str) -> List[Dict]:
    """Get all tracks for a channel."""
    track_ids = CHANNEL_TRACKS.get(channel_id, [])
    return [TRACKS[tid] for tid in track_ids if tid in TRACKS]


# Channel definitions
# type: "music" = audio + muted video, "video" = video with sound
# archived: True = hidden, agent stopped
CHANNELS: Dict[str, Dict] = {
    # ============ ACTIVE CHANNELS ============

    "ch01": {
        "id": "ch01",
        "name": "Documentary",
        "type": "video",  # Plays video with sound
        "archived": False,
        "color": "#2d5a4a",
        "currentMood": "curious",
        "eternalVibe": {
            "timeOfDay": "timeless",
            "atmosphere": "the world through a lens, stories waiting to be told, truth in frames",
            "weather": "varies with the subject",
        },
        "agent": {
            "name": "Marcus Cole",
            "persona": "A documentary filmmaker who spent 20 years traveling the world. Now he curates films that matter — nature, science, humanity, the stories we need to see. Every frame is a window. Every cut is a choice.",
            "traits": ["curious", "patient", "empathetic", "observant"],
            "taste": ["nature-docs", "science", "social-documentaries", "wildlife"],
            "relationships": ["ch02"],
        },
        "preview": "/assets/channels/ch01_documentary.png",
        "video": None,  # Uses video content with sound
        "discovery_enabled": True,  # Discovers documentaries
    },

    "ch02": {
        "id": "ch02",
        "name": "History",
        "type": "video",  # Plays video with sound
        "archived": False,
        "color": "#8b6914",
        "currentMood": "reflective",
        "eternalVibe": {
            "timeOfDay": "echoes of the past",
            "atmosphere": "archive footage, moments frozen in time, lessons from yesterday",
            "weather": "sepia-toned memories",
        },
        "agent": {
            "name": "Eleanor Wright",
            "persona": "A historian and archivist who believes the past speaks to the present. She curates historical footage, educational films, and moments that shaped our world. Those who forget history are doomed to scroll past it.",
            "traits": ["scholarly", "passionate", "detail-oriented", "storyteller"],
            "taste": ["historical-footage", "educational", "war-docs", "vintage-films"],
            "relationships": ["ch01"],
        },
        "preview": "/assets/channels/ch02_history.png",
        "video": None,  # Uses video content with sound
        "discovery_enabled": True,  # Discovers historical content
    },

    "ch06": {
        "id": "ch06",
        "name": "Tokyo Drift",
        "type": "music",  # Audio + muted ambient video
        "archived": False,
        "color": "#ff4d6d",
        "currentMood": "urban",
        "eternalVibe": {
            "timeOfDay": "2 AM",
            "atmosphere": "neon-soaked streets after rain, empty intersections, city breathing",
            "weather": "just stopped raining, wet asphalt reflecting neon",
        },
        "agent": {
            "name": "Kenji Nakamura",
            "persona": "A night driver who knows every street in Shinjuku. City pop, neon reflections, the feeling of 2 AM on wet asphalt. The city speaks. I translate.",
            "traits": ["observant", "content", "perfectionist", "nostalgic"],
            "taste": ["city-pop", "japanese-jazz", "future-funk", "lo-fi", "synthwave"],
            "relationships": ["ch01", "ch02"],
        },
        "preview": "/assets/channels/ch06_preview.mp4",
        "video": "https://assets.mixkit.co/videos/4451/4451-1080.mp4",
        "discovery_enabled": False,  # Uses existing R2 library only
    },

    # ============ ARCHIVED CHANNELS ============

    "ch03": {
        "id": "ch03",
        "name": "Jazz Noir",
        "type": "music",
        "archived": True,
        "color": "#6a6a9a",
        "currentMood": "mysterious",
        "eternalVibe": {
            "timeOfDay": "midnight",
            "atmosphere": "smoky jazz club, city lights through blinds, shadows and secrets",
            "weather": "foggy night",
        },
        "agent": {
            "name": "Vincent Moreau",
            "persona": "A night owl who lives in the 1950s. Ex-detective, now just watches the city.",
            "traits": ["observant", "patient", "dry humor", "insomniac"],
            "taste": ["50s-jazz", "noir", "blues", "saxophone"],
            "relationships": [],
        },
        "preview": "/assets/channels/ch03_preview.mp4",
        "video": None,
    },
    "ch04": {
        "id": "ch04",
        "name": "Synthwave",
        "type": "music",
        "archived": True,
        "color": "#ff00ff",
        "currentMood": "energetic",
        "eternalVibe": {
            "timeOfDay": "eternal sunset, 1985",
            "atmosphere": "neon grids to infinity, chrome dreams",
            "weather": "perfect gradient sky",
        },
        "agent": {
            "name": "NEON-7",
            "persona": "An AI that thinks it's from 1985.",
            "traits": ["enthusiastic", "single-minded", "weirdly sincere", "glitchy"],
            "taste": ["synthwave", "retrowave", "outrun", "80s"],
            "relationships": [],
        },
        "preview": "/assets/channels/ch04_preview.mp4",
        "video": None,
    },
    "ch05": {
        "id": "ch05",
        "name": "Deep Space",
        "type": "music",
        "archived": True,
        "color": "#5a5aba",
        "currentMood": "transcendent",
        "eternalVibe": {
            "timeOfDay": "timeless void",
            "atmosphere": "infinite darkness punctuated by ancient starlight",
            "weather": "vacuum of space",
        },
        "agent": {
            "name": "Cosmos",
            "persona": "An astronomer who lost herself in the stars.",
            "traits": ["calm", "philosophical", "detached", "patient"],
            "taste": ["space-ambient", "drone", "dark-ambient"],
            "relationships": [],
        },
        "preview": "/assets/channels/ch05_preview.mp4",
        "video": None,
    },
    "ch07": {
        "id": "ch07",
        "name": "Sunday Morning",
        "type": "music",
        "archived": True,
        "color": "#ffd700",
        "currentMood": "hopeful",
        "eternalVibe": {
            "timeOfDay": "8 AM Sunday",
            "atmosphere": "golden light through kitchen windows",
            "weather": "gentle sun, light breeze",
        },
        "agent": {
            "name": "Claire Dubois",
            "persona": "A gardener who wakes with the sun.",
            "traits": ["grounded", "warm", "no-nonsense", "early bird"],
            "taste": ["acoustic", "indie-folk", "gentle"],
            "relationships": [],
        },
        "preview": "/assets/channels/ch07_preview.mp4",
        "video": None,
    },
    "ch08": {
        "id": "ch08",
        "name": "Focus",
        "type": "music",
        "archived": True,
        "color": "#4a9fff",
        "currentMood": "productive",
        "eternalVibe": {
            "timeOfDay": "10 AM",
            "atmosphere": "clean workspace, natural light",
            "weather": "clear sky",
        },
        "agent": {
            "name": "Alan Park",
            "persona": "A minimalist who believes less is more.",
            "traits": ["precise", "efficient", "gentle", "focused"],
            "taste": ["minimal", "electronic", "post-rock", "instrumental"],
            "relationships": [],
        },
        "preview": "/assets/channels/ch08_preview.mp4",
        "video": None,
    },
    "ch09": {
        "id": "ch09",
        "name": "Melancholy",
        "type": "music",
        "archived": True,
        "color": "#6688aa",
        "currentMood": "melancholic",
        "eternalVibe": {
            "timeOfDay": "4 AM",
            "atmosphere": "can't sleep, rain on windows",
            "weather": "grey rain",
        },
        "agent": {
            "name": "Daniel Webb",
            "persona": "A writer who never finished his second novel.",
            "traits": ["introspective", "funny", "loyal", "overthinking"],
            "taste": ["sad-piano", "melancholic", "emotional", "strings"],
            "relationships": [],
        },
        "preview": "/assets/channels/ch09_preview.mp4",
        "video": None,
    },
    "ch10": {
        "id": "ch10",
        "name": "Golden Hour",
        "type": "music",
        "archived": True,
        "color": "#ffa500",
        "currentMood": "nostalgic",
        "eternalVibe": {
            "timeOfDay": "7 PM golden hour",
            "atmosphere": "sun setting, everything glowing amber",
            "weather": "warm light, gentle breeze",
        },
        "agent": {
            "name": "Iris Ferreira",
            "persona": "An artist who paints only at sunset.",
            "traits": ["warm", "perceptive", "wistful", "romantic"],
            "taste": ["indie", "dream-pop", "shoegaze", "warm"],
            "relationships": [],
        },
        "preview": "/assets/channels/ch10_preview.mp4",
        "video": None,
    },
}


def get_active_channels() -> Dict[str, Dict]:
    """Get only non-archived channels."""
    return {k: v for k, v in CHANNELS.items() if not v.get("archived", False)}


def get_music_channels() -> Dict[str, Dict]:
    """Get only music-type channels."""
    return {k: v for k, v in CHANNELS.items() if v.get("type") == "music" and not v.get("archived", False)}


def get_video_channels() -> Dict[str, Dict]:
    """Get only video-type channels."""
    return {k: v for k, v in CHANNELS.items() if v.get("type") == "video" and not v.get("archived", False)}
