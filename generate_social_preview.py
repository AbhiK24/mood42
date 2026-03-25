"""Generate social preview image using BytePlus."""
import httpx
import asyncio
import base64
from pathlib import Path

API_KEY = "4379a644-f5b9-4a48-9e2b-a55efafa0fcc"
API_BASE = "https://ark.ap-southeast.bytepluses.com/api/v3"

async def generate_preview():
    print("Generating social preview image...")

    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{API_BASE}/images/generations",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {API_KEY}",
            },
            json={
                "model": "seedream-3-0-t2i-250201",
                "prompt": "Minimalist dark poster design, 'mood42' text in center, ambient TV channels concept, lo-fi aesthetic, warm neon glow, purple and orange gradient, cinematic mood, clean typography, 1200x630 aspect ratio",
                "size": "1024x1024",
                "response_format": "url",
            },
        )

        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(response.text[:500])
            return

        data = response.json()
        image_url = data.get("data", [{}])[0].get("url")

        if image_url:
            print(f"Downloading from: {image_url[:50]}...")
            img_response = await client.get(image_url)
            if img_response.status_code == 200:
                output_path = Path("public/assets/social-preview.png")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "wb") as f:
                    f.write(img_response.content)
                print(f"Saved: {output_path}")
            else:
                print(f"Download failed: {img_response.status_code}")
        else:
            print("No image URL in response")
            print(data)


if __name__ == "__main__":
    asyncio.run(generate_preview())
