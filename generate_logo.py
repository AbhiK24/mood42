"""Generate mood42 logo."""
import httpx
import asyncio
from pathlib import Path

API_KEY = "4379a644-f5b9-4a48-9e2b-a55efafa0fcc"
API_BASE = "https://ark.ap-southeast.bytepluses.com/api/v3"
MODEL = "seedream-5-0-260128"

ASSETS_DIR = Path("public/assets")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

LOGO_PROMPTS = [
    {
        "name": "logo_mood42",
        "prompt": """
            Minimalist logo design, the text "mood42" in lowercase,
            modern sans-serif typeface, clean geometric letterforms,
            subtle gradient from warm amber to soft pink,
            dark background, professional brand identity,
            no icons just typography, elegant spacing,
            broadcast TV aesthetic, retro-modern hybrid,
            high contrast, vector-style clean edges,
            4K quality, centered composition
        """,
    },
    {
        "name": "logo_mood42_icon",
        "prompt": """
            Abstract minimalist icon logo, geometric shape representing
            TV screen or broadcast signal, warm amber and coral gradient,
            dark background, no text, simple memorable mark,
            could be a stylized "42" or abstract waveform,
            modern broadcast aesthetic, clean vector style,
            suitable for favicon or app icon, 4K quality
        """,
    },
]


async def generate_image(prompt: str, name: str, size: str = "1K"):
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
    print("MOOD42 - LOGO GENERATION")
    print("=" * 60)

    for item in LOGO_PROMPTS:
        try:
            await generate_image(
                prompt=item["prompt"].strip().replace("\n", " "),
                name=item["name"],
            )
            await asyncio.sleep(2)
        except Exception as e:
            print(f"  Error: {e}")

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
