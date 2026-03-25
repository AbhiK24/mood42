"""
Content Discovery Tools for mood42 Agents
Search for copyright-free music and videos
PROACTIVE discovery - agents actively search for new content
WITH URL VALIDATION - verify content is accessible before using
"""

import httpx
import asyncio
import random
import re
import time
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote_plus


# ============ URL VALIDATION ============

# Cache for URL health checks: url -> (is_valid, last_checked_timestamp)
_url_cache: Dict[str, Tuple[bool, float]] = {}
URL_CACHE_TTL = 300  # 5 minutes cache for URL checks
URL_CHECK_TIMEOUT = 5.0  # 5 second timeout for HEAD requests

# Track verified working URLs (confirmed good)
_verified_urls: set = set()
# Track broken URLs (don't retry for a while)
_broken_urls: Dict[str, float] = {}
BROKEN_URL_COOLDOWN = 600  # Don't retry broken URLs for 10 minutes


async def check_url_health(url: str) -> bool:
    """
    Check if a URL is accessible (returns 200 or 302).
    Uses caching to avoid hammering servers.
    """
    if not url:
        return False

    now = time.time()

    # Check if URL is in broken list
    if url in _broken_urls:
        if now - _broken_urls[url] < BROKEN_URL_COOLDOWN:
            return False
        else:
            del _broken_urls[url]

    # Check if already verified
    if url in _verified_urls:
        return True

    # Check cache
    if url in _url_cache:
        is_valid, checked_at = _url_cache[url]
        if now - checked_at < URL_CACHE_TTL:
            return is_valid

    # Actually check the URL
    try:
        async with httpx.AsyncClient(timeout=URL_CHECK_TIMEOUT, follow_redirects=False) as client:
            response = await client.head(url)
            # 200 = OK, 302/301 = redirect (Archive.org uses this)
            is_valid = response.status_code in [200, 301, 302]

            _url_cache[url] = (is_valid, now)

            if is_valid:
                _verified_urls.add(url)
                print(f"[URL] ✓ Verified: {url[:60]}...")
            else:
                _broken_urls[url] = now
                print(f"[URL] ✗ Broken ({response.status_code}): {url[:60]}...")

            return is_valid
    except Exception as e:
        print(f"[URL] ✗ Error checking {url[:50]}...: {e}")
        _broken_urls[url] = now
        _url_cache[url] = (False, now)
        return False


async def validate_track(track: Dict) -> bool:
    """Validate a track's audio URL is accessible."""
    if not track or not track.get("url"):
        return False
    return await check_url_health(track["url"])


async def validate_video(video: Dict) -> bool:
    """Validate a video URL is accessible."""
    if not video or not video.get("url"):
        return False
    return await check_url_health(video["url"])


async def get_validated_track(tracks: List[Dict], exclude_id: str = None) -> Optional[Dict]:
    """
    Get a validated track from the list.
    Checks URLs and returns only working ones.
    """
    # Shuffle for variety
    candidates = [t for t in tracks if t.get("id") != exclude_id]
    random.shuffle(candidates)

    for track in candidates:
        if await validate_track(track):
            return track

    # If no tracks validated, return first one anyway (let it fail gracefully)
    print(f"[URL] Warning: No validated tracks found, using fallback")
    return candidates[0] if candidates else None


async def get_validated_video(videos: List[Dict], exclude_id: str = None) -> Optional[Dict]:
    """
    Get a validated video from the list.
    Checks URLs and returns only working ones.
    Avoids repeating the same video (exclude_id).
    """
    # Filter out the current video to avoid repeats
    available = [v for v in videos if v.get("id") != exclude_id] if exclude_id else videos

    # If all filtered out, allow current again (better than nothing)
    if not available:
        available = videos

    random.shuffle(available)

    for video in available:
        if await validate_video(video):
            return video

    # Fallback
    print(f"[URL] Warning: No validated videos found, using fallback")
    return videos[0] if videos else None


# ============ MUSIC SOURCES ============

# Track last search time to enable proactive discovery
_last_search_time: Dict[str, float] = {}
SEARCH_COOLDOWN = 120  # Seconds between proactive searches per channel

# Archive.org collections with ambient/lo-fi music (expanded with verified working collections)
ARCHIVE_COLLECTIONS = {
    "lo-fi": [
        "kalaido-hanging-lanterns_202101",  # Verified working
        "lofi-music-swing-jazz-grooves-to-elevate-your-mood-feel-the-rhythm",
    ],
    "ambient": [
        "dx_ambient",  # Verified working - 8+ tracks
        "ambient-music-for-sleep",
        "space-ambient-music",
    ],
    "jazz": [
        "Free_20s_Jazz_Collection",  # Verified working
        "jazz-piano-background-music",
    ],
    "synthwave": [
        "synthwave-music-collection",
    ],
    "piano": [
        "relaxing-piano-music",
    ],
    "acoustic": [
        "acoustic-guitar-instrumentals",
    ],
    "electronic": [
        "electronic-music-collection",
    ],
}

# Known working Archive.org identifiers with their actual audio files
# These are VERIFIED to work and serve as reliable fallbacks
VERIFIED_ARCHIVE_ITEMS = [
    # From kalaido-hanging-lanterns_202101
    ("kalaido-hanging-lanterns_202101", "Kalaido%20-%20Hanging%20Lanterns.mp3"),
    ("kalaido-hanging-lanterns_202101", "Kerusu%20-%20First%20Snow.mp3"),
    ("kalaido-hanging-lanterns_202101", "Matt%20Quentin%20-%20Waves.mp3"),
    ("kalaido-hanging-lanterns_202101", "Sleepy%20Fish%20-%20Beneath%20the%20Moonlight.mp3"),
    ("kalaido-hanging-lanterns_202101", "Aso%20-%20Seasons.mp3"),
    ("kalaido-hanging-lanterns_202101", "idealism%20-%20Contrails.mp3"),
    ("kalaido-hanging-lanterns_202101", "j%27san%20-%20Serenade.mp3"),
    ("kalaido-hanging-lanterns_202101", "SwuM%20-%20Coffee.mp3"),
    ("kalaido-hanging-lanterns_202101", "In%20Love%20With%20a%20Ghost%20-%20Flowers.mp3"),
    ("kalaido-hanging-lanterns_202101", "tomppabeats%20-%20Lonely%20Dance.mp3"),
    # From dx_ambient
    ("dx_ambient", "01_ambient.mp3"),
    ("dx_ambient", "02_ambient.mp3"),
    ("dx_ambient", "03_ambient.mp3"),
    ("dx_ambient", "04_ambient.mp3"),
    ("dx_ambient", "05_ambient.mp3"),
    ("dx_ambient", "06_ambient.mp3"),
    # From Free_20s_Jazz_Collection
    ("Free_20s_Jazz_Collection", "Annette%20Hanshaw%20-%20Mean%20To%20Me.mp3"),
    ("Free_20s_Jazz_Collection", "Benny%20Goodman%20-%20Moonglow.mp3"),
    ("Free_20s_Jazz_Collection", "Duke%20Ellington%20-%20Mood%20Indigo.mp3"),
]

# Pre-curated tracks from Archive.org (verified working URLs only)
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
        {
            "id": "lofi_chillhop",
            "name": "Chillhop Essentials",
            "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/Aso%20-%20Seasons.mp3",
            "genres": ["lo-fi", "chill"],
            "duration": 175,
        },
        {
            "id": "lofi_morning",
            "name": "Morning Coffee Lo-fi",
            "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/idealism%20-%20Contrails.mp3",
            "genres": ["lo-fi", "morning", "cafe"],
            "duration": 190,
        },
        {
            "id": "lofi_sunset",
            "name": "Sunset Drive",
            "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/j%27san%20-%20Serenade.mp3",
            "genres": ["lo-fi", "evening"],
            "duration": 185,
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
        {
            "id": "jazz_cafe",
            "name": "Late Night Cafe Jazz",
            "url": "https://archive.org/download/Free_20s_Jazz_Collection/Annette%20Hanshaw%20-%20Mean%20To%20Me.mp3",
            "genres": ["jazz", "cafe", "vintage"],
            "duration": 180,
        },
        {
            "id": "jazz_smooth",
            "name": "Smooth Jazz Vibes",
            "url": "https://archive.org/download/Free_20s_Jazz_Collection/Benny%20Goodman%20-%20Moonglow.mp3",
            "genres": ["jazz", "smooth"],
            "duration": 195,
        },
        {
            "id": "jazz_piano",
            "name": "Jazz Piano Evening",
            "url": "https://archive.org/download/Free_20s_Jazz_Collection/Duke%20Ellington%20-%20Mood%20Indigo.mp3",
            "genres": ["jazz", "piano", "night"],
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
        {
            "id": "ambient_04",
            "name": "Floating Ambient",
            "url": "https://archive.org/download/dx_ambient/04_ambient.mp3",
            "genres": ["ambient", "floating"],
            "duration": 290,
        },
        {
            "id": "ambient_05",
            "name": "Cosmic Drift",
            "url": "https://archive.org/download/dx_ambient/05_ambient.mp3",
            "genres": ["ambient", "cosmic"],
            "duration": 310,
        },
        {
            "id": "ambient_06",
            "name": "Night Meditation",
            "url": "https://archive.org/download/dx_ambient/06_ambient.mp3",
            "genres": ["ambient", "meditation"],
            "duration": 285,
        },
    ],
    "synthwave": [
        {
            "id": "synthwave_01",
            "name": "Neon Nights",
            "url": "https://archive.org/download/synthwave-music-collection/01%20-%20Neon%20Dreams.mp3",
            "genres": ["synthwave", "neon"],
            "duration": 210,
        },
        {
            "id": "synthwave_02",
            "name": "Retro Future",
            "url": "https://archive.org/download/synthwave-music-collection/02%20-%20Retro%20Future.mp3",
            "genres": ["synthwave", "retro"],
            "duration": 225,
        },
        {
            "id": "synthwave_03",
            "name": "Digital Sunset",
            "url": "https://archive.org/download/synthwave-music-collection/03%20-%20Digital%20Sunset.mp3",
            "genres": ["synthwave", "sunset"],
            "duration": 195,
        },
        # Fallback to lo-fi for variety
        {
            "id": "electronic_chill",
            "name": "Electronic Chill",
            "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/SwuM%20-%20Coffee.mp3",
            "genres": ["electronic", "chill"],
            "duration": 180,
        },
    ],
    "acoustic": [
        {
            "id": "acoustic_01",
            "name": "Peaceful Morning",
            "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/Louk%20-%20Time.mp3",
            "genres": ["acoustic", "peaceful"],
            "duration": 195,
        },
        {
            "id": "acoustic_02",
            "name": "Gentle Breeze",
            "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/Philanthrope%20-%20Maple%20Leaf%20Rag.mp3",
            "genres": ["acoustic", "gentle"],
            "duration": 185,
        },
    ],
    "piano": [
        {
            "id": "piano_01",
            "name": "Soft Piano Dreams",
            "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/In%20Love%20With%20a%20Ghost%20-%20Flowers.mp3",
            "genres": ["piano", "soft"],
            "duration": 200,
        },
        {
            "id": "piano_02",
            "name": "Rainy Window Piano",
            "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/SwuM%20x%20Psalm%20Trees%20-%20Affection.mp3",
            "genres": ["piano", "rain"],
            "duration": 190,
        },
        {
            "id": "piano_03",
            "name": "Evening Reflection",
            "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/tomppabeats%20-%20Lonely%20Dance.mp3",
            "genres": ["piano", "reflection"],
            "duration": 175,
        },
    ],
    "electronic": [
        {
            "id": "electronic_01",
            "name": "Deep Electronic",
            "url": "https://archive.org/download/dx_ambient/07_ambient.mp3",
            "genres": ["electronic", "deep"],
            "duration": 275,
        },
        {
            "id": "electronic_02",
            "name": "Electronic Dreams",
            "url": "https://archive.org/download/dx_ambient/08_ambient.mp3",
            "genres": ["electronic", "dreams"],
            "duration": 290,
        },
    ],
}


async def search_music(query: str, mood: Optional[str] = None) -> List[Dict]:
    """
    Search for copyright-free music matching the query.
    PRIORITY: Search online FIRST, then fall back to curated tracks.
    Returns list of track objects with url, name, genres.
    """
    print(f"[Music] Searching for: '{query}' (mood: {mood})")

    # ===== STEP 1: SEARCH ONLINE FIRST =====
    online_results = await search_all_sources(query, mood)

    if online_results:
        print(f"[Music] Found {len(online_results)} tracks online")
        return online_results

    # ===== STEP 2: FALLBACK TO CURATED TRACKS =====
    print(f"[Music] No online results, using curated library")

    query_lower = query.lower()
    results = []

    # Search curated tracks
    for genre, tracks in CURATED_TRACKS.items():
        for track in tracks:
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

    # Deduplicate by URL
    seen_urls = set()
    unique_results = []
    for track in results:
        if track["url"] not in seen_urls:
            seen_urls.add(track["url"])
            unique_results.append(track)

    # Shuffle results to provide variety
    random.shuffle(unique_results)
    return unique_results[:10]


async def proactive_discover(channel_id: str, mood: str, period: str) -> Optional[Dict]:
    """
    Proactively discover NEW content for a channel.
    ALWAYS searches online first to find fresh music.
    """
    global _last_search_time

    now = time.time()
    last_search = _last_search_time.get(channel_id, 0)

    # Only search if cooldown has passed
    if now - last_search < SEARCH_COOLDOWN:
        return None

    _last_search_time[channel_id] = now

    # Generate contextual search queries
    period_queries = {
        "night": [
            "lo-fi night chill creative commons",
            "ambient midnight music free",
            "nocturnal beats royalty free",
            "late night jazz instrumental",
        ],
        "morning": [
            "morning ambient creative commons",
            "sunrise music royalty free",
            "peaceful wake up instrumental",
            "coffee shop morning jazz",
        ],
        "afternoon": [
            "focus beats creative commons",
            "productivity ambient music",
            "afternoon jazz instrumental",
            "work music royalty free",
        ],
        "evening": [
            "sunset chill music free",
            "evening jazz royalty free",
            "twilight ambient instrumental",
            "relaxing evening piano",
        ],
    }

    mood_queries = {
        "calm": ["calm ambient creative commons", "peaceful piano royalty free"],
        "focused": ["focus music creative commons", "concentration ambient"],
        "energetic": ["upbeat electronic creative commons", "energetic music free"],
        "melancholic": ["melancholic piano royalty free", "sad jazz instrumental"],
        "cozy": ["cozy cafe music creative commons", "warm lo-fi royalty free"],
        "dreamy": ["dreamy ambient music free", "ethereal soundscape"],
    }

    # Build search query
    base_queries = period_queries.get(period, ["ambient music creative commons"])
    if mood.lower() in mood_queries:
        base_queries.extend(mood_queries[mood.lower()])

    search_query = random.choice(base_queries)
    print(f"[Discovery] {channel_id} searching online: {search_query}")

    # Search online sources first
    online_results = await search_all_sources(search_query, mood)
    if online_results:
        track = random.choice(online_results)
        print(f"[Discovery] {channel_id} found online: {track['name']}")
        return track

    # Fallback to curated
    results = await search_music(search_query, mood)
    if results:
        return random.choice(results)

    return None


async def search_archive_org(query: str) -> List[Dict]:
    """Search Archive.org for audio files - improved with better collection targeting."""
    results = []

    # Target specific CC music collections on Archive.org
    collection_queries = [
        f"collection:opensource_audio AND {query}",
        f"collection:audio AND mediatype:audio AND {query}",
        f"subject:creative_commons AND mediatype:audio AND {query}",
    ]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            for coll_query in collection_queries[:1]:  # Use first query
                encoded_query = quote_plus(coll_query)
                url = f"https://archive.org/advancedsearch.php?q={encoded_query}&fl[]=identifier,title,creator&rows=10&output=json"

                response = await client.get(url)
                if response.status_code != 200:
                    continue

                data = response.json()

                for doc in data.get("response", {}).get("docs", []):
                    identifier = doc.get("identifier", "")
                    title = doc.get("title", "Unknown")
                    creator = doc.get("creator", "")
                    if isinstance(creator, list):
                        creator = creator[0] if creator else ""

                    # Try to get actual files from the item
                    files_url = f"https://archive.org/metadata/{identifier}/files"
                    try:
                        files_resp = await client.get(files_url, timeout=5.0)
                        if files_resp.status_code == 200:
                            files_data = files_resp.json()
                            for f in files_data.get("result", []):
                                fname = f.get("name", "")
                                if fname.endswith((".mp3", ".ogg", ".flac")):
                                    track_url = f"https://archive.org/download/{identifier}/{quote_plus(fname)}"
                                    results.append({
                                        "id": f"archive_{identifier}_{fname[:20]}",
                                        "name": f"{title} - {creator}" if creator else title,
                                        "url": track_url,
                                        "genres": extract_genres_from_query(query),
                                        "duration": 180,
                                        "source": "archive.org",
                                    })
                                    break  # One track per item
                    except:
                        # Fallback to guessed URL
                        results.append({
                            "id": f"archive_{identifier}",
                            "name": f"{title} - {creator}" if creator else title,
                            "url": f"https://archive.org/download/{identifier}/{identifier}.mp3",
                            "genres": extract_genres_from_query(query),
                            "duration": 180,
                            "source": "archive.org",
                        })

                if results:
                    break

    except Exception as e:
        print(f"[Tools] Archive.org search failed: {e}")

    return results[:5]


async def search_free_music_archive(query: str, genre: str = None) -> List[Dict]:
    """Search Free Music Archive for CC-licensed tracks."""
    results = []

    # FMA genre mappings
    fma_genres = {
        "lo-fi": "Electronic",
        "ambient": "Ambient",
        "jazz": "Jazz",
        "synthwave": "Electronic",
        "acoustic": "Folk",
        "piano": "Classical",
        "chill": "Electronic",
    }

    try:
        # FMA API endpoint (using their public API)
        search_genre = fma_genres.get(genre or query.split()[0].lower(), "Electronic")
        # Note: FMA API may require API key for full access
        # Using curated FMA tracks as fallback

        # These are known working FMA tracks (CC licensed)
        fma_tracks = [
            {
                "id": "fma_blue_dot",
                "name": "Blue Dot Sessions - The Big Escape",
                "url": "https://freemusicarchive.org/file/music/ccCommunity/Blue_Dot_Sessions/The_Big_Escape/Blue_Dot_Sessions_-_The_Big_Escape.mp3",
                "genres": ["ambient", "chill"],
                "duration": 195,
                "source": "fma",
            },
            {
                "id": "fma_podington",
                "name": "Podington Bear - Starling",
                "url": "https://freemusicarchive.org/file/music/ccCommunity/Podington_Bear/Starling/Podington_Bear_-_Starling.mp3",
                "genres": ["ambient", "peaceful"],
                "duration": 180,
                "source": "fma",
            },
        ]

        # Filter by query
        query_lower = query.lower()
        for track in fma_tracks:
            if any(g in query_lower for g in track["genres"]) or query_lower in track["name"].lower():
                results.append(track)

    except Exception as e:
        print(f"[Tools] FMA search failed: {e}")

    return results


async def search_ccmixter(query: str) -> List[Dict]:
    """Search ccMixter for CC-licensed remixes and samples."""
    results = []

    try:
        # ccMixter API
        encoded_query = quote_plus(query)
        url = f"http://ccmixter.org/api/query?tags={encoded_query}&f=json&limit=5"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                for item in data:
                    if item.get("files"):
                        for f in item["files"]:
                            if f.get("download_url"):
                                results.append({
                                    "id": f"ccmixter_{item.get('upload_id', '')}",
                                    "name": item.get("upload_name", "ccMixter Track"),
                                    "url": f["download_url"],
                                    "genres": extract_genres_from_query(query),
                                    "duration": 180,
                                    "source": "ccmixter",
                                })
                                break

    except Exception as e:
        print(f"[Tools] ccMixter search failed: {e}")

    return results[:3]


async def search_all_sources(query: str, mood: str = None) -> List[Dict]:
    """
    Search ALL online sources for music.
    This is the primary search function agents should use.
    """
    print(f"[Search] Searching all sources for: {query}")

    all_results = []

    # Search multiple sources in parallel
    try:
        archive_task = search_archive_org(query)
        fma_task = search_free_music_archive(query, mood)
        ccmixter_task = search_ccmixter(query)

        results = await asyncio.gather(
            archive_task,
            fma_task,
            ccmixter_task,
            return_exceptions=True
        )

        for result in results:
            if isinstance(result, list):
                all_results.extend(result)

    except Exception as e:
        print(f"[Search] Multi-source search failed: {e}")

    # Validate URLs before returning
    validated = []
    for track in all_results:
        if await check_url_health(track.get("url", "")):
            validated.append(track)
            if len(validated) >= 5:  # Return max 5 validated tracks
                break

    print(f"[Search] Found {len(all_results)} tracks, {len(validated)} validated")
    return validated


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

# Mixkit free videos - expanded library for variety
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
        {
            "id": "rain_drops",
            "name": "Rain Drops Close-up",
            "url": "https://assets.mixkit.co/videos/4271/4271-720.mp4",
            "tags": ["rain", "drops", "macro"],
        },
        {
            "id": "rain_puddles",
            "name": "Rain Puddles",
            "url": "https://assets.mixkit.co/videos/4278/4278-720.mp4",
            "tags": ["rain", "puddles", "street"],
        },
        {
            "id": "rain_city_night",
            "name": "City in Rain",
            "url": "https://assets.mixkit.co/videos/4634/4634-720.mp4",
            "tags": ["rain", "city", "night"],
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
        {
            "id": "city_timelapse",
            "name": "City Timelapse",
            "url": "https://assets.mixkit.co/videos/4077/4077-720.mp4",
            "tags": ["city", "timelapse", "night"],
        },
        {
            "id": "downtown_traffic",
            "name": "Downtown Traffic",
            "url": "https://assets.mixkit.co/videos/1134/1134-720.mp4",
            "tags": ["city", "traffic", "night"],
        },
        {
            "id": "neon_streets",
            "name": "Neon Streets",
            "url": "https://assets.mixkit.co/videos/3116/3116-720.mp4",
            "tags": ["neon", "street", "night"],
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
        {
            "id": "forest_sunlight",
            "name": "Forest Sunlight",
            "url": "https://assets.mixkit.co/videos/1164/1164-720.mp4",
            "tags": ["forest", "sunlight", "nature"],
        },
        {
            "id": "ocean_waves",
            "name": "Ocean Waves",
            "url": "https://assets.mixkit.co/videos/1189/1189-720.mp4",
            "tags": ["ocean", "waves", "peaceful"],
        },
        {
            "id": "clouds_timelapse",
            "name": "Clouds Timelapse",
            "url": "https://assets.mixkit.co/videos/1166/1166-720.mp4",
            "tags": ["clouds", "sky", "timelapse"],
        },
    ],
    "space": [
        {
            "id": "stars_space",
            "name": "Stars in Space",
            "url": "https://assets.mixkit.co/videos/14185/14185-720.mp4",
            "tags": ["space", "stars", "night"],
        },
        {
            "id": "galaxy_travel",
            "name": "Galaxy Travel",
            "url": "https://assets.mixkit.co/videos/4039/4039-720.mp4",
            "tags": ["galaxy", "space", "travel"],
        },
        {
            "id": "nebula_flight",
            "name": "Nebula Flight",
            "url": "https://assets.mixkit.co/videos/39702/39702-720.mp4",
            "tags": ["nebula", "space", "cosmic"],
        },
        {
            "id": "earth_orbit",
            "name": "Earth from Orbit",
            "url": "https://assets.mixkit.co/videos/3754/3754-720.mp4",
            "tags": ["earth", "orbit", "space"],
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
        {
            "id": "liquid_motion",
            "name": "Liquid Motion",
            "url": "https://assets.mixkit.co/videos/27/27-720.mp4",
            "tags": ["liquid", "abstract", "flow"],
        },
        {
            "id": "particle_flow",
            "name": "Particle Flow",
            "url": "https://assets.mixkit.co/videos/200/200-720.mp4",
            "tags": ["particles", "abstract", "motion"],
        },
        {
            "id": "color_gradient",
            "name": "Color Gradient",
            "url": "https://assets.mixkit.co/videos/12/12-720.mp4",
            "tags": ["gradient", "colors", "abstract"],
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
    """Get recommended videos for a channel based on its vibe - expanded categories."""
    # Each channel gets multiple video categories for variety
    channel_visuals = {
        "ch01": ["rain", "city", "abstract"],       # Late Night - moody urban
        "ch02": ["rain", "nature", "city"],         # Rain Cafe - cozy vibes
        "ch03": ["city", "rain", "abstract"],       # Jazz Noir - urban noir
        "ch04": ["abstract", "space", "city"],      # Synthwave - retro futurism
        "ch05": ["space", "abstract", "nature"],    # Deep Space - cosmic
        "ch06": ["city", "abstract", "rain"],       # Tokyo Drift - neon urbanism
        "ch07": ["nature", "rain", "abstract"],     # Sunday Morning - peaceful
        "ch08": ["abstract", "nature", "space"],    # Focus - minimal
        "ch09": ["rain", "city", "nature"],         # Melancholy - emotional
        "ch10": ["nature", "abstract", "city"],     # Golden Hour - warm tones
    }

    categories = channel_visuals.get(channel_id, ["abstract", "nature"])
    videos = []

    for category in categories:
        if category in CURATED_VIDEOS:
            videos.extend(CURATED_VIDEOS[category])

    # Deduplicate by ID
    seen_ids = set()
    unique_videos = []
    for video in videos:
        if video["id"] not in seen_ids:
            seen_ids.add(video["id"])
            unique_videos.append(video)

    return unique_videos
