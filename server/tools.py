"""
Content Discovery Tools for mood42 Agents
Search for copyright-free music and videos
PROACTIVE discovery - agents actively search for new content
"""

import httpx
import random
import re
import time
from typing import List, Dict, Optional
from urllib.parse import quote_plus


# ============ MUSIC SOURCES ============

# Track last search time to enable proactive discovery
_last_search_time: Dict[str, float] = {}
SEARCH_COOLDOWN = 120  # Seconds between proactive searches per channel

# Archive.org collections with ambient/lo-fi music (expanded)
ARCHIVE_COLLECTIONS = {
    "lo-fi": [
        "lofi-music-for-study-and-relaxation",
        "kalaido-hanging-lanterns_202101",
        "lofi-music-swing-jazz-grooves-to-elevate-your-mood-feel-the-rhythm",
        "lofi-hip-hop-beats",
        "chillhop-music-collection",
        "study-beats-lofi",
    ],
    "ambient": [
        "dx_ambient",
        "ambient-music-collection",
        "ambient-electronic",
        "space-ambient-music",
        "drone-ambient",
        "dark-ambient-collection",
    ],
    "jazz": [
        "jazz-piano-background-music",
        "smooth-jazz-collection",
        "cafe-jazz-music",
        "late-night-jazz",
        "jazz-lounge",
    ],
    "synthwave": [
        "synthwave",
        "retrowave-collection",
        "80s-synthwave",
        "outrun-music",
        "cyberpunk-music",
    ],
    "piano": [
        "piano-music-collection",
        "relaxing-piano",
        "classical-piano-pieces",
    ],
    "acoustic": [
        "acoustic-guitar-music",
        "folk-acoustic-collection",
    ],
}

# Pre-curated tracks from Archive.org and other CC sources (expanded library)
CURATED_TRACKS = {
    "lo-fi": [
        {
            "id": "hanging_lanterns",
            "name": "Hanging Lanterns - Kalaido",
            "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/Kalaido%20-%20Hanging%20Lanterns.mp3",
            "genres": ["lo-fi", "chill"],
            "duration": 180,
        },
        {
            "id": "first_snow",
            "name": "First Snow - Kerusu",
            "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/Kerusu%20-%20First%20Snow.mp3",
            "genres": ["lo-fi", "chill"],
            "duration": 195,
        },
        {
            "id": "lofi_rain",
            "name": "Lo-fi Rain Beat",
            "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/%28FREE%29%20Lo-fi%20Type%20Beat%20-%20Rain.mp3",
            "genres": ["lo-fi", "rain"],
            "duration": 170,
        },
        {
            "id": "waves_matt",
            "name": "Waves - Matt Quentin",
            "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/Matt%20Quentin%20-%20Waves.mp3",
            "genres": ["lo-fi", "warm"],
            "duration": 200,
        },
        {
            "id": "sleepy_fish",
            "name": "Sleepy Fish - Beneath the Moonlight",
            "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/Sleepy%20Fish%20-%20Beneath%20the%20Moonlight.mp3",
            "genres": ["lo-fi", "night"],
            "duration": 185,
        },
        # Additional lo-fi tracks from Pixabay (CC0)
        {
            "id": "lofi_chill_01",
            "name": "Chill Lo-Fi Vibes",
            "url": "https://cdn.pixabay.com/download/audio/2022/05/27/audio_1808fbf07a.mp3",
            "genres": ["lo-fi", "chill"],
            "duration": 165,
        },
        {
            "id": "lofi_study_01",
            "name": "Study Session",
            "url": "https://cdn.pixabay.com/download/audio/2024/09/10/audio_6e5d7d1912.mp3",
            "genres": ["lo-fi", "study"],
            "duration": 180,
        },
        {
            "id": "lofi_night_drive",
            "name": "Night Drive Lo-Fi",
            "url": "https://cdn.pixabay.com/download/audio/2023/07/30/audio_e94bb32f96.mp3",
            "genres": ["lo-fi", "night"],
            "duration": 190,
        },
        {
            "id": "lofi_coffee_shop",
            "name": "Coffee Shop Beats",
            "url": "https://cdn.pixabay.com/download/audio/2022/10/25/audio_946bc46a39.mp3",
            "genres": ["lo-fi", "cafe"],
            "duration": 175,
        },
        {
            "id": "lofi_rainy_day",
            "name": "Rainy Day Vibes",
            "url": "https://cdn.pixabay.com/download/audio/2023/04/11/audio_85e0a27e07.mp3",
            "genres": ["lo-fi", "rain"],
            "duration": 200,
        },
    ],
    "jazz": [
        {
            "id": "swing_jazz",
            "name": "Swing Jazz Grooves",
            "url": "https://archive.org/download/lofi-music-swing-jazz-grooves-to-elevate-your-mood-feel-the-rhythm/LOFI%20Music%E3%80%80Swing%20Jazz%20Grooves%20to%20Elevate%20Your%20Mood%20%EF%BD%9C%20Feel%20the%20Rhythm%20.mp3",
            "genres": ["jazz", "swing"],
            "duration": 220,
        },
        {
            "id": "jazz_noir_beat",
            "name": "Jazz Type Beat - Lukrembo",
            "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/%28no%20copyright%20music%29%20jazz%20type%20beat%20bread%20royalty%20free%20youtube%20music%20prod.%20by%20lukrembo.mp3",
            "genres": ["jazz", "noir"],
            "duration": 165,
        },
        # Additional jazz from Pixabay
        {
            "id": "jazz_cafe_01",
            "name": "Cafe Jazz Piano",
            "url": "https://cdn.pixabay.com/download/audio/2022/03/10/audio_2c27c91ea6.mp3",
            "genres": ["jazz", "piano", "cafe"],
            "duration": 195,
        },
        {
            "id": "jazz_smooth_01",
            "name": "Smooth Jazz Evening",
            "url": "https://cdn.pixabay.com/download/audio/2023/09/04/audio_25bca0c9cb.mp3",
            "genres": ["jazz", "smooth"],
            "duration": 210,
        },
        {
            "id": "jazz_night_club",
            "name": "Late Night Jazz Club",
            "url": "https://cdn.pixabay.com/download/audio/2022/05/16/audio_bf04b4b6ae.mp3",
            "genres": ["jazz", "noir", "night"],
            "duration": 185,
        },
        {
            "id": "jazz_bossa_01",
            "name": "Bossa Nova Cafe",
            "url": "https://cdn.pixabay.com/download/audio/2022/09/07/audio_5db1bd53b7.mp3",
            "genres": ["jazz", "bossa", "chill"],
            "duration": 200,
        },
    ],
    "ambient": [
        {
            "id": "ambient_space_01",
            "name": "Ambient Space - Dimaension X",
            "url": "https://archive.org/download/dx_ambient/01_ambient.mp3",
            "genres": ["ambient", "space"],
            "duration": 300,
        },
        {
            "id": "ambient_focus",
            "name": "Focus Ambient",
            "url": "https://archive.org/download/dx_ambient/03_ambient.mp3",
            "genres": ["ambient", "minimal"],
            "duration": 280,
        },
        {
            "id": "ambient_deep",
            "name": "Deep Ambient",
            "url": "https://archive.org/download/dx_ambient/02_ambient.mp3",
            "genres": ["ambient", "deep"],
            "duration": 320,
        },
        # Additional ambient from Pixabay
        {
            "id": "ambient_meditation",
            "name": "Meditation Soundscape",
            "url": "https://cdn.pixabay.com/download/audio/2022/03/24/audio_9f3bdbaa77.mp3",
            "genres": ["ambient", "meditation"],
            "duration": 240,
        },
        {
            "id": "ambient_forest",
            "name": "Forest Ambience",
            "url": "https://cdn.pixabay.com/download/audio/2023/10/30/audio_b889df0ebe.mp3",
            "genres": ["ambient", "nature"],
            "duration": 260,
        },
        {
            "id": "ambient_cosmic",
            "name": "Cosmic Dreams",
            "url": "https://cdn.pixabay.com/download/audio/2022/08/02/audio_884fe92c21.mp3",
            "genres": ["ambient", "space", "cosmic"],
            "duration": 300,
        },
        {
            "id": "ambient_underwater",
            "name": "Underwater World",
            "url": "https://cdn.pixabay.com/download/audio/2022/11/22/audio_a156e7c6e2.mp3",
            "genres": ["ambient", "underwater"],
            "duration": 275,
        },
    ],
    "synthwave": [
        {
            "id": "synthwave_dreams",
            "name": "Synthwave Dreams",
            "url": "https://cdn.pixabay.com/download/audio/2022/04/27/audio_67bcabb5c4.mp3",
            "genres": ["synthwave", "retro"],
            "duration": 240,
        },
        {
            "id": "cyberpunk_night",
            "name": "Cyberpunk Night",
            "url": "https://cdn.pixabay.com/download/audio/2023/03/16/audio_8cb749bf65.mp3",
            "genres": ["synthwave", "cyberpunk"],
            "duration": 210,
        },
        {
            "id": "retrowave_01",
            "name": "Retrowave Cruise",
            "url": "https://cdn.pixabay.com/download/audio/2022/10/06/audio_df0d3952ab.mp3",
            "genres": ["synthwave", "retro", "80s"],
            "duration": 195,
        },
        {
            "id": "neon_city",
            "name": "Neon City Nights",
            "url": "https://cdn.pixabay.com/download/audio/2023/05/22/audio_be3a4dca3f.mp3",
            "genres": ["synthwave", "neon", "city"],
            "duration": 220,
        },
        {
            "id": "outrun_drive",
            "name": "Outrun Night Drive",
            "url": "https://cdn.pixabay.com/download/audio/2022/06/20/audio_ea18f3d10e.mp3",
            "genres": ["synthwave", "outrun"],
            "duration": 185,
        },
    ],
    "acoustic": [
        {
            "id": "acoustic_morning",
            "name": "Morning Light - Acoustic",
            "url": "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0a13f69d2.mp3",
            "genres": ["acoustic", "peaceful"],
            "duration": 195,
        },
        {
            "id": "acoustic_guitar_01",
            "name": "Gentle Guitar",
            "url": "https://cdn.pixabay.com/download/audio/2022/08/04/audio_2dde668d05.mp3",
            "genres": ["acoustic", "guitar"],
            "duration": 180,
        },
        {
            "id": "acoustic_folk_01",
            "name": "Folk Morning",
            "url": "https://cdn.pixabay.com/download/audio/2023/02/08/audio_8164f6a9c5.mp3",
            "genres": ["acoustic", "folk"],
            "duration": 200,
        },
    ],
    "piano": [
        {
            "id": "piano_soft_01",
            "name": "Soft Piano Dreams",
            "url": "https://cdn.pixabay.com/download/audio/2022/02/07/audio_95ca4a53df.mp3",
            "genres": ["piano", "calm"],
            "duration": 215,
        },
        {
            "id": "piano_emotional",
            "name": "Emotional Piano",
            "url": "https://cdn.pixabay.com/download/audio/2023/07/03/audio_850865b86c.mp3",
            "genres": ["piano", "emotional"],
            "duration": 230,
        },
        {
            "id": "piano_rain",
            "name": "Piano in the Rain",
            "url": "https://cdn.pixabay.com/download/audio/2022/12/13/audio_3ff40ab2b9.mp3",
            "genres": ["piano", "rain"],
            "duration": 195,
        },
    ],
    "electronic": [
        {
            "id": "electronic_chill_01",
            "name": "Electronic Chill",
            "url": "https://cdn.pixabay.com/download/audio/2022/11/04/audio_3458d76a3f.mp3",
            "genres": ["electronic", "chill"],
            "duration": 205,
        },
        {
            "id": "electronic_deep",
            "name": "Deep Electronic",
            "url": "https://cdn.pixabay.com/download/audio/2023/01/24/audio_69a61cd6d7.mp3",
            "genres": ["electronic", "deep"],
            "duration": 220,
        },
    ],
}


async def search_music(query: str, mood: Optional[str] = None) -> List[Dict]:
    """
    Search for copyright-free music matching the query.
    Returns list of track objects with url, name, genres.
    """
    query_lower = query.lower()
    results = []

    # First, search curated tracks
    for genre, tracks in CURATED_TRACKS.items():
        for track in tracks:
            # Check if query matches genre or track name
            if (query_lower in genre.lower() or
                query_lower in track["name"].lower() or
                any(query_lower in g.lower() for g in track.get("genres", []))):
                results.append(track)

    # Also check mood mapping
    mood_to_genre = {
        "calm": ["lo-fi", "ambient", "piano"],
        "focused": ["lo-fi", "ambient", "electronic"],
        "energetic": ["synthwave", "electronic"],
        "melancholic": ["jazz", "lo-fi", "piano"],
        "cozy": ["jazz", "lo-fi", "acoustic"],
        "mysterious": ["jazz", "ambient"],
        "nostalgic": ["synthwave", "lo-fi"],
        "peaceful": ["acoustic", "ambient", "piano"],
        "transcendent": ["ambient"],
        "urban": ["synthwave", "electronic"],
        "reflective": ["piano", "ambient"],
        "dreamy": ["lo-fi", "ambient"],
    }

    if mood and mood.lower() in mood_to_genre:
        for genre in mood_to_genre[mood.lower()]:
            if genre in CURATED_TRACKS:
                for track in CURATED_TRACKS[genre]:
                    if track not in results:
                        results.append(track)

    # Try Archive.org search for more results (always search to expand library)
    archive_results = await search_archive_org(query)
    results.extend(archive_results)

    # Deduplicate by URL
    seen_urls = set()
    unique_results = []
    for track in results:
        if track["url"] not in seen_urls:
            seen_urls.add(track["url"])
            unique_results.append(track)

    # Shuffle results to provide variety
    random.shuffle(unique_results)
    return unique_results[:15]  # Return top 15


async def proactive_discover(channel_id: str, mood: str, period: str) -> Optional[Dict]:
    """
    Proactively discover new content for a channel.
    Called periodically to keep content fresh.
    """
    global _last_search_time

    now = time.time()
    last_search = _last_search_time.get(channel_id, 0)

    # Only search if cooldown has passed
    if now - last_search < SEARCH_COOLDOWN:
        return None

    _last_search_time[channel_id] = now

    # Generate search based on channel mood and time of day
    period_queries = {
        "night": ["late night chill", "midnight ambient", "nocturnal beats"],
        "morning": ["morning ambient", "sunrise vibes", "peaceful wake up"],
        "afternoon": ["focus beats", "productive ambient", "afternoon jazz"],
        "evening": ["sunset chill", "evening jazz", "twilight ambient"],
    }

    mood_queries = {
        "calm": ["calm ambient", "peaceful music", "relaxing piano"],
        "focused": ["focus music", "concentration beats", "study ambient"],
        "energetic": ["upbeat electronic", "energetic synthwave"],
        "melancholic": ["melancholic piano", "sad jazz", "emotional ambient"],
        "cozy": ["cozy cafe jazz", "warm lo-fi", "comfort music"],
    }

    # Combine queries
    queries = period_queries.get(period, ["ambient music"])
    if mood.lower() in mood_queries:
        queries.extend(mood_queries[mood.lower()])

    search_query = random.choice(queries)
    print(f"[Discovery] {channel_id} proactively searching: {search_query}")

    results = await search_music(search_query, mood)
    if results:
        return random.choice(results)

    return None


async def search_archive_org(query: str) -> List[Dict]:
    """Search Archive.org for audio files."""
    try:
        encoded_query = quote_plus(f"{query} audio")
        url = f"https://archive.org/advancedsearch.php?q={encoded_query}&fl[]=identifier,title,creator&rows=5&output=json&mediatype=audio"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return []

            data = response.json()
            results = []

            for doc in data.get("response", {}).get("docs", []):
                identifier = doc.get("identifier", "")
                title = doc.get("title", "Unknown")
                creator = doc.get("creator", "Unknown Artist")

                # Construct a likely MP3 URL (Archive.org pattern)
                # Note: This may not always work - would need to fetch item metadata
                results.append({
                    "id": f"archive_{identifier}",
                    "name": f"{title} - {creator}" if creator != "Unknown Artist" else title,
                    "url": f"https://archive.org/download/{identifier}/{identifier}.mp3",
                    "genres": extract_genres_from_query(query),
                    "duration": 180,  # Default
                    "source": "archive.org",
                })

            return results

    except Exception as e:
        print(f"[Tools] Archive.org search failed: {e}")
        return []


def extract_genres_from_query(query: str) -> List[str]:
    """Extract genre tags from search query."""
    query_lower = query.lower()
    genres = []

    genre_keywords = {
        "lo-fi": ["lo-fi", "lofi", "chillhop", "chill"],
        "jazz": ["jazz", "swing", "bebop", "smooth"],
        "ambient": ["ambient", "atmospheric", "drone", "space"],
        "synthwave": ["synthwave", "retrowave", "80s", "neon", "cyberpunk"],
        "acoustic": ["acoustic", "folk", "guitar"],
        "rain": ["rain", "storm", "thunder"],
        "piano": ["piano", "keys"],
    }

    for genre, keywords in genre_keywords.items():
        if any(kw in query_lower for kw in keywords):
            genres.append(genre)

    return genres if genres else ["ambient"]


# ============ VIDEO SOURCES ============

# Mixkit free videos (known working)
CURATED_VIDEOS = {
    "rain": [
        {
            "id": "rain_window",
            "name": "Rain on Window",
            "url": "https://assets.mixkit.co/videos/18308/18308-720.mp4",
            "tags": ["rain", "window", "night"],
        },
        {
            "id": "rain_street",
            "name": "Rainy Street",
            "url": "https://assets.mixkit.co/videos/33951/33951-720.mp4",
            "tags": ["rain", "street", "city"],
        },
    ],
    "city": [
        {
            "id": "tokyo_night",
            "name": "Tokyo Night",
            "url": "https://assets.mixkit.co/videos/4451/4451-1080.mp4",
            "tags": ["tokyo", "neon", "night"],
        },
        {
            "id": "city_lights",
            "name": "City Lights",
            "url": "https://assets.mixkit.co/videos/650/650-720.mp4",
            "tags": ["city", "night", "noir"],
        },
    ],
    "nature": [
        {
            "id": "sunset_golden",
            "name": "Golden Hour Sunset",
            "url": "https://assets.mixkit.co/videos/4119/4119-1080.mp4",
            "tags": ["sunset", "golden", "nature"],
        },
        {
            "id": "morning_light",
            "name": "Morning Light",
            "url": "https://assets.mixkit.co/videos/26532/26532-720.mp4",
            "tags": ["morning", "light", "nature"],
        },
    ],
    "space": [
        {
            "id": "stars_space",
            "name": "Stars in Space",
            "url": "https://assets.mixkit.co/videos/14185/14185-720.mp4",
            "tags": ["space", "stars", "night"],
        },
    ],
    "abstract": [
        {
            "id": "neon_grid",
            "name": "Neon Grid",
            "url": "https://assets.mixkit.co/videos/35644/35644-720.mp4",
            "tags": ["neon", "grid", "synthwave"],
        },
        {
            "id": "minimal_waves",
            "name": "Minimal Waves",
            "url": "https://assets.mixkit.co/videos/914/914-1080.mp4",
            "tags": ["minimal", "abstract", "calm"],
        },
    ],
}


async def search_video(query: str, style: Optional[str] = None) -> List[Dict]:
    """
    Search for copyright-free video loops.
    Returns list of video objects with url, name, tags.
    """
    query_lower = query.lower()
    results = []

    # Search curated videos
    for category, videos in CURATED_VIDEOS.items():
        for video in videos:
            # Check if query matches category or tags
            if (query_lower in category.lower() or
                any(query_lower in tag for tag in video.get("tags", []))):
                results.append(video)

    # Style mapping
    style_to_category = {
        "cinematic": ["rain", "city", "nature"],
        "lo-fi": ["rain", "abstract"],
        "abstract": ["abstract", "space"],
        "neon": ["city", "abstract"],
        "peaceful": ["nature"],
        "noir": ["city", "rain"],
    }

    if style and style.lower() in style_to_category:
        for category in style_to_category[style.lower()]:
            if category in CURATED_VIDEOS:
                for video in CURATED_VIDEOS[category]:
                    if video not in results:
                        results.append(video)

    # Deduplicate
    seen_urls = set()
    unique_results = []
    for video in results:
        if video["url"] not in seen_urls:
            seen_urls.add(video["url"])
            unique_results.append(video)

    return unique_results[:5]


# ============ TOOL EXECUTION ============

async def execute_tool(tool_name: str, arguments: Dict) -> Dict:
    """Execute a tool and return results."""
    if tool_name == "search_music":
        tracks = await search_music(
            arguments.get("query", "ambient"),
            arguments.get("mood")
        )
        return {
            "success": True,
            "tracks": tracks,
            "count": len(tracks),
        }

    elif tool_name == "search_video":
        videos = await search_video(
            arguments.get("query", "ambient"),
            arguments.get("style")
        )
        return {
            "success": True,
            "videos": videos,
            "count": len(videos),
        }

    else:
        return {
            "success": False,
            "error": f"Unknown tool: {tool_name}",
        }


# ============ CONTENT RECOMMENDATIONS ============

def get_tracks_for_channel(channel_id: str, mood: Optional[str] = None) -> List[Dict]:
    """Get recommended tracks for a channel based on its vibe - expanded library."""
    channel_vibes = {
        "ch01": ["lo-fi", "ambient", "piano"],           # Late Night - Maya
        "ch02": ["jazz", "lo-fi", "piano"],              # Rain Cafe - Yuki
        "ch03": ["jazz", "piano"],                       # Jazz Noir - Vincent
        "ch04": ["synthwave", "electronic"],             # Synthwave - NEON
        "ch05": ["ambient", "electronic"],               # Deep Space - Cosmos
        "ch06": ["synthwave", "jazz", "electronic"],     # Tokyo Drift - Kenji
        "ch07": ["acoustic", "lo-fi", "piano"],          # Sunday Morning - Claire
        "ch08": ["ambient", "lo-fi", "electronic"],      # Focus - Alan
        "ch09": ["jazz", "lo-fi", "piano"],              # Melancholy - Daniel
        "ch10": ["lo-fi", "acoustic", "ambient"],        # Golden Hour - Iris
    }

    genres = channel_vibes.get(channel_id, ["lo-fi", "ambient"])
    tracks = []

    for genre in genres:
        if genre in CURATED_TRACKS:
            tracks.extend(CURATED_TRACKS[genre])

    # Deduplicate
    seen_ids = set()
    unique_tracks = []
    for track in tracks:
        if track["id"] not in seen_ids:
            seen_ids.add(track["id"])
            unique_tracks.append(track)

    # Shuffle to provide variety
    random.shuffle(unique_tracks)
    return unique_tracks


def get_videos_for_channel(channel_id: str) -> List[Dict]:
    """Get recommended videos for a channel based on its vibe."""
    channel_visuals = {
        "ch01": ["rain"],              # Late Night
        "ch02": ["rain"],              # Rain Cafe
        "ch03": ["city"],              # Jazz Noir
        "ch04": ["abstract"],          # Synthwave
        "ch05": ["space"],             # Deep Space
        "ch06": ["city"],              # Tokyo Drift
        "ch07": ["nature"],            # Sunday Morning
        "ch08": ["abstract"],          # Focus
        "ch09": ["rain"],              # Melancholy
        "ch10": ["nature"],            # Golden Hour
    }

    categories = channel_visuals.get(channel_id, ["abstract"])
    videos = []

    for category in categories:
        if category in CURATED_VIDEOS:
            videos.extend(CURATED_VIDEOS[category])

    return videos
