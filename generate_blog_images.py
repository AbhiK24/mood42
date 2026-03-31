"""Generate blog post hero images using ByteDance Seedream API."""
import httpx
import asyncio
from pathlib import Path

API_KEY = "4379a644-f5b9-4a48-9e2b-a55efafa0fcc"
API_BASE = "https://ark.ap-southeast.bytepluses.com/api/v3"
MODEL = "seedream-5-0-260128"

ASSETS_DIR = Path("/Users/abhijeet/Desktop/abhikatte.com/public/images")
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
                filepath = ASSETS_DIR / f"{name}.jpg"
                with open(filepath, "wb") as f:
                    f.write(img_response.content)
                print(f"  Saved: {filepath}")
                return filepath

    print(f"  Failed: {name}")
    return None


async def main():
    print("=" * 60)
    print("GENERATING BLOG POST IMAGES")
    print("=" * 60)

    posts = [
        {
            "name": "ai-capitalism",
            "prompt": "Abstract digital art, ghost of Karl Marx watching over modern silicon valley tech campus, red and blue neon lights, servers and data centers, capitalism meets communism symbolism, moody atmospheric, cinematic lighting, conceptual illustration, high quality"
        },
        {
            "name": "biases-in-ai",
            "prompt": "Abstract digital art, human face made of circuit patterns with cracks showing different skin tones underneath, algorithmic bias visualization, data flowing around, neural network patterns, warm and cool tones contrasting, conceptual tech illustration, moody atmospheric"
        },
        {
            "name": "biology-math",
            "prompt": "Abstract scientific illustration, DNA double helix intertwined with mathematical equations and geometric patterns, fibonacci spirals, microscopic cells merging with calculus symbols, soft blue and green bioluminescent glow, conceptual art, high quality digital painting"
        },
        {
            "name": "books-reading",
            "prompt": "Cozy lo-fi illustration, stack of old worn books on wooden desk by window, warm lamp light, reading glasses, coffee cup steaming, rain outside, peaceful contemplative mood, Studio Ghibli inspired, soft warm colors, digital art"
        },
        {
            "name": "france-ai-strategy",
            "prompt": "Abstract digital art, Eiffel Tower silhouette integrated with neural network nodes and AI circuits, French tricolor subtle in background, futuristic Paris skyline, tech innovation symbolism, elegant sophisticated style, blue and gold tones, conceptual illustration"
        },
        {
            "name": "market-lemons",
            "prompt": "Conceptual illustration, split image of shiny new car and rusted lemon car, information asymmetry visualization, buyer and seller silhouettes, economic charts in background, vintage economics textbook style, muted yellows and grays, editorial illustration"
        },
        {
            "name": "random-musings",
            "prompt": "Abstract lo-fi illustration, scattered thoughts visualization, floating geometric shapes, mathematical symbols, neural patterns, brain silhouette with ideas flowing out, soft purple and blue gradient, contemplative mood, digital art, minimal aesthetic"
        },
        {
            "name": "social-cue-factory",
            "prompt": "Surreal conceptual art, factory assembly line producing identical human silhouettes, some figures breaking free from conveyor belt, conformity vs individuality theme, industrial meets human, warm orange factory glow vs cool blue freedom, thought-provoking illustration"
        },
    ]

    for post in posts:
        try:
            await generate_image(
                prompt=post["prompt"],
                name=post["name"],
            )
            await asyncio.sleep(2)
        except Exception as e:
            print(f"  Error: {e}")

    print("\n" + "=" * 60)
    print("DONE!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
