from PIL import Image
import os

assets = [
    'adaptive-icon.png',
    'splash-icon.png',
    'icon.png',
    'favicon.png'
]

assets_dir = 'c:/Ideas/SikhSituationBot/mobile/assets'

for asset in assets:
    file_path = os.path.join(assets_dir, asset)
    if os.path.exists(file_path):
        print(f"Converting {asset} to valid PNG...")
        try:
            with Image.open(file_path) as img:
                # Force save as PNG regardless of current detection
                img.save(file_path, 'PNG')
            print(f"Successfully converted {asset}")
        except Exception as e:
            print(f"Error converting {asset}: {e}")
    else:
        print(f"File not found: {file_path}")
