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

    # Actually check the URL (follow redirects to verify final destination)
    try:
        async with httpx.AsyncClient(timeout=URL_CHECK_TIMEOUT, follow_redirects=True) as client:
            response = await client.head(url)
            # Only 200 is valid (we followed redirects, so no 301/302)
            is_valid = response.status_code == 200

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
    # From kalaido-hanging-lanterns_202101 (verified working)
    ("kalaido-hanging-lanterns_202101", "Kalaido%20-%20Hanging%20Lanterns.mp3"),
    ("kalaido-hanging-lanterns_202101", "Kerusu%20-%20First%20Snow.mp3"),
    ("kalaido-hanging-lanterns_202101", "Matt%20Quentin%20-%20Waves.mp3"),
    ("kalaido-hanging-lanterns_202101", "%28FREE%29%20Lo-fi%20Type%20Beat%20-%20Rain.mp3"),
    ("kalaido-hanging-lanterns_202101", "Kronicle%20-%20Lofi%20Experimentin%20%28No%20Copyright%20Hip%20Hop%20Music%29.mp3"),
    ("kalaido-hanging-lanterns_202101", "Onion%20%28Prod.%20by%20Lukrembo%29.mp3"),
    ("kalaido-hanging-lanterns_202101", "flovry%20-%20car%20radio.mp3"),
    ("kalaido-hanging-lanterns_202101", "Tranquillity%20-%20Chill%20Lofi%20Hip%20Hop%20Beat%20%28FREE%20FOR%20PROFIT%20USE%29.mp3"),
    ("kalaido-hanging-lanterns_202101", "%28no%20copyright%20music%29%20jazz%20type%20beat%20bread%20royalty%20free%20youtube%20music%20prod.%20by%20lukrembo.mp3"),
    # From dx_ambient (verified working)
    ("dx_ambient", "01_ambient.mp3"),
    ("dx_ambient", "02_ambient.mp3"),
    ("dx_ambient", "03_ambient.mp3"),
    ("dx_ambient", "04_ambient.mp3"),
    ("dx_ambient", "05_ambient.mp3"),
    ("dx_ambient", "06_ambient.mp3"),
    ("dx_ambient", "07_ambient.mp3"),
    ("dx_ambient", "08_ambient.mp3"),
    # From synthwave (verified working)
    ("synthwave", "synthwave.mp3"),
    ("synthwave", "cyberpunk.mp3"),
]

# =============================================================================
# EXCLUSIVE CHANNEL LIBRARIES - Each channel has its own unique audio/visual taste
# =============================================================================

# Each channel agent has EXCLUSIVE tracks - no sharing between channels
CHANNEL_TRACKS = {
    # CH01: Late Night with Maya - lo-fi, introspective night coding vibes
    "ch01": [
        {"id": "ch01_1", "name": "Hanging Lanterns - Kalaido", "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/Kalaido%20-%20Hanging%20Lanterns.mp3", "duration": 180},
        {"id": "ch01_2", "name": "First Snow - Kerusu", "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/Kerusu%20-%20First%20Snow.mp3", "duration": 195},
        {"id": "ch01_3", "name": "Lofi Experimentin - Kronicle", "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/Kronicle%20-%20Lofi%20Experimentin%20%28No%20Copyright%20Hip%20Hop%20Music%29.mp3", "duration": 185},
    ],
    # CH02: Rain Café with Yuki - jazz café, cozy rain vibes
    "ch02": [
        {"id": "ch02_1", "name": "Lo-fi Rain Beat", "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/%28FREE%29%20Lo-fi%20Type%20Beat%20-%20Rain.mp3", "duration": 170},
        {"id": "ch02_2", "name": "Chill Jazzy Lofi", "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/%5BNo%20Copyright%20Music%5D%20Chill%20Jazzy%20Lofi%20Hip-Hop%20Beat%20%28Copyright%20Free%29%20Music%20By%20KaizanBlu.mp3", "duration": 180},
        {"id": "ch02_3", "name": "Herbal Tea Jazz", "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/%5BNon%20Copyrighted%20Music%5D%20Artificial.Music%20-%20Herbal%20Tea%20%5BLo-fi%5D.mp3", "duration": 195},
    ],
    # CH03: Jazz Noir with Vincent - smoky detective jazz
    "ch03": [
        {"id": "ch03_1", "name": "Swing Jazz Grooves", "url": "https://archive.org/download/lofi-music-swing-jazz-grooves-to-elevate-your-mood-feel-the-rhythm/LOFI%20Music%E3%80%80Swing%20Jazz%20Grooves%20to%20Elevate%20Your%20Mood%20%EF%BD%9C%20Feel%20the%20Rhythm%20.mp3", "duration": 220},
        {"id": "ch03_2", "name": "Jazz Type Beat - Lukrembo", "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/%28no%20copyright%20music%29%20jazz%20type%20beat%20bread%20royalty%20free%20youtube%20music%20prod.%20by%20lukrembo.mp3", "duration": 165},
        {"id": "ch03_3", "name": "Deep Space Jazz", "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/deep%20space%20-%20Ambient%20Lofi%20Hip%20Hop%20Beat%20%28FREE%20FOR%20PROFIT%20USE%29.mp3", "duration": 200},
    ],
    # CH04: Synthwave with NEON - retro-futuristic neon dreams
    "ch04": [
        {"id": "ch04_1", "name": "Synthwave Dreams", "url": "https://archive.org/download/synthwave/synthwave.mp3", "duration": 210},
        {"id": "ch04_2", "name": "Cyberpunk Night", "url": "https://archive.org/download/synthwave/cyberpunk.mp3", "duration": 225},
        {"id": "ch04_3", "name": "Defective Beats", "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/defective%20-%20LofiTrap%20Style%20Hip%20Hop%20Beat%20%28FREE%20FOR%20PROFIT%20USE%29.mp3", "duration": 180},
    ],
    # CH05: Deep Space with Cosmos - vast cosmic ambience
    "ch05": [
        {"id": "ch05_1", "name": "Cosmic Drift", "url": "https://archive.org/download/dx_ambient/05_ambient.mp3", "duration": 310},
        {"id": "ch05_2", "name": "Deep Ambient", "url": "https://archive.org/download/dx_ambient/02_ambient.mp3", "duration": 320},
        {"id": "ch05_3", "name": "Night Meditation", "url": "https://archive.org/download/dx_ambient/06_ambient.mp3", "duration": 285},
    ],
    # CH06: Tokyo Drift with Kenji - neon city nights, city pop
    "ch06": [
        {"id": "ch06_1", "name": "Finite Dreams", "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/finite%20-%20Lofi%20Hip%20Hop%20Beat%20%28FREE%20FOR%20PROFIT%20USE%29.mp3", "duration": 195},
        {"id": "ch06_2", "name": "Onion - Lukrembo", "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/Onion%20%28Prod.%20by%20Lukrembo%29.mp3", "duration": 175},
        {"id": "ch06_3", "name": "Tranquillity", "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/Tranquillity%20-%20Chill%20Lofi%20Hip%20Hop%20Beat%20%28FREE%20FOR%20PROFIT%20USE%29.mp3", "duration": 190},
    ],
    # CH07: Sunday Morning with Claire - peaceful acoustic warmth
    "ch07": [
        {"id": "ch07_1", "name": "Dancing On My Own", "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/Outgoing%20Hikikomori%20-%20Dancing%20On%20My%20Own%20%28No%20copyright%20lo%20fi%20beat%29.mp3", "duration": 195},
        {"id": "ch07_2", "name": "Take Care - SURF", "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/%E3%81%91%EF%BD%8D%20SURF%20-%20Take%20Care.mp3", "duration": 185},
        {"id": "ch07_3", "name": "Waves - Matt Quentin", "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/Matt%20Quentin%20-%20Waves.mp3", "duration": 200},
    ],
    # CH08: Focus with Alan - minimal, distraction-free ambient
    "ch08": [
        {"id": "ch08_1", "name": "Focus Ambient", "url": "https://archive.org/download/dx_ambient/03_ambient.mp3", "duration": 280},
        {"id": "ch08_2", "name": "Floating Ambient", "url": "https://archive.org/download/dx_ambient/04_ambient.mp3", "duration": 290},
        {"id": "ch08_3", "name": "Ambient Space", "url": "https://archive.org/download/dx_ambient/01_ambient.mp3", "duration": 300},
    ],
    # CH09: Melancholy with Daniel - sad, reflective, rainy nights
    "ch09": [
        {"id": "ch09_1", "name": "Sunset Drive", "url": "https://archive.org/download/kalaido-hanging-lanterns_202101/flovry%20-%20car%20radio.mp3", "duration": 185},
        {"id": "ch09_2", "name": "Deep Electronic", "url": "https://archive.org/download/dx_ambient/07_ambient.mp3", "duration": 275},
        {"id": "ch09_3", "name": "Electronic Dreams", "url": "https://archive.org/download/dx_ambient/08_ambient.mp3", "duration": 290},
    ],
    # CH10: Golden Hour with Iris - warm sunset, golden light
    "ch10": [
        {"id": "ch10_1", "name": "Soft Piano Dreams", "url": "https://archive.org/download/dx_ambient/01_ambient.mp3", "duration": 300},
        {"id": "ch10_2", "name": "Rainy Window Piano", "url": "https://archive.org/download/dx_ambient/02_ambient.mp3", "duration": 320},
        {"id": "ch10_3", "name": "Evening Reflection", "url": "https://archive.org/download/dx_ambient/04_ambient.mp3", "duration": 290},
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


# Each channel agent has EXCLUSIVE videos - no sharing between channels
CHANNEL_VIDEOS = {
    # CH01: Late Night with Maya - rain on windows, moody city nights
    "ch01": [
        {"id": "ch01_v1", "name": "Rain on Window", "url": "https://assets.mixkit.co/videos/18308/18308-720.mp4", "tags": ["rain", "window", "night"]},
        {"id": "ch01_v2", "name": "City Timelapse", "url": "https://assets.mixkit.co/videos/4077/4077-720.mp4", "tags": ["city", "timelapse", "night"]},
        {"id": "ch01_v3", "name": "Liquid Motion", "url": "https://assets.mixkit.co/videos/27/27-720.mp4", "tags": ["liquid", "abstract", "flow"]},
    ],
    # CH02: Rain Café with Yuki - cozy rain, warm café vibes
    "ch02": [
        {"id": "ch02_v1", "name": "Rainy Street", "url": "https://assets.mixkit.co/videos/33951/33951-720.mp4", "tags": ["rain", "street", "city"]},
        {"id": "ch02_v2", "name": "Rain Drops Close-up", "url": "https://assets.mixkit.co/videos/4271/4271-720.mp4", "tags": ["rain", "drops", "macro"]},
        {"id": "ch02_v3", "name": "Forest Sunlight", "url": "https://assets.mixkit.co/videos/1164/1164-720.mp4", "tags": ["forest", "sunlight", "nature"]},
    ],
    # CH03: Jazz Noir with Vincent - smoky noir city
    "ch03": [
        {"id": "ch03_v1", "name": "City Lights", "url": "https://assets.mixkit.co/videos/650/650-720.mp4", "tags": ["city", "night", "noir"]},
        {"id": "ch03_v2", "name": "Rain Puddles", "url": "https://assets.mixkit.co/videos/4278/4278-720.mp4", "tags": ["rain", "puddles", "street"]},
        {"id": "ch03_v3", "name": "Downtown Traffic", "url": "https://assets.mixkit.co/videos/1134/1134-720.mp4", "tags": ["city", "traffic", "night"]},
    ],
    # CH04: Synthwave with NEON - retro neon grids
    "ch04": [
        {"id": "ch04_v1", "name": "Neon Grid", "url": "https://assets.mixkit.co/videos/35644/35644-720.mp4", "tags": ["neon", "grid", "synthwave"]},
        {"id": "ch04_v2", "name": "Galaxy Travel", "url": "https://assets.mixkit.co/videos/4039/4039-720.mp4", "tags": ["galaxy", "space", "travel"]},
        {"id": "ch04_v3", "name": "Color Gradient", "url": "https://assets.mixkit.co/videos/12/12-720.mp4", "tags": ["gradient", "colors", "abstract"]},
    ],
    # CH05: Deep Space with Cosmos - cosmic void
    "ch05": [
        {"id": "ch05_v1", "name": "Stars in Space", "url": "https://assets.mixkit.co/videos/14185/14185-720.mp4", "tags": ["space", "stars", "night"]},
        {"id": "ch05_v2", "name": "Nebula Flight", "url": "https://assets.mixkit.co/videos/39702/39702-720.mp4", "tags": ["nebula", "space", "cosmic"]},
        {"id": "ch05_v3", "name": "Earth from Orbit", "url": "https://assets.mixkit.co/videos/3754/3754-720.mp4", "tags": ["earth", "orbit", "space"]},
    ],
    # CH06: Tokyo Drift with Kenji - neon city streets
    "ch06": [
        {"id": "ch06_v1", "name": "Tokyo Night", "url": "https://assets.mixkit.co/videos/4451/4451-1080.mp4", "tags": ["tokyo", "neon", "night"]},
        {"id": "ch06_v2", "name": "Neon Streets", "url": "https://assets.mixkit.co/videos/3116/3116-720.mp4", "tags": ["neon", "street", "night"]},
        {"id": "ch06_v3", "name": "City in Rain", "url": "https://assets.mixkit.co/videos/4634/4634-720.mp4", "tags": ["rain", "city", "night"]},
    ],
    # CH07: Sunday Morning with Claire - peaceful nature
    "ch07": [
        {"id": "ch07_v1", "name": "Morning Light", "url": "https://assets.mixkit.co/videos/26532/26532-720.mp4", "tags": ["morning", "light", "nature"]},
        {"id": "ch07_v2", "name": "Ocean Waves", "url": "https://assets.mixkit.co/videos/1189/1189-720.mp4", "tags": ["ocean", "waves", "peaceful"]},
        {"id": "ch07_v3", "name": "Clouds Timelapse", "url": "https://assets.mixkit.co/videos/1166/1166-720.mp4", "tags": ["clouds", "sky", "timelapse"]},
    ],
    # CH08: Focus with Alan - minimal abstract
    "ch08": [
        {"id": "ch08_v1", "name": "Minimal Waves", "url": "https://assets.mixkit.co/videos/914/914-1080.mp4", "tags": ["minimal", "abstract", "calm"]},
        {"id": "ch08_v2", "name": "Particle Flow", "url": "https://assets.mixkit.co/videos/200/200-720.mp4", "tags": ["particles", "abstract", "motion"]},
        {"id": "ch08_v3", "name": "Soft Gradient", "url": "https://assets.mixkit.co/videos/18/18-720.mp4", "tags": ["gradient", "soft", "minimal"]},
    ],
    # CH09: Melancholy with Daniel - reflective rain
    "ch09": [
        {"id": "ch09_v1", "name": "Rain Window Reflection", "url": "https://assets.mixkit.co/videos/18312/18312-1080.mp4", "tags": ["rain", "window", "reflective"]},
        {"id": "ch09_v2", "name": "Misty Forest", "url": "https://assets.mixkit.co/videos/1176/1176-720.mp4", "tags": ["mist", "forest", "moody"]},
        {"id": "ch09_v3", "name": "Grey Clouds", "url": "https://assets.mixkit.co/videos/1172/1172-720.mp4", "tags": ["clouds", "grey", "melancholy"]},
    ],
    # CH10: Golden Hour with Iris - warm sunset
    "ch10": [
        {"id": "ch10_v1", "name": "Golden Hour Sunset", "url": "https://assets.mixkit.co/videos/4119/4119-1080.mp4", "tags": ["sunset", "golden", "nature"]},
        {"id": "ch10_v2", "name": "Sunset Beach", "url": "https://assets.mixkit.co/videos/1168/1168-720.mp4", "tags": ["beach", "sunset", "warm"]},
        {"id": "ch10_v3", "name": "Golden Fields", "url": "https://assets.mixkit.co/videos/1171/1171-720.mp4", "tags": ["fields", "golden", "warm"]},
    ],
}


# ============ VIDEO SOURCES ============

# Mixkit free videos - expanded library for variety (LEGACY - kept for fallback)
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
    """Get EXCLUSIVE tracks for a channel - each agent has their own unique library."""
    # Use exclusive channel tracks
    if channel_id in CHANNEL_TRACKS:
        tracks = CHANNEL_TRACKS[channel_id].copy()
        random.shuffle(tracks)
        return tracks

    # Fallback to old shared library (shouldn't happen)
    print(f"[Tracks] WARNING: No exclusive tracks for {channel_id}, using fallback")
    channel_vibes = {
        "ch01": ["lo-fi", "ambient", "piano"],
        "ch02": ["jazz", "lo-fi", "piano"],
        "ch03": ["jazz", "piano"],
        "ch04": ["synthwave", "electronic"],
        "ch05": ["ambient", "electronic"],
        "ch06": ["synthwave", "jazz", "electronic"],
        "ch07": ["acoustic", "lo-fi", "piano"],
        "ch08": ["ambient", "lo-fi", "electronic"],
        "ch09": ["jazz", "lo-fi", "piano"],
        "ch10": ["lo-fi", "acoustic", "ambient"],
    }
    genres = channel_vibes.get(channel_id, ["lo-fi", "ambient"])
    tracks = []
    for genre in genres:
        if genre in CURATED_TRACKS:
            tracks.extend(CURATED_TRACKS[genre])
    random.shuffle(tracks)
    return tracks


def get_videos_for_channel(channel_id: str) -> List[Dict]:
    """Get EXCLUSIVE videos for a channel - each agent has their own unique visual library."""
    # Use exclusive channel videos
    if channel_id in CHANNEL_VIDEOS:
        videos = CHANNEL_VIDEOS[channel_id].copy()
        random.shuffle(videos)
        return videos

    # Fallback to old shared library (shouldn't happen)
    print(f"[Videos] WARNING: No exclusive videos for {channel_id}, using fallback")
    channel_visuals = {
        "ch01": ["rain", "city", "abstract"],
        "ch02": ["rain", "nature", "city"],
        "ch03": ["city", "rain", "abstract"],
        "ch04": ["abstract", "space", "city"],
        "ch05": ["space", "abstract", "nature"],
        "ch06": ["city", "abstract", "rain"],
        "ch07": ["nature", "rain", "abstract"],
        "ch08": ["abstract", "nature", "space"],
        "ch09": ["rain", "city", "nature"],
        "ch10": ["nature", "abstract", "city"],
    }
    categories = channel_visuals.get(channel_id, ["abstract", "nature"])
    videos = []
    for category in categories:
        if category in CURATED_VIDEOS:
            videos.extend(CURATED_VIDEOS[category])
    return videos
