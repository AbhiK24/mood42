"""Generate channel preview videos using BytePlus Seaweed video model."""
import httpx
import asyncio
import json
import time
from pathlib import Path

API_KEY = "4379a644-f5b9-4a48-9e2b-a55efafa0fcc"
API_BASE = "https://ark.ap-southeast.bytepluses.com/api/v3"

# Video generation model
VIDEO_MODEL = "seaweed-video-01"

ASSETS_DIR = Path("public/assets/channels")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Channel video prompts - cinematic scenes with the manager's vibe
CHANNEL_VIDEOS = [
    {
        "id": "ch01",
        "name": "Late Night",
        "prompt": """
            Cinematic loop: Software engineer at desk, 3AM, rain hitting window,
            city lights twinkling outside, warm desk lamp glow, coffee steam rising,
            code on screen, lo-fi aesthetic, cozy night coding session,
            subtle camera movement, atmospheric, 4K quality
        """,
    },
    {
        "id": "ch02",
        "name": "Rain Café",
        "prompt": """
            Cinematic loop: Japanese kissaten coffee shop interior, rain outside window,
            vinyl record spinning, steam from coffee cup, warm amber lighting,
            plants on windowsill, vintage aesthetic, peaceful rainy afternoon,
            gentle camera drift, 4K quality
        """,
    },
    {
        "id": "ch03",
        "name": "Jazz Noir",
        "prompt": """
            Cinematic loop: 1950s jazz club, smoky atmosphere, dim spotlight,
            saxophone silhouette, noir shadows, whiskey glass on piano,
            film grain, black and white tones, mysterious mood,
            slow pan, 4K quality
        """,
    },
    {
        "id": "ch04",
        "name": "Synthwave",
        "prompt": """
            Cinematic loop: Retro-futuristic neon landscape, purple and pink sunset,
            chrome car driving on grid road, palm trees silhouette,
            80s aesthetic, VHS look, synthwave vibes, glowing horizon,
            forward motion, 4K quality
        """,
    },
    {
        "id": "ch05",
        "name": "Deep Space",
        "prompt": """
            Cinematic loop: Deep space nebula, stars slowly drifting,
            cosmic dust clouds in purple and blue, distant galaxy,
            astronaut floating peacefully, infinite void feeling,
            slow zoom through stars, 4K quality
        """,
    },
    {
        "id": "ch06",
        "name": "Tokyo Drift",
        "prompt": """
            Cinematic loop: Tokyo street at night after rain, neon signs reflecting,
            empty alley, vending machines glowing, steam from grate,
            cyberpunk aesthetic, Japanese text signs, moody atmosphere,
            slow dolly forward, 4K quality
        """,
    },
    {
        "id": "ch07",
        "name": "Sunday Morning",
        "prompt": """
            Cinematic loop: Sunlit farmhouse kitchen, golden morning light streaming,
            plants on windowsill, fresh bread on table, dust particles in light,
            peaceful countryside view outside, warm and hopeful mood,
            gentle camera sway, 4K quality
        """,
    },
    {
        "id": "ch08",
        "name": "Focus",
        "prompt": """
            Cinematic loop: Minimal Scandinavian workspace, clean white desk,
            single plant, natural light, laptop and notebook,
            zen aesthetic, productivity mood, calm and focused,
            subtle breathing camera movement, 4K quality
        """,
    },
    {
        "id": "ch09",
        "name": "Melancholy",
        "prompt": """
            Cinematic loop: Rainy London window view, writer's room,
            typewriter on desk, grey sky, contemplative mood,
            books stacked, tea cup, melancholic but beautiful,
            slow camera drift with rain drops, 4K quality
        """,
    },
    {
        "id": "ch10",
        "name": "Golden Hour",
        "prompt": """
            Cinematic loop: Lisbon rooftops at golden hour, warm sunset light,
            terracotta tiles, laundry on lines, church bells visible,
            magical warm glow, nostalgic Portuguese summer evening,
            gentle pan across cityscape, 4K quality
        """,
    },
]


async def generate_video(channel: dict):
    """Generate a video for a channel using BytePlus Seaweed."""
    print(f"\n{'='*60}")
    print(f"Generating video for: {channel['name']} ({channel['id']})")
    print(f"{'='*60}")

    prompt = channel["prompt"].strip().replace("\n", " ").replace("  ", " ")
    print(f"Prompt: {prompt[:100]}...")

    async with httpx.AsyncClient(timeout=300.0) as client:
        # Submit video generation request
        print("Submitting generation request...")
        response = await client.post(
            f"{API_BASE}/video/generations",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}",
            },
            json={
                "model": VIDEO_MODEL,
                "prompt": prompt,
                "duration": 4,  # 4 second loop
                "resolution": "720p",
                "fps": 24,
            },
        )

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(response.text)
            return None

        data = response.json()
        print(f"Response: {json.dumps(data, indent=2)[:500]}")

        # Check for task ID (async generation)
        if "task_id" in data:
            task_id = data["task_id"]
            print(f"Task ID: {task_id}")

            # Poll for completion
            for attempt in range(60):  # Max 5 minutes
                await asyncio.sleep(5)
                print(f"Checking status... (attempt {attempt + 1})")

                status_response = await client.get(
                    f"{API_BASE}/video/generations/{task_id}",
                    headers={"Authorization": f"Bearer {API_KEY}"},
                )

                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get("status", "unknown")
                    print(f"Status: {status}")

                    if status == "completed":
                        video_url = status_data.get("video_url") or status_data.get("data", {}).get("url")
                        if video_url:
                            return await download_video(client, video_url, channel["id"])
                    elif status == "failed":
                        print(f"Generation failed: {status_data}")
                        return None

        # Direct URL response
        elif "data" in data and len(data["data"]) > 0:
            video_url = data["data"][0].get("url")
            if video_url:
                return await download_video(client, video_url, channel["id"])

        # Video URL in response
        elif "video_url" in data:
            return await download_video(client, data["video_url"], channel["id"])

    print("No video URL found in response")
    return None


async def download_video(client: httpx.AsyncClient, url: str, channel_id: str):
    """Download video from URL."""
    print(f"Downloading video from: {url[:80]}...")

    video_response = await client.get(url)
    if video_response.status_code == 200:
        filepath = ASSETS_DIR / f"{channel_id}_preview.mp4"
        with open(filepath, "wb") as f:
            f.write(video_response.content)
        print(f"Saved: {filepath}")
        return filepath
    else:
        print(f"Download failed: {video_response.status_code}")
        return None


async def main():
    print("=" * 60)
    print("MOOD42 - CHANNEL VIDEO GENERATION")
    print("Using BytePlus Seaweed Video Model")
    print("=" * 60)

    for channel in CHANNEL_VIDEOS:
        try:
            result = await generate_video(channel)
            if result:
                print(f"✓ {channel['name']} video generated successfully")
            else:
                print(f"✗ {channel['name']} video generation failed")

            # Rate limiting
            await asyncio.sleep(3)

        except Exception as e:
            print(f"Error generating {channel['name']}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print("GENERATION COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
