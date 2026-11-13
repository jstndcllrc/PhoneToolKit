#!/usr/bin/env python3
"""Generate a proper Windows ICO file for PhoneToolKit"""
from PIL import Image, ImageDraw
from pathlib import Path

# Create a proper ICO with multiple sizes
img = Image.new('RGBA', (256, 256), (0, 0, 0, 0))
draw = ImageDraw.Draw(img)

# Background - blue rounded rect
draw.rounded_rectangle([0, 0, 255, 255], radius=32, fill=(25, 118, 210, 255))

# Phone body
draw.rounded_rectangle([88, 32, 168, 224], radius=16, fill=(255, 255, 255, 255), outline=(25, 118, 210, 255), width=2)

# Screen
draw.rounded_rectangle([96, 44, 160, 196], radius=8, fill=(13, 71, 161, 255))

# Shield icon on screen
shield_points = [(128, 75), (128, 90), (148, 105), (128, 120), (108, 105)]
draw.polygon(shield_points, outline=(79, 195, 247, 255), width=3)
draw.line([(128, 90), (128, 120)], fill=(79, 195, 247, 255), width=2)
draw.line([(108, 105), (148, 105)], fill=(79, 195, 247, 255), width=2)

# Tool icons at bottom
draw.ellipse([88, 200, 112, 224], fill=(255, 243, 224, 255), outline=(255, 152, 0, 255), width=2)

draw.ellipse([144, 200, 168, 224], fill=(232, 245, 233, 255), outline=(76, 175, 80, 255), width=2)

# Save as ICO with multiple sizes
ico_sizes = [(16,16), (24,24), (32,32), (48,48), (64,64), (128,128), (256,256)]
out_dir = Path(__file__).resolve().parent / "resources"
out_dir.mkdir(parents=True, exist_ok=True)
out_file = out_dir / "icon.ico"
img.save(str(out_file), format='ICO', sizes=ico_sizes)
print(f'Created proper ICO file at {out_file}')