"""Generate remaining assets."""
import httpx
import asyncio
from pathlib import Path

API_KEY = "4379a644-f5b9-4a48-9e2b-a55efafa0fcc"
API_BASE = "https://ark.ap-southeast.bytepluses.com/api/v3"
MODELS = {
    "seedream-3": "seedream-3-0-t2i-250415",
    "seedream-4": "seedream-4-0-250828",
    "seedream-5": "seedream-5-0-260128",
}

ASSETS_DIR = Path("assets")


async def generate_image(prompt: str, name: str, model: str = "seedream-4", size: str = "2K"):
    print(f"\n🎨 Generating: {name}")

    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{API_BASE}/images/generations",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}",
            },
            json={
                "model": MODELS[model],
                "prompt": prompt,
                "size": size,
                "response_format": "url",
                "watermark": False,
            },
        )
        response.raise_for_status()
        data = response.json()

        if data.get("data") and len(data["data"]) > 0:
            url = data["data"][0].get("url")
            if url:
                img_response = await client.get(url)
                filepath = ASSETS_DIR / f"{name}.png"
                with open(filepath, "wb") as f:
                    f.write(img_response.content)
                print(f"   ✓ Saved: {filepath}")
                return filepath
    return None


async def main():
    assets = [
        {
            "name": "character_withdrawn",
            "prompt": "Lo-fi anime illustration of a young South Asian woman, late 20s, sitting at desk looking tired and pensive, slumped shoulders, wearing cream sweater, dark hair in messy bun, looking away from screen, warm dim lamp lighting, melancholic mood, Studio Ghibli style, high quality digital art",
            "model": "seedream-5",
            "size": "2K",
        },
        {
            "name": "character_floor",
            "prompt": "Lo-fi anime illustration of a young South Asian woman sitting on floor against desk, knees up, head resting on arms, tired exhausted pose, wearing oversized sweater, dark moody lighting, emotional scene, Studio Ghibli style, high quality",
            "model": "seedream-4",
            "size": "2K",
        },
    ]

    for asset in assets:
        try:
            await generate_image(
                prompt=asset["prompt"],
                name=asset["name"],
                model=asset["model"],
                size=asset["size"],
            )
            await asyncio.sleep(2)
        except Exception as e:
            print(f"   Error: {e}")

    print("\n✓ Done!")


if __name__ == "__main__":
    asyncio.run(main())
