"""Generate lo-fi scene assets using BytePlus Seedream."""
import httpx
import asyncio
import os
from pathlib import Path

API_KEY = "4379a644-f5b9-4a48-9e2b-a55efafa0fcc"
API_BASE = "https://ark.ap-southeast.bytepluses.com/api/v3"
MODELS = {
    "seedream-3": "seedream-3-0-t2i-250415",
    "seedream-4": "seedream-4-0-250828",
    "seedream-5": "seedream-5-0-260128",
}

ASSETS_DIR = Path("assets")
ASSETS_DIR.mkdir(exist_ok=True)


async def generate_image(prompt: str, name: str, model: str = "seedream-4", size: str = "2K"):
    """Generate an image and save it."""
    print(f"\n🎨 Generating: {name}")
    print(f"   Prompt: {prompt[:80]}...")

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
                # Download the image
                img_response = await client.get(url)
                img_response.raise_for_status()

                filepath = ASSETS_DIR / f"{name}.png"
                with open(filepath, "wb") as f:
                    f.write(img_response.content)

                print(f"   ✓ Saved: {filepath}")
                return filepath

    print(f"   ✗ Failed to generate {name}")
    return None


async def main():
    print("=" * 60)
    print("MOOD42 ASSET GENERATION")
    print("Generating lo-fi scene assets with Seedream")
    print("=" * 60)

    # Define all the assets we need
    assets = [
        # Main scene background - NYC window at night
        {
            "name": "scene_background",
            "prompt": """
                Lo-fi anime style illustration, cozy apartment interior at night,
                large window showing NYC skyline with rain, neon lights reflecting,
                warm lamp glow inside, desk area visible, moody atmospheric lighting,
                Studio Ghibli inspired background art, Blade Runner color grading,
                deep blues and warm oranges, cinematic composition,
                high quality digital painting, 4K wallpaper quality
            """,
            "model": "seedream-5",
            "size": "2K",
        },
        # Character - South Asian woman at desk
        {
            "name": "character_focused",
            "prompt": """
                Lo-fi anime illustration of a young South Asian woman, late 20s,
                sitting at desk working on laptop, wearing oversized sweater,
                dark hair in loose bun with strands falling,
                warm lamp light illuminating her face, blue laptop glow,
                focused expression, cozy study vibes,
                Studio Ghibli character style, soft shadows,
                high quality digital art, lofi girl aesthetic
            """,
            "model": "seedream-5",
            "size": "2K",
        },
        # Character variant - withdrawn/tired pose
        {
            "name": "character_withdrawn",
            "prompt": """
                Lo-fi anime illustration of a young South Asian woman, late 20s,
                sitting at desk looking tired, slumped shoulders,
                wearing oversized sweater, dark hair messy,
                looking away from laptop screen, pensive expression,
                warm dim lighting, melancholic mood,
                Studio Ghibli character style, emotional,
                high quality digital art
            """,
            "model": "seedream-4",
            "size": "2K",
        },
        # City skyline layer
        {
            "name": "city_skyline",
            "prompt": """
                NYC skyline silhouette at night, rain falling,
                Empire State building visible, lit windows in buildings,
                one warm window light standing out,
                deep blue sky with rain clouds,
                neon signs reflecting in wet surfaces,
                Blade Runner inspired color palette,
                atmospheric perspective, moody night scene,
                digital matte painting style
            """,
            "model": "seedream-4",
            "size": "2K",
        },
        # Rain overlay
        {
            "name": "rain_layer",
            "prompt": """
                Rain drops on window glass, condensation,
                water streaks running down, bokeh effect,
                night city lights blurred through rain,
                shallow depth of field, macro photography style,
                moody atmospheric, cinematic look,
                transparent PNG style composition on dark background
            """,
            "model": "seedream-3",
            "size": "1K",
        },
        # Desk setup close-up
        {
            "name": "desk_objects",
            "prompt": """
                Lo-fi anime style desk setup illustration,
                laptop open with blue screen glow,
                coffee mug with steam rising,
                stack of books, potted plant,
                warm lamp light, cozy study aesthetic,
                Studio Ghibli object design,
                soft shadows, detailed props,
                high quality digital painting
            """,
            "model": "seedream-4",
            "size": "2K",
        },
        # Neon glow effect
        {
            "name": "neon_glow",
            "prompt": """
                Neon sign glow effect, red and blue neon lights,
                OPEN sign, atmospheric light bloom,
                rain reflections, wet surface reflections,
                cyberpunk inspired, Blade Runner aesthetic,
                light rays through rain, volumetric lighting,
                dark background with colored light sources
            """,
            "model": "seedream-3",
            "size": "1K",
        },
    ]

    # Generate all assets
    for asset in assets:
        await generate_image(
            prompt=asset["prompt"].strip().replace("\n", " "),
            name=asset["name"],
            model=asset["model"],
            size=asset["size"],
        )
        await asyncio.sleep(1)  # Rate limiting

    print("\n" + "=" * 60)
    print("DONE! Assets saved to ./assets/")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
