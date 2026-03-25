"""Generate agent avatar images using BytePlus Seedance."""
import httpx
import asyncio
from pathlib import Path

API_KEY = "4379a644-f5b9-4a48-9e2b-a55efafa0fcc"
API_BASE = "https://ark.ap-southeast.bytepluses.com/api/v3"
VIDEO_MODEL = "seedance-1-5-pro-251215"

ASSETS_DIR = Path("public/assets/avatars")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Agent avatar prompts - stylized portraits
AGENTS = [
    {
        "id": "maya_chen",
        "name": "Maya Chen",
        "prompt": "Cinematic portrait: Young Asian woman software engineer, warm desk lamp lighting, wearing cozy hoodie, glasses reflecting code, lo-fi aesthetic, soft bokeh background, intimate late night mood, film grain, 3/4 view"
    },
    {
        "id": "yuki_tanaka",
        "name": "Yuki Tanaka",
        "prompt": "Cinematic portrait: Japanese man in his 40s, cozy knit sweater, warm cafe lighting, vinyl records in background, gentle smile, steam from coffee cup, rain on window reflection, nostalgic film look, 3/4 view"
    },
    {
        "id": "vincent_moreau",
        "name": "Vincent Moreau",
        "prompt": "Cinematic portrait: 1950s jazz musician, African American man, fedora hat, cigarette smoke, dramatic noir lighting, single spotlight, saxophone reflection, black and white with sepia tint, film noir aesthetic"
    },
    {
        "id": "neon7",
        "name": "NEON-7",
        "prompt": "Cinematic portrait: Abstract AI entity, geometric face made of neon grid lines, purple and pink glow, synthwave aesthetic, chrome reflections, digital glitch effects, retro-futuristic, VHS scan lines"
    },
    {
        "id": "cosmos",
        "name": "Cosmos",
        "prompt": "Cinematic portrait: Ethereal cosmic being, face made of stars and nebulae, deep space background, purple blue cosmic dust, glowing eyes like distant galaxies, mystical and infinite, dreamy soft focus"
    },
    {
        "id": "kenji_nakamura",
        "name": "Kenji Nakamura",
        "prompt": "Cinematic portrait: Japanese photographer in his 30s, Tokyo neon lights reflecting on face, wet streets background, camera around neck, cyberpunk aesthetic, rain droplets, moody night atmosphere"
    },
    {
        "id": "claire_dubois",
        "name": "Claire Dubois",
        "prompt": "Cinematic portrait: French woman in her 30s, natural morning light, linen shirt, wildflowers nearby, farmhouse kitchen background, golden hour warmth, peaceful serene expression, soft pastoral aesthetic"
    },
    {
        "id": "alan_park",
        "name": "Alan Park",
        "prompt": "Cinematic portrait: Korean-American man, minimalist clean aesthetic, neutral grey background, simple white shirt, natural soft lighting, calm focused expression, zen simplicity, modern professional look"
    },
    {
        "id": "daniel_webb",
        "name": "Daniel Webb",
        "prompt": "Cinematic portrait: British writer in his 40s, rainy London window behind, typewriter nearby, wool sweater, contemplative melancholic expression, grey moody lighting, books in background, literary aesthetic"
    },
    {
        "id": "iris_ferreira",
        "name": "Iris Ferreira",
        "prompt": "Cinematic portrait: Portuguese woman artist, golden hour sunlight, Lisbon rooftops background, warm terracotta tones, flowing dark hair, warm genuine smile, Mediterranean warmth, dreamy sunset glow"
    },
]


async def create_avatar_video(client: httpx.AsyncClient, agent: dict) -> str | None:
    """Create video task to get a single frame as avatar."""
    print(f"\nGenerating: {agent['name']}")
    print(f"  Prompt: {agent['prompt'][:60]}...")

    response = await client.post(
        f"{API_BASE}/contents/generations/tasks",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
        json={
            "model": VIDEO_MODEL,
            "content": [{"type": "text", "text": agent["prompt"]}],
            "resolution": "720p",
            "ratio": "1:1",  # Square for avatar
            "duration": 4,
            "watermark": False,
            "camera_fixed": True,
        },
    )

    if response.status_code != 200:
        print(f"  Error: {response.status_code}")
        print(f"  {response.text[:200]}")
        return None

    data = response.json()
    task_id = data.get("id")
    print(f"  Task: {task_id}")
    return task_id


async def get_video_result(client: httpx.AsyncClient, task_id: str) -> str | None:
    """Poll for result."""
    for attempt in range(60):
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
            print(f"  Status: {status}")

        if status == "succeeded":
            return data.get("content", {}).get("video_url")
        elif status == "failed":
            print(f"  Failed: {data.get('error')}")
            return None

    return None


async def download_and_extract_frame(client: httpx.AsyncClient, url: str, agent_id: str) -> bool:
    """Download video and save (we'll extract frame later or use video as animated avatar)."""
    response = await client.get(url)
    if response.status_code == 200:
        # Save as video - can be used as animated avatar
        filepath = ASSETS_DIR / f"{agent_id}.mp4"
        with open(filepath, "wb") as f:
            f.write(response.content)
        print(f"  Saved: {filepath}")
        return True
    return False


async def main():
    print("=" * 60)
    print("GENERATING AGENT AVATARS")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=300.0) as client:
        for agent in AGENTS:
            task_id = await create_avatar_video(client, agent)
            if not task_id:
                print(f"  FAILED: {agent['name']}")
                continue

            video_url = await get_video_result(client, task_id)
            if not video_url:
                print(f"  FAILED: {agent['name']}")
                continue

            success = await download_and_extract_frame(client, video_url, agent["id"])
            print(f"  {'SUCCESS' if success else 'FAILED'}: {agent['name']}")

            await asyncio.sleep(2)

    print("\n" + "=" * 60)
    print("DONE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
