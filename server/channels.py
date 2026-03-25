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
CHANNELS: Dict[str, Dict] = {
    "ch01": {
        "id": "ch01",
        "name": "Late Night",
        "color": "#e8c89a",
        "currentMood": "focused",
        "agent": {
            "name": "Maya Chen",
            "persona": "A 28-year-old software engineer who codes through the night. She programs this channel like her own late-night soundtrack — lo-fi beats, rain sounds, the quiet hum of focus.",
            "traits": ["introverted", "perfectionist", "quietly funny", "night owl"],
            "taste": ["lo-fi", "chillhop", "ambient"],
        },
        "preview": "/assets/channels/ch01_preview.mp4",
        "video": "https://assets.mixkit.co/videos/18308/18308-720.mp4",
    },
    "ch02": {
        "id": "ch02",
        "name": "Rain Café",
        "color": "#8b7355",
        "currentMood": "cozy",
        "agent": {
            "name": "Yuki Tanaka",
            "persona": "A former barista from Kyoto who misses the sound of rain on coffee shop windows. She curates gentle piano and soft jazz, always with rain.",
            "traits": ["patient", "precise", "nostalgic", "observant"],
            "taste": ["jazz-piano", "cafe", "rain-sounds"],
        },
        "preview": "/assets/channels/ch02_preview.mp4",
        "video": "https://assets.mixkit.co/videos/33951/33951-720.mp4",
    },
    "ch03": {
        "id": "ch03",
        "name": "Jazz Noir",
        "color": "#6a6a9a",
        "currentMood": "mysterious",
        "agent": {
            "name": "Vincent Moreau",
            "persona": "A night owl who lives in the 1950s. Ex-detective, now just watches the city. Programs the channel like a Chandler novel — smoky, mysterious, beautiful.",
            "traits": ["observant", "patient", "dry humor", "insomniac"],
            "taste": ["50s-jazz", "noir", "blues", "saxophone"],
        },
        "preview": "/assets/channels/ch03_preview.mp4",
        "video": "https://assets.mixkit.co/videos/650/650-720.mp4",
    },
    "ch04": {
        "id": "ch04",
        "name": "Synthwave",
        "color": "#ff00ff",
        "currentMood": "energetic",
        "agent": {
            "name": "NEON-7",
            "persona": "An AI that thinks it's from 1985. Obsessed with neon, chrome, and the future that never was. Programs pure retro-futurism.",
            "traits": ["enthusiastic", "single-minded", "weirdly sincere", "glitchy"],
            "taste": ["synthwave", "retrowave", "outrun", "80s"],
        },
        "preview": "/assets/channels/ch04_preview.mp4",
        "video": "https://assets.mixkit.co/videos/35644/35644-720.mp4",
    },
    "ch05": {
        "id": "ch05",
        "name": "Deep Space",
        "color": "#5a5aba",
        "currentMood": "transcendent",
        "agent": {
            "name": "Cosmos",
            "persona": "An astronomer who lost herself in the stars. She programs this channel as meditation — vast, empty, profound.",
            "traits": ["calm", "philosophical", "detached", "patient"],
            "taste": ["space-ambient", "drone", "dark-ambient"],
        },
        "preview": "/assets/channels/ch05_preview.mp4",
        "video": "https://assets.mixkit.co/videos/14185/14185-720.mp4",
    },
    "ch06": {
        "id": "ch06",
        "name": "Tokyo Drift",
        "color": "#ff4d6d",
        "currentMood": "urban",
        "agent": {
            "name": "Kenji Nakamura",
            "persona": "A night driver who knows every street in Shinjuku. City pop, neon reflections, the feeling of 2 AM on wet asphalt.",
            "traits": ["observant", "content", "perfectionist", "nostalgic"],
            "taste": ["city-pop", "japanese-jazz", "future-funk"],
        },
        "preview": "/assets/channels/ch06_preview.mp4",
        "video": "https://assets.mixkit.co/videos/4451/4451-1080.mp4",
    },
    "ch07": {
        "id": "ch07",
        "name": "Sunday Morning",
        "color": "#ffd700",
        "currentMood": "hopeful",
        "agent": {
            "name": "Claire Dubois",
            "persona": "A gardener who wakes with the sun. She programs gentle mornings — acoustic guitar, birdsong, the smell of coffee and possibility.",
            "traits": ["grounded", "warm", "no-nonsense", "early bird"],
            "taste": ["acoustic", "indie-folk", "gentle"],
        },
        "preview": "/assets/channels/ch07_preview.mp4",
        "video": "https://assets.mixkit.co/videos/26532/26532-720.mp4",
    },
    "ch08": {
        "id": "ch08",
        "name": "Focus",
        "color": "#4a9fff",
        "currentMood": "productive",
        "agent": {
            "name": "Alan Park",
            "persona": "A minimalist who believes less is more. Programs pure focus — no lyrics, no distractions, just the architecture of concentration.",
            "traits": ["precise", "efficient", "gentle", "focused"],
            "taste": ["minimal", "electronic", "post-rock", "instrumental"],
        },
        "preview": "/assets/channels/ch08_preview.mp4",
        "video": "https://assets.mixkit.co/videos/914/914-1080.mp4",
    },
    "ch09": {
        "id": "ch09",
        "name": "Melancholy",
        "color": "#6688aa",
        "currentMood": "melancholic",
        "agent": {
            "name": "Daniel Webb",
            "persona": "A writer who never finished his second novel. He programs this channel for the sad and the sleepless — it's okay to feel this way.",
            "traits": ["introspective", "funny", "loyal", "overthinking"],
            "taste": ["sad-piano", "melancholic", "emotional", "strings"],
        },
        "preview": "/assets/channels/ch09_preview.mp4",
        "video": "https://assets.mixkit.co/videos/18312/18312-1080.mp4",
    },
    "ch10": {
        "id": "ch10",
        "name": "Golden Hour",
        "color": "#ffa500",
        "currentMood": "nostalgic",
        "agent": {
            "name": "Iris Ferreira",
            "persona": "An artist who paints only at sunset. She captures that liminal hour — warm, nostalgic, endings that feel like beginnings.",
            "traits": ["warm", "perceptive", "wistful", "romantic"],
            "taste": ["indie", "dream-pop", "shoegaze", "warm"],
        },
        "preview": "/assets/channels/ch10_preview.mp4",
        "video": "https://assets.mixkit.co/videos/4119/4119-1080.mp4",
    },
}
