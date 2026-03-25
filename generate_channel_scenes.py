"""Generate unique high-quality scenes for all 10 mood42 channels."""
import httpx
import asyncio
from pathlib import Path

API_KEY = "4379a644-f5b9-4a48-9e2b-a55efafa0fcc"
API_BASE = "https://ark.ap-southeast.bytepluses.com/api/v3"
MODEL = "seedream-5-0-260128"

ASSETS_DIR = Path("public/assets/channels")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Channel scene prompts - each unique to the channel's vibe
CHANNEL_SCENES = {
    "ch01_late_night": """
        Lo-fi anime illustration, young woman software engineer in her late 20s,
        sitting at desk with multiple monitors showing code, 3AM vibe,
        rain falling outside large window, city lights twinkling in distance,
        warm desk lamp casting amber glow, empty coffee cups,
        cat sleeping nearby, cozy bedroom office setup, purple and warm orange tones,
        focused peaceful coding session, Studio Ghibli meets cyberpunk aesthetic,
        atmospheric rain reflections, 4K cinematic, high quality digital painting
    """,

    "ch02_rain_cafe": """
        Lo-fi anime illustration, cozy Japanese kissaten coffee shop interior,
        rainy day outside large windows, warm wooden interior,
        vintage jazz vinyl playing, steam rising from coffee cups,
        soft warm lighting, empty seats in afternoon, rain streaks on glass,
        plants in ceramic pots, old books stacked, nostalgic atmosphere,
        Kyoto aesthetic, brown and warm amber tones, watercolor texture,
        peaceful solitude, Studio Ghibli style, 4K high quality
    """,

    "ch03_jazz_noir": """
        Film noir aesthetic, 1950s Chicago jazz club at night,
        smoky atmospheric interior, dim blue and amber lighting,
        saxophone silhouette on small stage, empty tables with drinks,
        rain visible through frosted windows, detective novel mood,
        art deco elements, shadows and light play, mysterious and beautiful,
        classic noir cinematography, black and blue and amber palette,
        lonely but romantic atmosphere, 4K cinematic quality
    """,

    "ch04_synthwave": """
        Synthwave retro-futuristic landscape, neon pink and cyan grid,
        endless sunset over digital ocean, chrome sports car on highway,
        geometric mountains in distance, palm trees silhouette,
        1985 retrofuture aesthetic, VHS scan lines subtle,
        chrome and neon reflections, outrun style,
        purple orange magenta gradient sky, perfect geometric lines,
        no people just pure aesthetic, 4K wallpaper quality
    """,

    "ch05_deep_space": """
        Deep space cosmic landscape, nebula clouds in purple and blue,
        distant stars and galaxies, radio telescope array silhouette,
        vast empty beautiful void, sense of infinite scale,
        dark ambient atmosphere, New Mexico desert meets cosmos,
        extremely dark with subtle color, astronomical photography style,
        transcendent peaceful, no text no people just space,
        4K ultra high detail, NASA aesthetic meets art
    """,

    "ch06_tokyo_drift": """
        Tokyo street at night after rain, neon signs reflecting on wet asphalt,
        empty Shinjuku alley, vending machines glowing,
        taxi cab waiting, city pop aesthetic, steam rising from grates,
        Japanese text on signs, pink and cyan neon,
        cinematic night photography, moody urban atmosphere,
        Blade Runner meets Lost in Translation, 4K quality,
        lonely but beautiful city night
    """,

    "ch07_sunday_morning": """
        Peaceful morning scene, sunlight streaming through window,
        Vermont farmhouse interior, plants everywhere,
        coffee steam catching golden light, garden visible outside,
        warm golden hour lighting, white curtains flowing,
        acoustic guitar leaning on chair, books and fresh flowers,
        hopeful new beginning atmosphere, pastoral and serene,
        watercolor soft edges, Studio Ghibli countryside style, 4K
    """,

    "ch08_focus": """
        Minimalist modern workspace, clean Scandinavian design,
        Copenhagen architect studio, white walls and birch wood,
        single plant, perfect geometric furniture placement,
        diffused natural light, no clutter absolute clarity,
        bauhaus aesthetic, focus and calm,
        white grey and light wood palette, architectural precision,
        zen productivity space, ultra clean 4K quality
    """,

    "ch09_melancholy": """
        Rainy London evening, view through apartment window,
        empty room with single lamp, books scattered,
        grey blue melancholic atmosphere, beautiful sadness,
        writer's room aesthetic, typewriter or notebook visible,
        Brixton apartment view, streetlights in rain,
        contemplative lonely but not depressing,
        Edward Hopper meets lo-fi, muted colors, 4K cinematic
    """,

    "ch10_golden_hour": """
        Golden hour sunset in Lisbon, view over terracotta rooftops,
        azulejo tiles catching warm light, Atlantic ocean in distance,
        Alfama neighborhood, warm orange and gold everywhere,
        laundry on lines catching light, photographer's paradise,
        nostalgic warm ending of day, birds silhouette,
        Portuguese tiles reflecting sunset, dreamlike warmth,
        magical hour atmosphere, 4K golden light photography
    """,
}


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
    print("MOOD42 - CHANNEL SCENE GENERATION")
    print("=" * 60)

    for name, prompt in CHANNEL_SCENES.items():
        try:
            await generate_image(
                prompt=prompt.strip().replace("\n", " "),
                name=name,
            )
            await asyncio.sleep(3)  # Rate limiting
        except Exception as e:
            print(f"  Error generating {name}: {e}")

    print("\n" + "=" * 60)
    print("DONE! Images saved to public/assets/channels/")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
