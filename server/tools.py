"""
Content Discovery Tools for mood42 Agents
Search for copyright-free music and videos
PROACTIVE discovery - agents actively search for new content
WITH URL VALIDATION - verify content is accessible before using
VIDEO DISCOVERY - agents search Archive.org and download to R2
"""

import httpx
import asyncio
import random
import re
import time
import json
import os
from typing import List, Dict, Optional, Tuple
from urllib.parse import quote_plus, quote
from pathlib import Path


# ============ PERSISTENCE (SQLite) ============
# Store all media in SQLite database - the source of truth

import sqlite3

MEDIA_DB_FILE = Path(__file__).parent / "media.db"

def _init_db():
    """Initialize the media database."""
    conn = sqlite3.connect(str(MEDIA_DB_FILE))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            channel_id TEXT NOT NULL,
            name TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            tags TEXT,
            attribution TEXT,
            source TEXT,
            source_url TEXT,
            added_at INTEGER,
            is_base INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tracks (
            id TEXT PRIMARY KEY,
            channel_id TEXT NOT NULL,
            name TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            duration INTEGER,
            tags TEXT,
            attribution TEXT,
            source TEXT,
            added_at INTEGER,
            is_base INTEGER DEFAULT 0
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_videos_channel ON videos(channel_id)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_tracks_channel ON tracks(channel_id)")
    conn.commit()
    conn.close()
    print(f"[DB] Initialized media database at {MEDIA_DB_FILE}")

# Initialize on module load
_init_db()

def load_discovered_media() -> Dict:
    """Load discovered (non-base) media from database."""
    conn = sqlite3.connect(str(MEDIA_DB_FILE))
    conn.row_factory = sqlite3.Row

    videos = {}
    tracks = {}

    # Load discovered videos
    for row in conn.execute("SELECT * FROM videos WHERE is_base = 0"):
        ch_id = row["channel_id"]
        if ch_id not in videos:
            videos[ch_id] = []
        videos[ch_id].append({
            "id": row["id"],
            "name": row["name"],
            "url": row["url"],
            "tags": json.loads(row["tags"]) if row["tags"] else [],
            "attribution": row["attribution"],
            "source": row["source"],
            "source_url": row["source_url"],
            "added_at": row["added_at"],
            "_discovered": True,
            "_verified": True,
        })

    # Load discovered tracks
    for row in conn.execute("SELECT * FROM tracks WHERE is_base = 0"):
        ch_id = row["channel_id"]
        if ch_id not in tracks:
            tracks[ch_id] = []
        tracks[ch_id].append({
            "id": row["id"],
            "name": row["name"],
            "url": row["url"],
            "duration": row["duration"],
            "tags": json.loads(row["tags"]) if row["tags"] else [],
            "attribution": row["attribution"],
            "source": row["source"],
            "added_at": row["added_at"],
            "_discovered": True,
            "_verified": True,
        })

    conn.close()

    total_v = sum(len(v) for v in videos.values())
    total_t = sum(len(t) for t in tracks.values())
    if total_v > 0 or total_t > 0:
        print(f"[DB] Loaded {total_v} discovered videos, {total_t} discovered tracks")

    return {"videos": videos, "tracks": tracks}

def save_discovered_media(videos: Dict, tracks: Dict):
    """Save discovered media to database."""
    conn = sqlite3.connect(str(MEDIA_DB_FILE))

    saved_v = 0
    saved_t = 0

    # Save discovered videos
    for ch_id, ch_videos in videos.items():
        for v in ch_videos:
            if v.get("_discovered") or v.get("added_at"):
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO videos
                        (id, channel_id, name, url, tags, attribution, source, source_url, added_at, is_base)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """, (
                        v.get("id", f"{ch_id}_v_{int(time.time())}"),
                        ch_id,
                        v.get("name", "Unknown"),
                        v.get("url"),
                        json.dumps(v.get("tags", [])),
                        v.get("attribution"),
                        v.get("source"),
                        v.get("source_url"),
                        v.get("added_at", int(time.time())),
                    ))
                    saved_v += 1
                except sqlite3.IntegrityError:
                    pass  # URL already exists

    # Save discovered tracks
    for ch_id, ch_tracks in tracks.items():
        for t in ch_tracks:
            if t.get("_discovered") or t.get("added_at"):
                try:
                    conn.execute("""
                        INSERT OR IGNORE INTO tracks
                        (id, channel_id, name, url, duration, tags, attribution, source, added_at, is_base)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
                    """, (
                        t.get("id", f"{ch_id}_t_{int(time.time())}"),
                        ch_id,
                        t.get("name", "Unknown"),
                        t.get("url"),
                        t.get("duration", 180),
                        json.dumps(t.get("tags", [])),
                        t.get("attribution"),
                        t.get("source"),
                        t.get("added_at", int(time.time())),
                    ))
                    saved_t += 1
                except sqlite3.IntegrityError:
                    pass  # URL already exists

    conn.commit()
    conn.close()

    if saved_v > 0 or saved_t > 0:
        print(f"[DB] Saved {saved_v} videos, {saved_t} tracks")
        # Verify counts only went up
        _verify_counts_increased()


# ============ COUNT MONITORING ============
# Track historical counts to ensure they only go UP

_last_known_counts = {
    "videos": 0,
    "tracks": 0,
}

def _verify_counts_increased():
    """Verify that media counts only increase, never decrease."""
    global _last_known_counts

    conn = sqlite3.connect(str(MEDIA_DB_FILE))
    current_videos = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
    current_tracks = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]
    conn.close()

    # Check for decreases (data loss)
    if _last_known_counts["videos"] > 0 and current_videos < _last_known_counts["videos"]:
        print(f"[ALERT] VIDEO COUNT DECREASED: {_last_known_counts['videos']} -> {current_videos}")

    if _last_known_counts["tracks"] > 0 and current_tracks < _last_known_counts["tracks"]:
        print(f"[ALERT] TRACK COUNT DECREASED: {_last_known_counts['tracks']} -> {current_tracks}")

    # Update last known counts
    _last_known_counts["videos"] = current_videos
    _last_known_counts["tracks"] = current_tracks


def get_db_stats() -> Dict:
    """Get database statistics for ops dashboard."""
    conn = sqlite3.connect(str(MEDIA_DB_FILE))

    total_videos = conn.execute("SELECT COUNT(*) FROM videos").fetchone()[0]
    total_tracks = conn.execute("SELECT COUNT(*) FROM tracks").fetchone()[0]

    stats = {
        "total_videos": total_videos,
        "total_tracks": total_tracks,
        "discovered_videos": conn.execute("SELECT COUNT(*) FROM videos WHERE is_base = 0").fetchone()[0],
        "discovered_tracks": conn.execute("SELECT COUNT(*) FROM tracks WHERE is_base = 0").fetchone()[0],
        "videos_by_channel": {},
        "tracks_by_channel": {},
        "health": {
            "counts_verified": True,
            "last_video_count": _last_known_counts.get("videos", 0),
            "last_track_count": _last_known_counts.get("tracks", 0),
        }
    }

    # Update monitoring
    _last_known_counts["videos"] = total_videos
    _last_known_counts["tracks"] = total_tracks

    for row in conn.execute("SELECT channel_id, COUNT(*) as cnt FROM videos GROUP BY channel_id"):
        stats["videos_by_channel"][row[0]] = row[1]

    for row in conn.execute("SELECT channel_id, COUNT(*) as cnt FROM tracks GROUP BY channel_id"):
        stats["tracks_by_channel"][row[0]] = row[1]

    conn.close()
    return stats


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

# ============ VIDEO DISCOVERY ============
from server.r2 import upload_to_r2, get_public_url, check_exists, is_configured as r2_is_configured
import os

# Pexels API for video search
PEXELS_API_KEY = os.environ.get("PEXELS_API_KEY", "")

# Archive.org collections for video discovery
ARCHIVE_VIDEO_COLLECTIONS = [
    "prelinger",  # Prelinger Archives - historical/artistic films
    "opensource_movies",  # Open source movies
    "stock_footage",  # Stock footage
]

# Taste to search query mapping for video discovery
# Biased towards humans, cities, cinematic shots - more interesting visuals
TASTE_TO_VIDEO_QUERY = {
    "lo-fi": ["people city night", "pedestrians urban street", "woman walking city", "man coffee shop window"],
    "ambient": ["people watching sunset", "silhouette person mountain", "human meditation nature", "person slow motion"],
    "jazz": ["people city noir", "couple night club", "man smoking bar", "woman vintage cafe"],
    "synthwave": ["people neon city", "cyberpunk street crowd", "urban night pedestrians", "city lights people"],
    "space": ["astronaut cinematic", "person stars night", "human silhouette cosmos", "observatory night"],
    "nature": ["person forest walk", "woman flowers garden", "human sunrise beach", "people ocean contemplation"],
    "minimal": ["person minimal space", "human geometric architecture", "silhouette clean lines", "person zen garden"],
    "melancholic": ["person rain city", "lonely figure fog", "human empty street", "woman window rain"],
    "warm": ["people golden hour", "couple sunset beach", "family warm light", "person autumn park"],
    "cozy": ["person coffee cafe", "woman reading fireplace", "man rain window", "couple bookstore"],
}


async def search_video_archive(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search Archive.org for videos matching query.
    Returns list of video objects with download URLs.
    """
    results = []

    try:
        # Search across collections
        search_query = f"({query}) AND mediatype:movies"
        encoded_query = quote_plus(search_query)
        url = f"https://archive.org/advancedsearch.php?q={encoded_query}&fl=identifier,title,description&rows={max_results * 2}&output=json"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            if response.status_code != 200:
                return results

            data = response.json()
            docs = data.get("response", {}).get("docs", [])

            for doc in docs[:max_results * 2]:
                identifier = doc.get("identifier", "")
                title = doc.get("title", "Unknown")

                # Get actual video files from this item
                files_url = f"https://archive.org/metadata/{identifier}/files"
                try:
                    files_resp = await client.get(files_url, timeout=5.0)
                    if files_resp.status_code == 200:
                        files_data = files_resp.json()
                        for f in files_data.get("result", []):
                            fname = f.get("name", "")
                            size = int(f.get("size", 0))

                            # Only MP4 files, reasonable size (1MB - 100MB)
                            if fname.endswith(".mp4") and 1_000_000 < size < 100_000_000:
                                video_url = f"https://archive.org/download/{identifier}/{quote(fname)}"
                                results.append({
                                    "id": f"archive_{identifier}_{fname[:20]}",
                                    "name": title[:50],
                                    "filename": fname,
                                    "url": video_url,
                                    "size_mb": size // 1_000_000,
                                    "source": "archive.org",
                                    "identifier": identifier,
                                })
                                if len(results) >= max_results:
                                    return results
                                break  # One video per item
                except Exception:
                    continue

    except Exception as e:
        print(f"[Video Search] Archive.org search failed: {e}")

    return results


async def search_video_pexels(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search Pexels API for videos matching query.
    Requires PEXELS_API_KEY environment variable.
    Returns list of video objects with download URLs.
    """
    if not PEXELS_API_KEY:
        return []

    results = []
    try:
        headers = {"Authorization": PEXELS_API_KEY}
        encoded_query = quote_plus(query)
        url = f"https://api.pexels.com/videos/search?query={encoded_query}&per_page={max_results}&orientation=landscape"

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code != 200:
                print(f"[Video Search] Pexels API error: {response.status_code}")
                return results

            data = response.json()
            videos = data.get("videos", [])

            for video in videos:
                video_id = video.get("id", "")
                # Get HD or SD video file
                video_files = video.get("video_files", [])
                # Prefer HD quality, reasonable file size
                best_file = None
                for vf in video_files:
                    quality = vf.get("quality", "")
                    width = vf.get("width", 0)
                    if quality in ["hd", "sd"] and 720 <= width <= 1920:
                        best_file = vf
                        break

                if not best_file and video_files:
                    best_file = video_files[0]

                if best_file:
                    results.append({
                        "id": f"pexels_{video_id}",
                        "name": video.get("user", {}).get("name", "Pexels Video")[:50],
                        "filename": f"pexels_{video_id}.mp4",
                        "url": best_file.get("link", ""),
                        "size_mb": (best_file.get("size", 0) or 0) // 1_000_000,
                        "source": "pexels",
                        "identifier": str(video_id),
                        "attribution": f"Video by {video.get('user', {}).get('name', 'Unknown')} on Pexels",
                    })

                if len(results) >= max_results:
                    break

    except Exception as e:
        print(f"[Video Search] Pexels search failed: {e}")

    return results


async def search_videos_all_sources(query: str, max_results: int = 5) -> List[Dict]:
    """
    Search all video sources (Pexels + Archive.org).
    Returns combined results, Pexels first if available.
    """
    results = []

    # Try Pexels first (higher quality, CC0 licensed)
    if PEXELS_API_KEY:
        pexels_results = await search_video_pexels(query, max_results=3)
        results.extend(pexels_results)
        if results:
            print(f"[Video Search] Found {len(results)} from Pexels")

    # Fill remaining with Archive.org
    remaining = max_results - len(results)
    if remaining > 0:
        archive_results = await search_video_archive(query, max_results=remaining)
        results.extend(archive_results)

    return results[:max_results]


async def download_and_upload_audio_to_r2(track: Dict, channel_id: str) -> Optional[Dict]:
    """
    Download audio from source and upload to R2.
    Returns dict with R2 URL and metadata if successful.
    """
    if not track or not track.get("url"):
        return None

    if not r2_is_configured():
        print("[Audio] R2 not configured - skipping upload")
        return None

    source_url = track["url"]
    track_name = track.get("name", "unknown")
    source = track.get("source", "unknown")
    duration = track.get("duration", 180)

    # Skip if already an R2 URL
    if "r2.dev" in source_url:
        return track

    # Create clean filename
    clean_name = re.sub(r'[^a-z0-9]', '_', track_name.lower())[:40]
    clean_name = re.sub(r'_+', '_', clean_name).strip('_')
    filename = f"{channel_id}_{clean_name}_{int(time.time())}.mp3"
    r2_key = f"audio/{filename}"

    # Check if already in R2
    if check_exists(r2_key):
        print(f"[Audio] Already in R2: {filename}")
        return {
            "url": get_public_url(r2_key),
            "name": track_name,
            "duration": duration,
            "source": source,
            "source_url": source_url,
            "_verified": True,
        }

    try:
        # Download audio
        print(f"[Audio] Downloading: {track_name[:40]}...")
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            response = await client.get(source_url)

            if response.status_code != 200:
                print(f"[Audio] Download failed: HTTP {response.status_code}")
                return None

            content = response.content
            content_type = response.headers.get("content-type", "audio/mpeg")

            # Validate it's actually audio (at least 50KB)
            if len(content) < 50_000:
                print(f"[Audio] File too small: {len(content)} bytes")
                return None

        # Upload to R2
        metadata = {
            "source": source,
            "source_url": source_url[:256],
            "original_name": track_name[:128],
            "channel": channel_id,
            "duration": str(duration),
            "uploaded_at": str(int(time.time())),
        }

        r2_url = upload_to_r2(
            data=content,
            key=r2_key,
            content_type="audio/mpeg",
            metadata=metadata
        )

        if r2_url:
            print(f"[Audio] Uploaded to R2: {filename} ({len(content) // 1024} KB)")
            return {
                "id": f"{channel_id}_discovered_{int(time.time())}",
                "url": r2_url,
                "name": track_name,
                "duration": duration,
                "source": source,
                "source_url": source_url,
                "attribution": track.get("attribution", f"Audio from {source}"),
                "_verified": True,
                "_discovered": True,
            }
        else:
            print(f"[Audio] R2 upload failed")
            return None

    except Exception as e:
        print(f"[Audio] Error downloading/uploading: {e}")
        return None


async def download_and_upload_to_r2(video: Dict, channel_id: str) -> Optional[Dict]:
    """
    Download video from source and upload to R2.
    Returns dict with R2 URL and metadata if successful.

    Args:
        video: Video info from search (url, name, source, identifier)
        channel_id: Channel requesting the video

    Returns:
        Dict with r2_url, name, attribution, etc. or None
    """
    if not video or not video.get("url"):
        return None

    if not r2_is_configured():
        print("[Video] R2 not configured - skipping upload")
        return None

    source_url = video["url"]
    video_name = video.get("name", "unknown")
    source = video.get("source", "unknown")
    identifier = video.get("identifier", "")

    # Create clean filename
    clean_name = re.sub(r'[^a-z0-9]', '_', video_name.lower())[:40]
    clean_name = re.sub(r'_+', '_', clean_name).strip('_')
    filename = f"{channel_id}_{clean_name}_{int(time.time())}.mp4"
    r2_key = f"video/{filename}"

    # Check if already in R2
    if check_exists(r2_key):
        print(f"[Video] Already in R2: {filename}")
        return {
            "url": get_public_url(r2_key),
            "name": video_name,
            "filename": filename,
            "source": source,
            "source_url": source_url,
            "identifier": identifier,
        }

    try:
        # Download video
        print(f"[Video] Downloading: {video_name[:40]}...")
        async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
            response = await client.get(source_url)

            if response.status_code != 200:
                print(f"[Video] Download failed: HTTP {response.status_code}")
                return None

            content = response.content
            content_type = response.headers.get("content-type", "video/mp4")

            # Validate it's actually a video
            if len(content) < 100_000:  # Less than 100KB is suspicious
                print(f"[Video] File too small: {len(content)} bytes")
                return None

            if "video" not in content_type and "octet-stream" not in content_type:
                # Check magic bytes for MP4
                if not content[:8].startswith(b'\x00\x00\x00') and b'ftyp' not in content[:12]:
                    print(f"[Video] Not a valid video file")
                    return None

        # Upload to R2 with attribution metadata
        metadata = {
            "source": source,
            "source_url": source_url[:256],  # R2 metadata has size limits
            "identifier": identifier[:128],
            "original_name": video_name[:128],
            "channel": channel_id,
            "uploaded_at": str(int(time.time())),
        }

        r2_url = upload_to_r2(
            data=content,
            key=r2_key,
            content_type="video/mp4",
            metadata=metadata
        )

        if r2_url:
            print(f"[Video] Uploaded to R2: {filename} ({len(content) // 1024} KB)")
            return {
                "url": r2_url,
                "name": video_name,
                "filename": filename,
                "source": source,
                "source_url": source_url,
                "identifier": identifier,
                "size_kb": len(content) // 1024,
            }
        else:
            print(f"[Video] R2 upload failed")
            return None

    except Exception as e:
        print(f"[Video] Error downloading/uploading: {e}")
        return None


async def proactive_video_discover(
    channel_id: str,
    taste: List[str],
    custom_query: str = None,
    current_videos: List[str] = None
) -> Optional[Dict]:
    """
    Agent discovers new videos based on their taste or a custom query.
    Searches Pexels (if API key available) and Archive.org.
    Returns video uploaded to R2, ready to use.

    Args:
        channel_id: The channel ID
        taste: List of taste preferences for query building
        custom_query: Optional custom search query (e.g., from reflection)
        current_videos: List of current video URLs to avoid duplicates
    """
    # Use custom query if provided, otherwise build from taste
    if custom_query:
        query = custom_query
        print(f"[Video Discovery] {channel_id} searching (reflection): {query}")
    else:
        # Build search query from taste
        queries = []
        for t in taste[:3]:  # Use first 3 taste preferences
            t_lower = t.lower().replace("-", "").replace("_", "")
            if t_lower in TASTE_TO_VIDEO_QUERY:
                queries.extend(TASTE_TO_VIDEO_QUERY[t_lower])
            else:
                queries.append(t)

        if not queries:
            queries = ["ambient", "abstract", "nature"]

        # Pick random query
        query = random.choice(queries)
        print(f"[Video Discovery] {channel_id} searching: {query}")

    # Search all sources (Pexels + Archive.org)
    results = await search_videos_all_sources(query, max_results=5)

    if not results:
        print(f"[Video Discovery] No results for: {query}")
        return None

    # Filter out videos we already have
    current_urls = set(current_videos or [])
    available = [v for v in results if v["url"] not in current_urls]

    if not available:
        available = results  # Use any if all filtered

    # Try each result until we find one that works
    random.shuffle(available)
    for video in available:
        # Download and upload to R2
        result = await download_and_upload_to_r2(video, channel_id)
        if result and result.get("url"):
            # Return video object ready for CHANNEL_VIDEOS
            clean_name = re.sub(r'[^a-zA-Z0-9\s]', '', result.get("name", "Discovered"))[:40].strip()
            source = result.get("source", "archive.org")
            # Build attribution string
            attribution = video.get("attribution", f"Video from {source}")
            return {
                "id": f"{channel_id}_discovered_{int(time.time())}",
                "name": clean_name or "Discovered Video",
                "url": result["url"],  # R2 URL
                "tags": query.split(),
                "source": source,
                "source_url": result.get("source_url", ""),
                "identifier": result.get("identifier", ""),
                "attribution": attribution,
                "added_at": int(time.time()),  # Unix timestamp when added
                "_verified": True,
            }

    print(f"[Video Discovery] No valid videos found for: {query}")
    return None


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
    Pre-verified tracks skip validation. Others are checked.
    """
    # Shuffle for variety
    candidates = [t for t in tracks if t.get("id") != exclude_id]
    random.shuffle(candidates)

    for track in candidates:
        # Skip validation for pre-verified exclusive tracks
        if track.get("_verified"):
            return track
        if await validate_track(track):
            return track

    # If no tracks validated, return first one anyway (let it fail gracefully)
    print(f"[URL] Warning: No validated tracks found, using fallback")
    return candidates[0] if candidates else None


async def get_validated_video(videos: List[Dict], exclude_id: str = None) -> Optional[Dict]:
    """
    Get a validated video from the list.
    Pre-verified videos skip validation. Others are checked.
    Avoids repeating the same video (exclude_id).
    """
    # Filter out the current video to avoid repeats
    available = [v for v in videos if v.get("id") != exclude_id] if exclude_id else videos

    # If all filtered out, allow current again (better than nothing)
    if not available:
        available = videos

    random.shuffle(available)

    for video in available:
        # Skip validation for pre-verified exclusive videos
        if video.get("_verified"):
            return video
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
# R2 CDN base URL - self-hosted for reliability
R2_BASE = "https://pub-c60e3a4de388402ba5e40acbc497a6d6.r2.dev"

CHANNEL_TRACKS = {
    # CH01: Late Night with Maya - lo-fi, introspective night coding vibes
    "ch01": [
        {"id": "ch01_1", "name": "Hanging Lanterns - Kalaido", "url": f"{R2_BASE}/audio/ch01_hanging_lanterns.mp3", "duration": 180, "attribution": "Hanging Lanterns by Kalaido (CC)", "source": "archive.org"},
        {"id": "ch01_2", "name": "First Snow - Kerusu", "url": f"{R2_BASE}/audio/ch01_first_snow.mp3", "duration": 195, "attribution": "First Snow by Kerusu (CC)", "source": "archive.org"},
        {"id": "ch01_3", "name": "Lofi Experimentin - Kronicle", "url": f"{R2_BASE}/audio/ch01_lofi_experimentin.mp3", "duration": 185, "attribution": "Lofi Experimentin by Kronicle (CC)", "source": "archive.org"},
    ],
    # CH02: Rain Café with Yuki - jazz café, cozy rain vibes
    "ch02": [
        {"id": "ch02_1", "name": "Lo-fi Rain Beat", "url": f"{R2_BASE}/audio/ch02_lofi_rain_beat.mp3", "duration": 170, "attribution": "Lo-fi Rain Beat (Free License)", "source": "archive.org"},
        {"id": "ch02_2", "name": "Chill Jazzy Lofi", "url": f"{R2_BASE}/audio/ch02_chill_jazzy_lofi.mp3", "duration": 180, "attribution": "Chill Jazzy Lofi (CC)", "source": "chosic"},
        {"id": "ch02_3", "name": "Herbal Tea Jazz", "url": f"{R2_BASE}/audio/ch02_herbal_tea_jazz.mp3", "duration": 195, "attribution": "Herbal Tea Jazz (CC)", "source": "chosic"},
    ],
    # CH03: Jazz Noir with Vincent - smoky detective jazz
    "ch03": [
        {"id": "ch03_1", "name": "Swing Jazz Grooves", "url": f"{R2_BASE}/audio/ch03_swing_jazz_grooves.mp3", "duration": 220, "attribution": "Swing Jazz Grooves (CC)", "source": "archive.org"},
        {"id": "ch03_2", "name": "Jazz Type Beat - Lukrembo", "url": f"{R2_BASE}/audio/ch03_jazz_type_beat.mp3", "duration": 165, "attribution": "Jazz Type Beat by Lukrembo (Free)", "source": "archive.org"},
        {"id": "ch03_3", "name": "Deep Space Jazz", "url": f"{R2_BASE}/audio/ch03_deep_space_jazz.mp3", "duration": 200, "attribution": "Deep Space Jazz (CC)", "source": "chosic"},
    ],
    # CH04: Synthwave with NEON - retro-futuristic neon dreams
    "ch04": [
        {"id": "ch04_1", "name": "Synthwave Dreams", "url": f"{R2_BASE}/audio/ch04_synthwave_dreams.mp3", "duration": 210, "attribution": "Synthwave Dreams (CC)", "source": "archive.org"},
        {"id": "ch04_2", "name": "Cyberpunk Night", "url": f"{R2_BASE}/audio/ch04_cyberpunk_night.mp3", "duration": 225, "attribution": "Cyberpunk Night (CC)", "source": "archive.org"},
        {"id": "ch04_3", "name": "Defective Beats", "url": f"{R2_BASE}/audio/ch04_defective_beats.mp3", "duration": 180, "attribution": "Defective Beats (CC)", "source": "chosic"},
    ],
    # CH05: Deep Space with Cosmos - vast cosmic ambience
    "ch05": [
        {"id": "ch05_1", "name": "Cosmic Drift", "url": f"{R2_BASE}/audio/ch05_cosmic_drift.mp3", "duration": 310, "attribution": "Cosmic Drift (CC)", "source": "chosic"},
        {"id": "ch05_2", "name": "Deep Ambient", "url": f"{R2_BASE}/audio/ch05_deep_ambient.mp3", "duration": 320, "attribution": "Deep Ambient by Dimaension X (CC)", "source": "archive.org"},
        {"id": "ch05_3", "name": "Night Meditation", "url": f"{R2_BASE}/audio/ch05_night_meditation.mp3", "duration": 285, "attribution": "Night Meditation (CC)", "source": "chosic"},
    ],
    # CH06: Tokyo Drift with Kenji - neon city nights, city pop
    "ch06": [
        {"id": "ch06_1", "name": "Finite Dreams", "url": f"{R2_BASE}/audio/ch06_finite_dreams.mp3", "duration": 195, "attribution": "Finite Dreams (CC)", "source": "chosic"},
        {"id": "ch06_2", "name": "Onion - Lukrembo", "url": f"{R2_BASE}/audio/ch06_onion_lukrembo.mp3", "duration": 175, "attribution": "Onion by Lukrembo (Free)", "source": "archive.org"},
        {"id": "ch06_3", "name": "Tranquillity", "url": f"{R2_BASE}/audio/ch06_tranquillity.mp3", "duration": 190, "attribution": "Tranquillity (CC)", "source": "chosic"},
    ],
    # CH07: Sunday Morning with Claire - peaceful acoustic warmth
    "ch07": [
        {"id": "ch07_1", "name": "Dancing On My Own", "url": f"{R2_BASE}/audio/ch07_dancing_on_my_own.mp3", "duration": 195, "attribution": "Dancing On My Own (CC)", "source": "chosic"},
        {"id": "ch07_2", "name": "Take Care - SURF", "url": f"{R2_BASE}/audio/ch07_take_care_surf.mp3", "duration": 185, "attribution": "Take Care by SURF (CC)", "source": "archive.org"},
        {"id": "ch07_3", "name": "Waves - Matt Quentin", "url": f"{R2_BASE}/audio/ch07_waves.mp3", "duration": 200, "attribution": "Waves by Matt Quentin (CC)", "source": "archive.org"},
    ],
    # CH08: Focus with Alan - minimal, distraction-free ambient
    "ch08": [
        {"id": "ch08_1", "name": "Focus Ambient", "url": f"{R2_BASE}/audio/ch08_focus_ambient.mp3", "duration": 280, "attribution": "Focus Ambient by Dimaension X (CC)", "source": "archive.org"},
        {"id": "ch08_2", "name": "Floating Ambient", "url": f"{R2_BASE}/audio/ch08_floating_ambient.mp3", "duration": 290, "attribution": "Floating Ambient (CC)", "source": "chosic"},
        {"id": "ch08_3", "name": "Ambient Space", "url": f"{R2_BASE}/audio/ch08_ambient_space.mp3", "duration": 300, "attribution": "Ambient Space by Dimaension X (CC)", "source": "archive.org"},
    ],
    # CH09: Melancholy with Daniel - sad, reflective, rainy nights
    "ch09": [
        {"id": "ch09_1", "name": "Sunset Drive", "url": f"{R2_BASE}/audio/ch09_sunset_drive.mp3", "duration": 185, "attribution": "Sunset Drive (CC)", "source": "chosic"},
        {"id": "ch09_2", "name": "Deep Electronic", "url": f"{R2_BASE}/audio/ch09_deep_electronic.mp3", "duration": 275, "attribution": "Deep Electronic (CC)", "source": "chosic"},
        {"id": "ch09_3", "name": "Electronic Dreams", "url": f"{R2_BASE}/audio/ch09_electronic_dreams.mp3", "duration": 290, "attribution": "Electronic Dreams (CC)", "source": "chosic"},
    ],
    # CH10: Golden Hour with Iris - warm sunset, golden light
    "ch10": [
        {"id": "ch10_1", "name": "Soft Piano Dreams", "url": f"{R2_BASE}/audio/ch10_soft_piano_dreams.mp3", "duration": 300, "attribution": "Soft Piano Dreams (CC)", "source": "chosic"},
        {"id": "ch10_2", "name": "Rainy Window Piano", "url": f"{R2_BASE}/audio/ch10_rainy_window_piano.mp3", "duration": 320, "attribution": "Rainy Window Piano (CC)", "source": "chosic"},
        {"id": "ch10_3", "name": "Evening Reflection", "url": f"{R2_BASE}/audio/ch10_evening_reflection.mp3", "duration": 290, "attribution": "Evening Reflection (CC)", "source": "chosic"},
    ],
}

# Legacy shared tracks - kept empty for backwards compatibility
# All tracks are now exclusive per-channel in CHANNEL_TRACKS above
CURATED_TRACKS: Dict[str, List[Dict]] = {}


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

        # Upload to R2 for persistence
        r2_track = await download_and_upload_audio_to_r2(track, channel_id)
        if r2_track:
            print(f"[Discovery] {channel_id} uploaded to R2: {r2_track['name']}")
            return r2_track
        else:
            # Return original if R2 upload fails (still usable but may break later)
            return track

    # Fallback to curated (these are already in R2)
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


# EXCLUSIVE CHANNEL VIDEOS - ZERO OVERLAP
# Each channel has unique videos that NO other channel uses
# 12 unique videos distributed across 10 channels
CHANNEL_VIDEOS = {
    # CH01: Maya - lo-fi city vibes (expanded library)
    "ch01": [
        {"id": "ch01_v1", "name": "City Timelapse", "url": f"{R2_BASE}/video/ch01_city_timelapse.mp4", "tags": ["city", "night", "lo-fi"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch01_v2", "name": "City Night Traffic", "url": "https://assets.mixkit.co/videos/4484/4484-720.mp4", "tags": ["city", "night", "traffic"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch01_v3", "name": "City Skyline", "url": "https://assets.mixkit.co/videos/4063/4063-720.mp4", "tags": ["city", "skyline", "sunset"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch01_v4", "name": "Street Lights", "url": "https://assets.mixkit.co/videos/4636/4636-720.mp4", "tags": ["city", "lights", "night"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
    ],
    # CH02: Yuki - rainy cozy vibes (expanded library)
    "ch02": [
        {"id": "ch02_v1", "name": "Rain Cafe", "url": f"{R2_BASE}/video/ch02_rain_cafe.mp4", "tags": ["rain", "cozy", "cafe"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch02_v2", "name": "Rain Drops", "url": "https://assets.mixkit.co/videos/4271/4271-720.mp4", "tags": ["rain", "drops", "macro"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch02_v3", "name": "Rain Puddles", "url": "https://assets.mixkit.co/videos/4278/4278-720.mp4", "tags": ["rain", "puddles", "street"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch02_v4", "name": "Cozy Fireplace", "url": "https://assets.mixkit.co/videos/3455/3455-720.mp4", "tags": ["cozy", "fire", "warm"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
    ],
    # CH03: Vincent - jazz noir city (expanded library)
    "ch03": [
        {"id": "ch03_v1", "name": "Jazz Noir", "url": f"{R2_BASE}/video/ch03_jazz_noir.mp4", "tags": ["jazz", "noir", "night"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch03_v2", "name": "City Noir Night", "url": "https://assets.mixkit.co/videos/4633/4633-720.mp4", "tags": ["city", "noir", "night"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch03_v3", "name": "Night Drive", "url": "https://assets.mixkit.co/videos/4358/4358-720.mp4", "tags": ["drive", "night", "city"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch03_v4", "name": "Bar Atmosphere", "url": "https://assets.mixkit.co/videos/3457/3457-720.mp4", "tags": ["bar", "cozy", "night"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
    ],
    # CH04: NEON-7 - synthwave space (expanded library)
    "ch04": [
        {"id": "ch04_v1", "name": "Galaxy Travel", "url": f"{R2_BASE}/video/ch04_galaxy_travel.mp4", "tags": ["galaxy", "synthwave", "neon"], "attribution": "Video from Archive.org (Public Domain)", "source": "archive.org"},
        {"id": "ch04_v2", "name": "Neon Tunnel", "url": "https://assets.mixkit.co/videos/4696/4696-720.mp4", "tags": ["neon", "tunnel", "abstract"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch04_v3", "name": "Digital Grid", "url": "https://assets.mixkit.co/videos/4694/4694-720.mp4", "tags": ["grid", "digital", "retro"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch04_v4", "name": "Space Nebula", "url": "https://assets.mixkit.co/videos/9797/9797-720.mp4", "tags": ["space", "nebula", "cosmic"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
    ],
    # CH05: Cosmos - cosmic space exploration (expanded library)
    "ch05": [
        {"id": "ch05_v1", "name": "Eclipse Cosmic", "url": f"{R2_BASE}/video/ch05_cosmic.mp4", "tags": ["cosmic", "space", "eclipse"], "attribution": "Video from Archive.org (Public Domain)", "source": "archive.org"},
        {"id": "ch05_v2", "name": "Aurora Stars", "url": f"{R2_BASE}/video/ch05_stars.mp4", "tags": ["stars", "aurora", "infinite"], "attribution": "Video from Archive.org (Public Domain)", "source": "archive.org"},
        {"id": "ch05_v3", "name": "Deep Space", "url": "https://assets.mixkit.co/videos/9799/9799-720.mp4", "tags": ["space", "stars", "deep"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch05_v4", "name": "Galaxy Drift", "url": "https://assets.mixkit.co/videos/9798/9798-720.mp4", "tags": ["galaxy", "drift", "cosmic"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
    ],
    # CH06: Kenji - city pop night drive (expanded library)
    "ch06": [
        {"id": "ch06_v1", "name": "Tokyo Night", "url": f"{R2_BASE}/video/ch06_tokyo_night.mp4", "tags": ["tokyo", "neon", "night"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch06_v2", "name": "City Drive", "url": "https://assets.mixkit.co/videos/4359/4359-720.mp4", "tags": ["drive", "city", "night"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch06_v3", "name": "Neon Streets", "url": "https://assets.mixkit.co/videos/4635/4635-720.mp4", "tags": ["neon", "city", "night"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch06_v4", "name": "Downtown Lights", "url": "https://assets.mixkit.co/videos/4637/4637-720.mp4", "tags": ["downtown", "lights", "night"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
    ],
    # CH07: Claire - sunday morning nature (expanded library)
    "ch07": [
        {"id": "ch07_v1", "name": "Sunday Nature", "url": f"{R2_BASE}/video/ch07_sunday_nature.mp4", "tags": ["nature", "morning", "peaceful"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch07_v2", "name": "Morning Meadow", "url": "https://assets.mixkit.co/videos/3123/3123-720.mp4", "tags": ["meadow", "morning", "nature"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch07_v3", "name": "Peaceful Lake", "url": "https://assets.mixkit.co/videos/4266/4266-720.mp4", "tags": ["lake", "peaceful", "nature"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch07_v4", "name": "Gentle Breeze", "url": "https://assets.mixkit.co/videos/3124/3124-720.mp4", "tags": ["breeze", "grass", "nature"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
    ],
    # CH08: Alan - abstract focus minimal (expanded library)
    "ch08": [
        {"id": "ch08_v1", "name": "Abstract Lines", "url": f"{R2_BASE}/video/ch08_abstract.mp4", "tags": ["abstract", "focus", "lines"], "attribution": "Video from Archive.org (Public Domain)", "source": "archive.org"},
        {"id": "ch08_v2", "name": "Minimal Motion", "url": f"{R2_BASE}/video/ch08_minimal.mp4", "tags": ["minimal", "clean", "simple"], "attribution": "Video from Archive.org (Public Domain)", "source": "archive.org"},
        {"id": "ch08_v3", "name": "Geometric Flow", "url": "https://assets.mixkit.co/videos/4695/4695-720.mp4", "tags": ["geometric", "abstract", "flow"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch08_v4", "name": "Particle Motion", "url": "https://assets.mixkit.co/videos/4693/4693-720.mp4", "tags": ["particles", "motion", "abstract"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
    ],
    # CH09: Daniel - melancholy ocean/rain/city vibes (expanded library)
    "ch09": [
        {"id": "ch09_v1", "name": "Ocean Waves", "url": f"{R2_BASE}/video/ch09_ocean.mp4", "tags": ["ocean", "waves", "melancholy"], "attribution": "Video from Archive.org (Public Domain)", "source": "archive.org"},
        {"id": "ch09_v2", "name": "Rain on Window", "url": "https://assets.mixkit.co/videos/18308/18308-720.mp4", "tags": ["rain", "window", "night"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch09_v3", "name": "Rainy Street", "url": "https://assets.mixkit.co/videos/33951/33951-720.mp4", "tags": ["rain", "street", "city"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch09_v4", "name": "City in Rain", "url": "https://assets.mixkit.co/videos/4634/4634-720.mp4", "tags": ["rain", "city", "night"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch09_v5", "name": "Foggy Forest", "url": "https://assets.mixkit.co/videos/3572/3572-720.mp4", "tags": ["forest", "fog", "nature"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
    ],
    # CH10: Iris - dreamy golden/sunset/nature vibes (expanded library)
    "ch10": [
        {"id": "ch10_v1", "name": "Golden Moon", "url": f"{R2_BASE}/video/ch10_golden_light.mp4", "tags": ["golden", "moon", "sunset"], "attribution": "Video from Archive.org (Public Domain)", "source": "archive.org"},
        {"id": "ch10_v2", "name": "Sunset Clouds", "url": "https://assets.mixkit.co/videos/4064/4064-720.mp4", "tags": ["sunset", "clouds", "sky"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch10_v3", "name": "Golden Hour Field", "url": "https://assets.mixkit.co/videos/3122/3122-720.mp4", "tags": ["golden", "field", "nature"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch10_v4", "name": "Forest Stream", "url": "https://assets.mixkit.co/videos/42757/42757-720.mp4", "tags": ["forest", "stream", "nature"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
        {"id": "ch10_v5", "name": "Misty Mountains", "url": "https://assets.mixkit.co/videos/3569/3569-720.mp4", "tags": ["mountains", "mist", "nature"], "attribution": "Video from Mixkit (Free License)", "source": "mixkit"},
    ],
}


# ============ LOAD DISCOVERED MEDIA ON STARTUP ============
# Merge any previously discovered media into the base libraries

def _seed_base_media_to_db():
    """Seed base videos and tracks to database (one-time)."""
    conn = sqlite3.connect(str(MEDIA_DB_FILE))

    # Check if already seeded
    count = conn.execute("SELECT COUNT(*) FROM videos WHERE is_base = 1").fetchone()[0]
    if count > 0:
        conn.close()
        return  # Already seeded

    print("[DB] Seeding base media to database...")

    # Seed base videos
    for ch_id, videos in CHANNEL_VIDEOS.items():
        for v in videos:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO videos
                    (id, channel_id, name, url, tags, attribution, source, source_url, added_at, is_base)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    v.get("id"),
                    ch_id,
                    v.get("name"),
                    v.get("url"),
                    json.dumps(v.get("tags", [])),
                    v.get("attribution"),
                    v.get("source"),
                    v.get("source_url"),
                    int(time.time()),
                ))
            except Exception as e:
                print(f"[DB] Error seeding video: {e}")

    # Seed base tracks
    for ch_id, tracks in CHANNEL_TRACKS.items():
        for t in tracks:
            try:
                conn.execute("""
                    INSERT OR IGNORE INTO tracks
                    (id, channel_id, name, url, duration, tags, attribution, source, added_at, is_base)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                """, (
                    t.get("id"),
                    ch_id,
                    t.get("name"),
                    t.get("url"),
                    t.get("duration", 180),
                    json.dumps(t.get("tags", [])),
                    t.get("attribution"),
                    t.get("source"),
                    int(time.time()),
                ))
            except Exception as e:
                print(f"[DB] Error seeding track: {e}")

    conn.commit()
    conn.close()

    stats = get_db_stats()
    print(f"[DB] Seeded {stats['total_videos']} videos, {stats['total_tracks']} tracks")

def _merge_discovered_media():
    """Load and merge discovered media into CHANNEL_VIDEOS and CHANNEL_TRACKS."""
    # First seed base media to DB
    _seed_base_media_to_db()

    # Then load discovered media from DB
    discovered = load_discovered_media()

    # Merge discovered videos
    for ch_id, videos in discovered.get("videos", {}).items():
        if ch_id not in CHANNEL_VIDEOS:
            CHANNEL_VIDEOS[ch_id] = []
        existing_urls = {v.get("url") for v in CHANNEL_VIDEOS[ch_id]}
        for video in videos:
            if video.get("url") and video.get("url") not in existing_urls:
                video["_discovered"] = True
                CHANNEL_VIDEOS[ch_id].append(video)
                existing_urls.add(video.get("url"))

    # Merge discovered tracks
    for ch_id, tracks in discovered.get("tracks", {}).items():
        if ch_id not in CHANNEL_TRACKS:
            CHANNEL_TRACKS[ch_id] = []
        existing_urls = {t.get("url") for t in CHANNEL_TRACKS[ch_id]}
        for track in tracks:
            if track.get("url") and track.get("url") not in existing_urls:
                track["_discovered"] = True
                CHANNEL_TRACKS[ch_id].append(track)
                existing_urls.add(track.get("url"))

    total_v = sum(len(v) for v in discovered.get("videos", {}).values())
    total_t = sum(len(t) for t in discovered.get("tracks", {}).values())
    if total_v > 0 or total_t > 0:
        print(f"[DB] Merged {total_v} discovered videos, {total_t} discovered tracks")

# Run on module load
_merge_discovered_media()


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
    # Use exclusive channel tracks - these are PRE-VERIFIED, skip validation
    if channel_id in CHANNEL_TRACKS:
        tracks = CHANNEL_TRACKS[channel_id].copy()
        # Mark as pre-verified to skip slow URL validation
        for t in tracks:
            t["_verified"] = True
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
    # Use exclusive channel videos - these are PRE-VERIFIED, skip validation
    if channel_id in CHANNEL_VIDEOS:
        videos = CHANNEL_VIDEOS[channel_id].copy()
        # Mark as pre-verified to skip slow URL validation
        for v in videos:
            v["_verified"] = True
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
