"""Generate symbolic images in jzhao.xyz hand-drawn line art style."""
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
    print("GENERATING SYMBOLIC IMAGES - LINE ART STYLE")
    print("=" * 60)

    # Style reference: jzhao.xyz - minimalist hand-drawn black line art on white/cream background
    style = "minimalist hand-drawn black ink line art illustration, simple sketch style, clean white background, single continuous line drawing, zen aesthetic, no shading, no color, pen and ink style"

    symbols = [
        {
            "name": "swan-hamsa",
            "prompt": f"Swan bird Hamsa, elegant curved neck, floating on water with lotus, {style}"
        },
        {
            "name": "shiva-linga",
            "prompt": f"Shiva lingam stone on yoni base, simple sacred geometry, temple symbol, {style}"
        },
        {
            "name": "theatre-natya",
            "prompt": f"Theatre masks comedy and tragedy, stage curtains, performance art symbol, {style}"
        },
        {
            "name": "maya-simulation",
            "prompt": f"Infinite mirrors reflecting each other, recursive pattern, illusion concept, dream within dream, {style}"
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
