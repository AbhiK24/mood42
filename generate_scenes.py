"""Generate complete lo-fi scenes with character included."""
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

ASSETS_DIR = Path("public/assets")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


async def generate_image(prompt: str, name: str, model: str = "seedream-5", size: str = "2K"):
    print(f"\n Generating: {name}")
    print(f"   Prompt: {prompt[:100]}...")

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
                img_response.raise_for_status()
                filepath = ASSETS_DIR / f"{name}.png"
                with open(filepath, "wb") as f:
                    f.write(img_response.content)
                print(f"   Saved: {filepath}")
                return filepath

    print(f"   Failed: {name}")
    return None


async def main():
    print("=" * 60)
    print("MOOD42 - COMPLETE SCENE GENERATION")
    print("=" * 60)

    # Generate COMPLETE scenes with character already in the scene
    scenes = [
        {
            "name": "scene_focused",
            "prompt": """
                Lo-fi anime illustration, complete scene, young South Asian woman late 20s
                sitting at desk by large window, working on laptop, wearing cream oversized sweater,
                dark hair in messy bun, NYC skyline visible through rain-streaked window at night,
                warm desk lamp casting orange glow on her face, blue laptop screen light,
                neon signs reflecting outside, cozy apartment interior, plants on windowsill,
                coffee mug steaming, focused peaceful expression, Studio Ghibli style,
                Blade Runner color grading, moody atmospheric, cinematic composition,
                high quality digital painting, lofi girl aesthetic, 4K wallpaper
            """,
            "model": "seedream-5",
        },
        {
            "name": "scene_withdrawn",
            "prompt": """
                Lo-fi anime illustration, complete scene, young South Asian woman late 20s
                sitting at desk by large window, looking tired and pensive, slumped posture,
                wearing cream oversized sweater, dark messy hair, looking away from laptop,
                NYC skyline through rain-streaked window at night, dimmer warm lamp light,
                melancholic mood, blue hour lighting, cozy but lonely apartment interior,
                coffee mug gone cold, plants on windowsill, emotional contemplative expression,
                Studio Ghibli style, moody atmospheric, soft shadows, high quality digital art
            """,
            "model": "seedream-5",
        },
    ]

    for scene in scenes:
        try:
            await generate_image(
                prompt=scene["prompt"].strip().replace("\n", " "),
                name=scene["name"],
                model=scene["model"],
            )
            await asyncio.sleep(3)
        except Exception as e:
            print(f"   Error: {e}")

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
