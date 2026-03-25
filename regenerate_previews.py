"""Regenerate preview videos for CH1, CH2, CH3 with better prompts."""
import httpx
import asyncio
from pathlib import Path

API_KEY = "4379a644-f5b9-4a48-9e2b-a55efafa0fcc"
API_BASE = "https://ark.ap-southeast.bytepluses.com/api/v3"
VIDEO_MODEL = "seedance-1-5-pro-251215"

ASSETS_DIR = Path("public/assets/channels")

# Better prompts - more artistic, less stock
CHANNELS_TO_REGENERATE = [
    {
        "id": "ch01",
        "name": "Late Night",
        "prompt": "Abstract cinematic: Rain droplets on glass with blurred city bokeh lights behind, warm amber glow from desk lamp reflection, soft focus, intimate night atmosphere, lo-fi aesthetic, gentle movement of light through water, 4K film quality",
    },
    {
        "id": "ch02",
        "name": "Rain Café",
        "prompt": "Abstract cinematic: Close-up of coffee steam rising in warm light, rain streaks on window glass in background, soft jazz vinyl record spinning blur, golden hour cafe lighting, dreamy shallow depth of field, cozy intimate mood, film grain texture",
    },
    {
        "id": "ch03",
        "name": "Jazz Noir",
        "prompt": "Abstract cinematic: Cigarette smoke curling through single spotlight beam, deep shadows, saxophone brass reflection catching light, 1950s film noir aesthetic, black and white with warm sepia tones, moody atmospheric, grainy 35mm film look",
    },
]


async def create_video_task(client: httpx.AsyncClient, channel: dict) -> str | None:
    """Create a video generation task."""
    print(f"Creating video task for: {channel['name']}")
    print(f"  Prompt: {channel['prompt'][:80]}...")

    response = await client.post(
        f"{API_BASE}/contents/generations/tasks",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
        json={
            "model": VIDEO_MODEL,
            "content": [{"type": "text", "text": channel["prompt"]}],
            "resolution": "720p",
            "ratio": "3:4",
            "duration": 4,
            "watermark": False,
            "camera_fixed": True,  # Less movement for abstract scenes
        },
    )

    if response.status_code != 200:
        print(f"  Error: {response.status_code}")
        print(f"  {response.text[:300]}")
        return None

    data = response.json()
    task_id = data.get("id")
    print(f"  Task ID: {task_id}")
    return task_id


async def get_video_result(client: httpx.AsyncClient, task_id: str) -> str | None:
    """Poll for video result."""
    print(f"  Polling...")

    for attempt in range(120):
        await asyncio.sleep(5)

        response = await client.get(
            f"{API_BASE}/contents/generations/tasks/{task_id}",
            headers={"Authorization": f"Bearer {API_KEY}"},
        )

        if response.status_code != 200:
            continue

        data = response.json()
        status = data.get("status", "unknown")

        if attempt % 6 == 0:
            print(f"  Status: {status} (attempt {attempt + 1})")

        if status == "succeeded":
            video_url = data.get("content", {}).get("video_url")
            if video_url:
                print(f"  Video ready!")
                return video_url

        elif status == "failed":
            print(f"  Failed: {data.get('error', {})}")
            return None

    print(f"  Timeout")
    return None


async def download_video(client: httpx.AsyncClient, url: str, channel_id: str) -> bool:
    """Download video."""
    print(f"  Downloading...")

    response = await client.get(url)
    if response.status_code == 200:
        filepath = ASSETS_DIR / f"{channel_id}_preview.mp4"
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"  Saved: {filepath}")
        return True
    return False


async def main():
    print("=" * 60)
    print("REGENERATING CH1, CH2, CH3 PREVIEWS")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=300.0) as client:
        for channel in CHANNELS_TO_REGENERATE:
            print(f"\n{'='*60}")
            print(f"Channel: {channel['name']} ({channel['id']})")
            print(f"{'='*60}")

            task_id = await create_video_task(client, channel)
            if not task_id:
                print(f"FAILED: {channel['name']}")
                continue

            video_url = await get_video_result(client, task_id)
            if not video_url:
                print(f"FAILED: {channel['name']}")
                continue

            success = await download_video(client, video_url, channel["id"])
            if success:
                print(f"SUCCESS: {channel['name']}")
            else:
                print(f"FAILED: {channel['name']}")

            await asyncio.sleep(2)

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
