"""Generate symbolic images: swan, shiva linga, theatre, maya."""
import httpx
import asyncio
from pathlib import Path

API_KEY = "4379a644-f5b9-4a48-9e2b-a55efafa0fcc"
API_BASE = "https://ark.ap-southeast.bytepluses.com/api/v3"
MODEL = "seedream-5-0-260128"

ASSETS_DIR = Path("/Users/abhijeet/Desktop/abhikatte.com/public/images/symbols")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


async def generate_image(prompt: str, name: str, size: str = "2K"):
    print(f"\nGenerating: {name}")
    print(f"  Prompt: {prompt[:80]}...")

    async with httpx.AsyncClient(timeout=180.0) as client:
        response = await client.post(
            f"{API_BASE}/images/generations",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}",
            },
            json={
                "model": MODEL,
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
                print(f"  Saved: {filepath}")
                return filepath

    print(f"  Failed: {name}")
    return None


async def main():
    print("=" * 60)
    print("GENERATING SYMBOLIC IMAGES")
    print("=" * 60)

    symbols = [
        {
            "name": "swan-hamsa",
            "prompt": "Minimalist sacred swan (Hamsa), elegant white swan floating on still water, lotus petals around, ancient Indian temple art style, gold and cream tones, spiritual symbolism, clean lines, meditative atmosphere, high quality illustration"
        },
        {
            "name": "shiva-linga",
            "prompt": "Sacred Shiva Linga stone, minimalist representation, ancient carved black stone with water drops, bilva leaves, marigold flowers, soft temple lamp light, spiritual Indian aesthetic, reverent atmosphere, clean composition, warm tones"
        },
        {
            "name": "theatre-natya",
            "prompt": "Ancient Indian theatre concept, Natya Shastra inspired, classical dancer silhouette with dramatic lighting, theatre masks, stage curtains, red and gold tones, performance art symbolism, elegant minimalist style, high quality illustration"
        },
        {
            "name": "maya-simulation",
            "prompt": "Maya illusion concept, Vedantic philosophy visualization, reality dissolving into geometric patterns, mirror reflections, cosmic simulation, dream within dream, blue and purple ethereal tones, abstract spiritual art, high quality digital illustration"
        },
    ]

    for symbol in symbols:
        try:
            await generate_image(
                prompt=symbol["prompt"],
                name=symbol["name"],
            )
            await asyncio.sleep(2)
        except Exception as e:
            print(f"  Error: {e}")

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
