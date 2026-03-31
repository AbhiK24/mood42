"""Generate ishtalinga in hand."""
import httpx
import asyncio
from pathlib import Path

API_KEY = "4379a644-f5b9-4a48-9e2b-a55efafa0fcc"
API_BASE = "https://ark.ap-southeast.bytepluses.com/api/v3"
MODEL = "seedream-5-0-260128"

ASSETS_DIR = Path("/Users/abhijeet/Desktop/abhikatte.com/public/images/symbols")


async def generate_image(prompt: str, name: str, size: str = "2K"):
    print(f"\nGenerating: {name}")

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
    return None


async def main():
    style = "detailed pen and ink illustration, rich hand-drawn sketch with fine crosshatching texture, intricate linework, artistic black ink on cream paper, professional illustration quality, vintage etching style"

    prompt = f"Human hand gently holding small oval ishtalinga stone, Lingayat sacred symbol, smooth polished black stone egg shape cradled in open palm, devotional gesture, {style}"

    await generate_image(prompt, "shiva-linga")
    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
