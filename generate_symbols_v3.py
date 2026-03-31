"""Generate symbolic images - rich hand-drawn style like jzhao.xyz."""
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
    print("GENERATING SYMBOLS - RICH HAND-DRAWN STYLE")
    print("=" * 60)

    # Rich hand-drawn style with texture, cross-hatching, fine pen work
    style = "detailed pen and ink illustration, rich hand-drawn sketch with fine crosshatching texture, intricate linework, artistic black ink on cream paper, professional illustration quality, single centered object, no background elements, vintage etching style"

    symbols = [
        {
            "name": "swan-hamsa",
            "prompt": f"Single elegant swan bird swimming, graceful curved S-neck, detailed feather texture, {style}"
        },
        {
            "name": "shiva-linga",
            "prompt": f"Single smooth oval stone Lingayat ishtalinga, formless sacred egg shape, simple polished ovoid form worn by devotees, {style}"
        },
        {
            "name": "theatre-natya",
            "prompt": f"Single classical theatre mask, dramatic expression, ancient Greek or Indian Natya style, {style}"
        },
        {
            "name": "maya-simulation",
            "prompt": f"Single ornate mirror frame with infinite reflection inside, recursive depth illusion, {style}"
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
