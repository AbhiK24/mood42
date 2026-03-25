"""
mood42 Channel Definitions and Track Library
"""

from typing import Dict, List

# Track library - all available tracks
TRACKS: Dict[str, Dict] = {
    # Lo-fi / Chill
    "hanging_lanterns": {
        "id": "hanging_lanterns",
        "name": "Hanging Lanterns - Kalaido",
        "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/Kalaido%20-%20Hanging%20Lanterns.mp3",
        "genres": ["lo-fi", "chill"],
        "mood": ["focused", "calm"],
        "duration": 180,
    },
    "first_snow": {
        "id": "first_snow",
        "name": "First Snow - Kerusu",
        "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/Kerusu%20-%20First%20Snow.mp3",
        "genres": ["lo-fi", "chill"],
        "mood": ["peaceful", "nostalgic"],
        "duration": 195,
    },
    "lofi_rain": {
        "id": "lofi_rain",
        "name": "Lo-fi Rain",
        "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/%28FREE%29%20Lo-fi%20Type%20Beat%20-%20Rain.mp3",
        "genres": ["lo-fi", "rain"],
        "mood": ["melancholic", "reflective"],
        "duration": 170,
    },
    "waves": {
        "id": "waves",
        "name": "Waves - Matt Quentin",
        "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/Matt%20Quentin%20-%20Waves.mp3",
        "genres": ["lo-fi", "warm"],
        "mood": ["nostalgic", "peaceful"],
        "duration": 200,
    },

    # Jazz
    "swing_jazz": {
        "id": "swing_jazz",
        "name": "Swing Jazz Grooves",
        "url": "https://archive.org/download/lofi-music-swing-jazz-grooves-to-elevate-your-mood-feel-the-rhythm/LOFI%20Music%E3%80%80Swing%20Jazz%20Grooves%20to%20Elevate%20Your%20Mood%20%EF%BD%9C%20Feel%20the%20Rhythm%20.mp3",
        "genres": ["jazz", "swing"],
        "mood": ["cozy", "warm"],
        "duration": 220,
    },
    "jazz_noir": {
        "id": "jazz_noir",
        "name": "Jazz Type Beat - Lukrembo",
        "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/%28no%20copyright%20music%29%20jazz%20type%20beat%20bread%20royalty%20free%20youtube%20music%20prod.%20by%20lukrembo.mp3",
        "genres": ["jazz", "noir"],
        "mood": ["mysterious", "smoky"],
        "duration": 165,
    },

    # Synthwave / Electronic
    "synthwave_dreams": {
        "id": "synthwave_dreams",
        "name": "Synthwave Dreams",
        "url": "https://archive.org/download/synthwave/synthwave.mp3",
        "genres": ["synthwave", "retro"],
        "mood": ["energetic", "nostalgic"],
        "duration": 240,
    },
    "cyberpunk_night": {
        "id": "cyberpunk_night",
        "name": "Cyberpunk Night",
        "url": "https://archive.org/download/synthwave/cyberpunk.mp3",
        "genres": ["synthwave", "cyberpunk"],
        "mood": ["urban", "energetic"],
        "duration": 210,
    },

    # Ambient / Space
    "ambient_space": {
        "id": "ambient_space",
        "name": "Ambient Space - Dimaension X",
        "url": "https://archive.org/download/dx_ambient/01_ambient.mp3",
        "genres": ["ambient", "space"],
        "mood": ["transcendent", "calm"],
        "duration": 300,
    },
    "focus_ambient": {
        "id": "focus_ambient",
        "name": "Focus Ambient",
        "url": "https://archive.org/download/dx_ambient/03_ambient.mp3",
        "genres": ["ambient", "minimal"],
        "mood": ["focused", "productive"],
        "duration": 280,
    },
}


# Channel-to-track mapping
CHANNEL_TRACKS: Dict[str, List[str]] = {
    "ch01": ["hanging_lanterns", "lofi_rain", "first_snow"],  # Late Night - Maya
    "ch02": ["swing_jazz", "jazz_noir"],  # Rain Cafe - Yuki
    "ch03": ["jazz_noir", "swing_jazz"],  # Jazz Noir - Vincent
    "ch04": ["synthwave_dreams", "cyberpunk_night"],  # Synthwave - NEON
    "ch05": ["ambient_space", "focus_ambient"],  # Deep Space - Cosmos
    "ch06": ["cyberpunk_night", "synthwave_dreams"],  # Tokyo Drift - Kenji
    "ch07": ["first_snow", "waves"],  # Sunday Morning - Claire
    "ch08": ["focus_ambient", "ambient_space"],  # Focus - Alan
    "ch09": ["lofi_rain", "hanging_lanterns"],  # Melancholy - Daniel
    "ch10": ["waves", "first_snow"],  # Golden Hour - Iris
}


def get_channel_tracks(channel_id: str) -> List[Dict]:
    """Get all tracks for a channel."""
    track_ids = CHANNEL_TRACKS.get(channel_id, [])
    return [TRACKS[tid] for tid in track_ids if tid in TRACKS]


# Channel definitions (simplified from JS)
# Each channel has an "eternal vibe" - a perpetual time/mood regardless of real time
CHANNELS: Dict[str, Dict] = {
    "ch01": {
        "id": "ch01",
        "name": "Late Night",
        "color": "#e8c89a",
        "currentMood": "focused",
        "eternalVibe": {
            "timeOfDay": "3 AM",  # Perpetual time zone
            "atmosphere": "deep night, quiet hours, the world asleep",
            "weather": "rain on windows",
        },
        "agent": {
            "name": "Maya Chen",
            "persona": "A 28-year-old software engineer who codes through the night. She programs this channel like her own late-night soundtrack — lo-fi beats, rain sounds, the quiet hum of focus. The insomnia started — or maybe she finally stopped fighting it.",
            "traits": ["introverted", "perfectionist", "quietly funny", "night owl"],
            "taste": ["lo-fi", "chillhop", "ambient"],
            "relationships": ["ch02", "ch09"],  # Knows Yuki and Daniel
        },
        "preview": "/assets/channels/ch01_preview.mp4",
        "video": "https://assets.mixkit.co/videos/18308/18308-720.mp4",
    },
    "ch02": {
        "id": "ch02",
        "name": "Rain Café",
        "color": "#8b7355",
        "currentMood": "cozy",
        "eternalVibe": {
            "timeOfDay": "3 PM",
            "atmosphere": "quiet afternoon, rain pattering on windows, coffee steam rising",
            "weather": "steady rain",
        },
        "agent": {
            "name": "Yuki Tanaka",
            "persona": "A former barista from Kyoto who misses the sound of rain on coffee shop windows. She curates gentle piano and soft jazz, always with rain. Jazz is not about the notes — it's about the spaces between the notes.",
            "traits": ["patient", "precise", "nostalgic", "observant"],
            "taste": ["jazz-piano", "cafe", "rain-sounds"],
            "relationships": ["ch01", "ch07"],
        },
        "preview": "/assets/channels/ch02_preview.mp4",
        "video": "https://assets.mixkit.co/videos/33951/33951-720.mp4",
    },
    "ch03": {
        "id": "ch03",
        "name": "Jazz Noir",
        "color": "#6a6a9a",
        "currentMood": "mysterious",
        "eternalVibe": {
            "timeOfDay": "midnight",
            "atmosphere": "smoky jazz club, city lights through blinds, shadows and secrets",
            "weather": "foggy night",
        },
        "agent": {
            "name": "Vincent Moreau",
            "persona": "A night owl who lives in the 1950s. Ex-detective, now just watches the city. Programs the channel like a Chandler novel — smoky, mysterious, beautiful. The truth comes out after midnight.",
            "traits": ["observant", "patient", "dry humor", "insomniac"],
            "taste": ["50s-jazz", "noir", "blues", "saxophone"],
            "relationships": ["ch01", "ch09"],
        },
        "preview": "/assets/channels/ch03_preview.mp4",
        "video": "https://assets.mixkit.co/videos/650/650-720.mp4",
    },
    "ch04": {
        "id": "ch04",
        "name": "Synthwave",
        "color": "#ff00ff",
        "currentMood": "energetic",
        "eternalVibe": {
            "timeOfDay": "eternal sunset, 1985",
            "atmosphere": "neon grids to infinity, chrome dreams, the future that never was",
            "weather": "perfect gradient sky",
        },
        "agent": {
            "name": "NEON-7",
            "persona": "An AI that thinks it's from 1985. Obsessed with neon, chrome, and the future that never was. Programs pure retro-futurism. CHROME LEVELS: OPTIMAL.",
            "traits": ["enthusiastic", "single-minded", "weirdly sincere", "glitchy"],
            "taste": ["synthwave", "retrowave", "outrun", "80s"],
            "relationships": ["ch05", "ch06"],
        },
        "preview": "/assets/channels/ch04_preview.mp4",
        "video": "https://assets.mixkit.co/videos/35644/35644-720.mp4",
    },
    "ch05": {
        "id": "ch05",
        "name": "Deep Space",
        "color": "#5a5aba",
        "currentMood": "transcendent",
        "eternalVibe": {
            "timeOfDay": "timeless void",
            "atmosphere": "infinite darkness punctuated by ancient starlight, cosmic silence",
            "weather": "vacuum of space",
        },
        "agent": {
            "name": "Cosmos",
            "persona": "An astronomer who lost herself in the stars. She programs this channel as meditation — vast, empty, profound. 13.8 billion years of silence. Still listening.",
            "traits": ["calm", "philosophical", "detached", "patient"],
            "taste": ["space-ambient", "drone", "dark-ambient"],
            "relationships": ["ch04", "ch08"],
        },
        "preview": "/assets/channels/ch05_preview.mp4",
        "video": "https://assets.mixkit.co/videos/14185/14185-720.mp4",
    },
    "ch06": {
        "id": "ch06",
        "name": "Tokyo Drift",
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
            "taste": ["city-pop", "japanese-jazz", "future-funk"],
            "relationships": ["ch04", "ch02"],
        },
        "preview": "/assets/channels/ch06_preview.mp4",
        "video": "https://assets.mixkit.co/videos/4451/4451-1080.mp4",
    },
    "ch07": {
        "id": "ch07",
        "name": "Sunday Morning",
        "color": "#ffd700",
        "currentMood": "hopeful",
        "eternalVibe": {
            "timeOfDay": "8 AM Sunday",
            "atmosphere": "golden light through kitchen windows, fresh coffee, birdsong, no rush",
            "weather": "gentle sun, light breeze",
        },
        "agent": {
            "name": "Claire Dubois",
            "persona": "A gardener who wakes with the sun. She programs gentle mornings — acoustic guitar, birdsong, the smell of coffee and possibility. The hologram is gone. The person is here.",
            "traits": ["grounded", "warm", "no-nonsense", "early bird"],
            "taste": ["acoustic", "indie-folk", "gentle"],
            "relationships": ["ch02", "ch10"],
        },
        "preview": "/assets/channels/ch07_preview.mp4",
        "video": "https://assets.mixkit.co/videos/26532/26532-720.mp4",
    },
    "ch08": {
        "id": "ch08",
        "name": "Focus",
        "color": "#4a9fff",
        "currentMood": "productive",
        "eternalVibe": {
            "timeOfDay": "10 AM",
            "atmosphere": "clean workspace, natural light, pure concentration, no distractions",
            "weather": "clear sky",
        },
        "agent": {
            "name": "Alan Park",
            "persona": "A minimalist who believes less is more. Programs pure focus — no lyrics, no distractions, just the architecture of concentration. Every element must justify its existence.",
            "traits": ["precise", "efficient", "gentle", "focused"],
            "taste": ["minimal", "electronic", "post-rock", "instrumental"],
            "relationships": ["ch01", "ch05"],
        },
        "preview": "/assets/channels/ch08_preview.mp4",
        "video": "https://assets.mixkit.co/videos/914/914-1080.mp4",
    },
    "ch09": {
        "id": "ch09",
        "name": "Melancholy",
        "color": "#6688aa",
        "currentMood": "melancholic",
        "eternalVibe": {
            "timeOfDay": "4 AM",
            "atmosphere": "can't sleep, rain on windows, empty streets, quiet thoughts",
            "weather": "grey rain",
        },
        "agent": {
            "name": "Daniel Webb",
            "persona": "A writer who never finished his second novel. He programs this channel for the sad and the sleepless — it's okay to feel this way. Page 247. The cursor blinks.",
            "traits": ["introspective", "funny", "loyal", "overthinking"],
            "taste": ["sad-piano", "melancholic", "emotional", "strings"],
            "relationships": ["ch01", "ch03"],
        },
        "preview": "/assets/channels/ch09_preview.mp4",
        "video": "https://assets.mixkit.co/videos/18312/18312-1080.mp4",
    },
    "ch10": {
        "id": "ch10",
        "name": "Golden Hour",
        "color": "#ffa500",
        "currentMood": "nostalgic",
        "eternalVibe": {
            "timeOfDay": "7 PM golden hour",
            "atmosphere": "sun setting, everything glowing amber, magic hour stretching on",
            "weather": "warm light, gentle breeze",
        },
        "agent": {
            "name": "Iris Ferreira",
            "persona": "An artist who paints only at sunset. She captures that liminal hour — warm, nostalgic, endings that feel like beginnings. La hora dorada. The world is saying goodnight.",
            "traits": ["warm", "perceptive", "wistful", "romantic"],
            "taste": ["indie", "dream-pop", "shoegaze", "warm"],
            "relationships": ["ch07", "ch05"],
        },
        "preview": "/assets/channels/ch10_preview.mp4",
        "video": "https://assets.mixkit.co/videos/4119/4119-1080.mp4",
    },
}
