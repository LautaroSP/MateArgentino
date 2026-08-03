from pathlib import Path

from PIL import Image


root = Path(__file__).resolve().parents[1]
preview = root / "art-3d" / "animation-preview"
frames = sorted((preview / "frames").glob("frame_*.png"))
if not frames:
    raise SystemExit("No rendered frames found")

images = [Image.open(path).convert("RGB") for path in frames]
destination = preview / "mate_sip_preview.gif"
images[0].save(
    destination,
    save_all=True,
    append_images=images[1:],
    duration=33,
    loop=0,
    optimize=False,
)
for image in images:
    image.close()
print(destination)
