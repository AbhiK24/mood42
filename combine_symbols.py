"""Combine 4 symbols into horizontal strip."""
from PIL import Image
from pathlib import Path

SYMBOLS_DIR = Path("/Users/abhijeet/Desktop/abhikatte.com/public/images/symbols")
OUTPUT = Path("/Users/abhijeet/Desktop/abhikatte.com/public/images/symbols-strip.png")

# Load all 4 images
images = [
    Image.open(SYMBOLS_DIR / "swan-hamsa.png"),
    Image.open(SYMBOLS_DIR / "shiva-linga.png"),
    Image.open(SYMBOLS_DIR / "theatre-natya.png"),
    Image.open(SYMBOLS_DIR / "maya-simulation.png"),
]

# Resize to same height (use smallest height)
target_height = 200
resized = []
for img in images:
    ratio = target_height / img.height
    new_width = int(img.width * ratio)
    resized.append(img.resize((new_width, target_height), Image.Resampling.LANCZOS))

# Calculate total width
total_width = sum(img.width for img in resized)
gap = 20  # gap between images
total_width += gap * (len(resized) - 1)

# Create new image with cream background
strip = Image.new('RGB', (total_width, target_height), (249, 247, 242))

# Paste images
x = 0
for img in resized:
    # Convert to RGB if needed
    if img.mode == 'RGBA':
        bg = Image.new('RGB', img.size, (249, 247, 242))
        bg.paste(img, mask=img.split()[3])
        img = bg
    strip.paste(img, (x, 0))
    x += img.width + gap

strip.save(OUTPUT, quality=95)
print(f"Saved: {OUTPUT}")
print(f"Size: {strip.width}x{strip.height}")
