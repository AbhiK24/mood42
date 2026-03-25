"""Generate channel preview videos using BytePlus Seedance video model."""
import httpx
import asyncio
import json
from pathlib import Path

API_KEY = "4379a644-f5b9-4a48-9e2b-a55efafa0fcc"
API_BASE = "https://ark.ap-southeast.bytepluses.com/api/v3"

# Seedance video model
VIDEO_MODEL = "seedance-1-5-pro-251215"

ASSETS_DIR = Path("public/assets/channels")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Channel video prompts - cinematic scenes
CHANNEL_VIDEOS = [
    {
        "id": "ch01",
        "name": "Late Night",
        "prompt": "Cinematic scene: Software engineer coding at desk, 3AM, rain hitting window, city lights outside, warm desk lamp, coffee steam, lo-fi cozy atmosphere, subtle movement",
        "image": "ch01_late_night.png",
    },
    {
        "id": "ch02",
        "name": "Rain Café",
        "prompt": "Cinematic scene: Japanese kissaten coffee shop, rain outside window, vinyl record spinning, steam from coffee cup, warm amber lighting, peaceful rainy afternoon",
        "image": "ch02_rain_cafe.png",
    },
    {
        "id": "ch03",
        "name": "Jazz Noir",
        "prompt": "Cinematic scene: 1950s jazz club, smoky atmosphere, dim spotlight, saxophone silhouette, noir shadows, whiskey glass on piano, film grain aesthetic",
        "image": "ch03_jazz_noir.png",
    },
    {
        "id": "ch04",
        "name": "Synthwave",
        "prompt": "Cinematic scene: Retro-futuristic neon landscape, purple pink sunset, chrome car on grid road, 80s synthwave aesthetic, VHS look, glowing horizon",
        "image": "ch04_synthwave.png",
    },
    {
        "id": "ch05",
        "name": "Deep Space",
        "prompt": "Cinematic scene: Deep space nebula, stars slowly drifting, cosmic dust clouds purple blue, distant galaxy, astronaut floating, infinite void",
        "image": "ch05_deep_space.png",
    },
    {
        "id": "ch06",
        "name": "Tokyo Drift",
        "prompt": "Cinematic scene: Tokyo street at night after rain, neon signs reflecting on wet pavement, empty alley, vending machines glowing, cyberpunk atmosphere",
        "image": "ch06_tokyo_drift.png",
    },
    {
        "id": "ch07",
        "name": "Sunday Morning",
        "prompt": "Cinematic scene: Sunlit farmhouse kitchen, golden morning light streaming through window, plants on windowsill, fresh bread, dust particles in light",
        "image": "ch07_sunday_morning.png",
    },
    {
        "id": "ch08",
        "name": "Focus",
        "prompt": "Cinematic scene: Minimal Scandinavian workspace, clean white desk, single plant, natural light from window, laptop and notebook, zen productivity",
        "image": "ch08_focus.png",
    },
    {
        "id": "ch09",
        "name": "Melancholy",
        "prompt": "Cinematic scene: Rainy London window view, writer's room, typewriter on desk, grey sky, contemplative mood, books stacked, tea cup steaming",
        "image": "ch09_melancholy.png",
    },
    {
        "id": "ch10",
        "name": "Golden Hour",
        "prompt": "Cinematic scene: Lisbon rooftops at golden hour, warm sunset light, terracotta tiles, laundry on lines, church bells visible, magical warm glow",
        "image": "ch10_golden_hour.png",
    },
]


async def create_video_task(client: httpx.AsyncClient, channel: dict) -> str | None:
    """Create a video generation task, returns task ID."""
    print(f"Creating video task for: {channel['name']}")

    # Build content array - use existing image as first frame
    image_path = ASSETS_DIR / channel["image"]

    content = [
        {
            "type": "text",
            "text": channel["prompt"]
        }
    ]

    # If we have an existing image, use it as first frame reference
    if image_path.exists():
        # For image-to-video, we'd need to upload or use a URL
        # For now, just use text-to-video
        pass

    response = await client.post(
        f"{API_BASE}/contents/generations/tasks",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
        json={
            "model": VIDEO_MODEL,
            "content": content,
            "resolution": "720p",
            "ratio": "3:4",  # Portrait for cards
            "duration": 4,  # 4 second loop
            "watermark": False,
            "camera_fixed": False,
        },
    )

    if response.status_code != 200:
        print(f"  Error creating task: {response.status_code}")
        print(f"  Response: {response.text[:500]}")
        return None

    data = response.json()
    task_id = data.get("id")
    print(f"  Task created: {task_id}")
    return task_id


async def get_video_result(client: httpx.AsyncClient, task_id: str) -> str | None:
    """Poll for video generation result, returns video URL."""
    print(f"  Polling for result...")

    for attempt in range(120):  # Max 10 minutes
        await asyncio.sleep(5)

        response = await client.get(
            f"{API_BASE}/contents/generations/tasks/{task_id}",
            headers={
                "Authorization": f"Bearer {API_KEY}",
            },
        )

        if response.status_code != 200:
            print(f"  Poll error: {response.status_code}")
            continue

        data = response.json()
        status = data.get("status", "unknown")

        if attempt % 6 == 0:  # Log every 30 seconds
            print(f"  Status: {status} (attempt {attempt + 1})")

        if status == "succeeded":
            video_url = data.get("content", {}).get("video_url")
            if video_url:
                print(f"  Video ready!")
                return video_url

        elif status == "failed":
            error = data.get("error", {})
            print(f"  Generation failed: {error}")
            return None

    print(f"  Timeout waiting for video")
    return None


async def download_video(client: httpx.AsyncClient, url: str, channel_id: str) -> Path | None:
    """Download video from URL."""
    print(f"  Downloading video...")

    response = await client.get(url)
    if response.status_code == 200:
        filepath = ASSETS_DIR / f"{channel_id}_preview.mp4"
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"  Saved: {filepath}")
        return filepath
    else:
        print(f"  Download failed: {response.status_code}")
        return None


async def generate_channel_video(channel: dict) -> bool:
    """Generate video for a single channel."""
    print(f"\n{'='*60}")
    print(f"Channel: {channel['name']} ({channel['id']})")
    print(f"{'='*60}")

    async with httpx.AsyncClient(timeout=300.0) as client:
        # Create task
        task_id = await create_video_task(client, channel)
        if not task_id:
            return False

        # Wait for result
        video_url = await get_video_result(client, task_id)
        if not video_url:
            return False

        # Download video
        result = await download_video(client, video_url, channel["id"])
        return result is not None


async def main():
    print("=" * 60)
    print("MOOD42 - CHANNEL VIDEO GENERATION")
    print("Using BytePlus Seedance Video Model")
    print(f"Model: {VIDEO_MODEL}")
    print("=" * 60)

    results = {"success": [], "failed": []}

    for channel in CHANNEL_VIDEOS:
        try:
            success = await generate_channel_video(channel)
            if success:
                results["success"].append(channel["name"])
                print(f"✓ {channel['name']} - SUCCESS")
            else:
                results["failed"].append(channel["name"])
                print(f"✗ {channel['name']} - FAILED")

            # Rate limiting between requests
            await asyncio.sleep(2)

        except Exception as e:
            results["failed"].append(channel["name"])
            print(f"✗ {channel['name']} - ERROR: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print(f"Success: {len(results['success'])}/{len(CHANNEL_VIDEOS)}")
    print(f"Failed: {results['failed']}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
