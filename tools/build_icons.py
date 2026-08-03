from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "art-transparent"
TEXTURES = (
    ROOT
    / "Contents"
    / "mods"
    / "MateArgentino"
    / "42"
    / "media"
    / "textures"
)
MOD_ROOT = ROOT / "Contents" / "mods" / "MateArgentino" / "42"


def fit_transparent(source: Path, destination: Path, size: int, padding: int) -> None:
    image = Image.open(source).convert("RGBA")
    alpha_box = image.getchannel("A").getbbox()
    if alpha_box is None:
        raise ValueError(f"{source} no contiene píxeles visibles")

    image = image.crop(alpha_box)
    target = size - (padding * 2)
    image.thumbnail((target, target), Image.Resampling.LANCZOS)

    canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    x = (size - image.width) // 2
    y = (size - image.height) // 2
    canvas.alpha_composite(image, (x, y))
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination, optimize=True)


def main() -> None:
    icon_sources = {
        "Item_MateVacio.png": SOURCE / "MateVacio.png",
        "Item_MatePreparado.png": SOURCE / "MatePreparado.png",
        "Item_MateLavado.png": SOURCE / "MateLavado.png",
        "Item_Termo.png": SOURCE / "Termo.png",
        "Item_Yerba.png": SOURCE / "Yerba.png",
        "Item_YerbaMedia.png": SOURCE / "YerbaMedia.png",
        "Item_YerbaPremium.png": SOURCE / "YerbaPremium.png",
    }

    for filename, source in icon_sources.items():
        fit_transparent(source, TEXTURES / filename, size=64, padding=4)

    fit_transparent(SOURCE / "MatePreparado.png", MOD_ROOT / "poster.png", 256, 18)
    fit_transparent(SOURCE / "MatePreparado.png", ROOT / "preview.png", 256, 18)


if __name__ == "__main__":
    main()
