import json
import re
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
VERSION_ROOT = ROOT / "Contents" / "mods" / "MateArgentino" / "42"
MEDIA = VERSION_ROOT / "media"
MAX_CEBADAS = 40


def check_balanced_braces(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    depth = 0
    for line_number, line in enumerate(text.splitlines(), start=1):
        line = line.split("//", 1)[0]
        depth += line.count("{") - line.count("}")
        if depth < 0:
            raise AssertionError(f"{path}:{line_number}: cierre inesperado")
    assert depth == 0, f"{path}: llaves desbalanceadas ({depth})"


def main() -> None:
    required_files = [
        VERSION_ROOT / "mod.info",
        VERSION_ROOT / "poster.png",
        ROOT / "preview.png",
        MEDIA / "scripts" / "MateArgentino_Items.txt",
        MEDIA / "scripts" / "MateArgentino_Recipes.txt",
        MEDIA / "scripts" / "MateArgentino_Fluids.txt",
        MEDIA / "scripts" / "MateArgentino_Models.txt",
        MEDIA / "scripts" / "MateArgentino_Sounds.txt",
        MEDIA / "sound" / "MateArgentino_RuidoMate.mp3",
        MEDIA / "lua" / "client" / "MateArgentino_ContextMenu.lua",
        MEDIA / "lua" / "client" / "MateArgentino_TermoTemperatura.lua",
        MEDIA / "lua" / "server" / "Items" / "MateArgentino_Distributions.lua",
    ]
    for path in required_files:
        assert path.is_file(), f"Falta {path}"

    for path in (MEDIA / "scripts").glob("*.txt"):
        check_balanced_braces(path)
    for path in (MEDIA / "lua" / "shared" / "Translate").rglob("*.json"):
        value = json.loads(path.read_text(encoding="utf-8"))
        assert isinstance(value, dict) and value, f"Traducción vacía: {path}"

    item_text = (MEDIA / "scripts" / "MateArgentino_Items.txt").read_text(
        encoding="utf-8"
    )
    recipe_text = (MEDIA / "scripts" / "MateArgentino_Recipes.txt").read_text(
        encoding="utf-8"
    )
    declared = set(re.findall(r"^\s*item\s+(\w+)\s*$", item_text, re.MULTILINE))

    required_items = {
        "Yerba",
        "YerbaEconomica",
        "YerbaMedia",
        "YerbaPremium",
        "MateVacio",
        "MateLavado",
        "Termo",
        *{f"MateConYerba{n}" for n in range(1, MAX_CEBADAS + 1)},
        *{f"MatePreparado{n}" for n in range(1, MAX_CEBADAS + 1)},
        *{f"MatePreparadoCaliente{n}" for n in range(1, MAX_CEBADAS + 1)},
    }
    assert required_items <= declared, "Faltan objetos del ciclo de mate"

    for count in range(1, MAX_CEBADAS + 1):
        mapper = (
            f"MateArgentino.MatePreparado{count} = "
            f"MateArgentino.MateConYerba{count}"
        )
        assert mapper in recipe_text, f"Falta mapper: {mapper}"
        hot_mapper = (
            f"MateArgentino.MatePreparadoCaliente{count} = "
            f"MateArgentino.MateConYerba{count}"
        )
        assert hot_mapper in recipe_text, f"Falta mapper caliente: {hot_mapper}"

    ranges = {"Economica": (10, 15), "Media": (15, 25), "Premium": (25, 40)}
    for quality, (minimum, maximum) in ranges.items():
        for count in range(minimum, maximum + 1):
            item_id = f"Yerba{quality}{count}"
            assert item_id in declared, f"Falta variante {item_id}"
            mapper = (
                f"MateArgentino.MateConYerba{count} = "
                f"MateArgentino.{item_id}"
            )
            assert mapper in recipe_text, f"Falta mapper: {mapper}"

    assert "item 1 [MateArgentino.Termo] mode:keep flags[NotEmpty;Prop1]" in recipe_text
    assert "-fluid 0.045 [Water]" in recipe_text
    assert "-fluid 0.045 [HotWater]" in recipe_text
    assert "Eattime = 160" not in item_text
    assert "CustomEatSound = MateArgentino_RuidoMate" not in item_text
    assert item_text.count("CustomDrinkSound = MateArgentino_RuidoMate") == MAX_CEBADAS * 2
    assert item_text.count("Capacity = 0.045") == MAX_CEBADAS * 2
    assert item_text.count("fluid = MateInfusion:0.045") == MAX_CEBADAS
    assert item_text.count("fluid = MateInfusionHot:0.045") == MAX_CEBADAS
    assert "Tags = base:cookable" in item_text
    def count_hand_model(model_name: str) -> int:
        pattern = (
            rf"^\s*StaticModel\s*=\s*"
            rf"MateArgentino\.MateArgentino_{model_name},\s*$"
        )
        return len(re.findall(pattern, item_text, re.MULTILINE))

    assert count_hand_model("MateVacio3D") == 1
    assert count_hand_model("MateConYerba3D") == MAX_CEBADAS
    assert count_hand_model("MatePreparado3D") == MAX_CEBADAS * 2
    assert count_hand_model("MateLavado3D") == 1
    assert count_hand_model("Termo3D") == 1

    fluids_text = (MEDIA / "scripts" / "MateArgentino_Fluids.txt").read_text(
        encoding="utf-8"
    )
    assert "fluid HotWater" in fluids_text
    assert "fluid MateInfusion" in fluids_text
    assert "fluid MateInfusionHot" in fluids_text
    assert "fatigueChange = -177.778" in fluids_text
    assert "Fluid_Name_MateArgentino_HotWater" in fluids_text

    sound_text = (MEDIA / "scripts" / "MateArgentino_Sounds.txt").read_text(
        encoding="utf-8"
    )
    assert "sound MateArgentino_RuidoMate" in sound_text
    assert "loop = true" in sound_text
    assert "file = media/sound/MateArgentino_RuidoMate.mp3" in sound_text
    assert (MEDIA / "sound" / "MateArgentino_RuidoMate.mp3").stat().st_size > 0

    context_text = (
        MEDIA / "lua" / "client" / "MateArgentino_ContextMenu.lua"
    ).read_text(encoding="utf-8")
    assert "DrinkThird" not in context_text
    assert "MatePreparadoCaliente" in context_text
    assert "recoverEmptyMates" in context_text
    assert "fluidContainer:getAmount() <= EMPTY_THRESHOLD" in context_text
    assert "Events.OnTick.Add(recoverPlayerMates)" in context_text
    assert "ISInventoryPaneContextMenu.onDrinkFluid" not in context_text

    temperature_text = (
        MEDIA / "lua" / "client" / "MateArgentino_TermoTemperatura.lua"
    ).read_text(encoding="utf-8")
    assert 'Fluid.Get("HotWater")' in temperature_text
    assert "item:getItemHeat() > HOT_THRESHOLD" in temperature_text
    assert "local INSULATION_HOURS = 24" in temperature_text
    assert "now + INSULATION_HOURS" in temperature_text
    assert "Events.OnTick.Add(updatePlayerTermos)" in temperature_text

    for icon_name in (
        "MateVacio",
        "MatePreparado",
        "MateLavado",
        "Termo",
        "Yerba",
        "YerbaMedia",
        "YerbaPremium",
    ):
        path = MEDIA / "textures" / f"Item_{icon_name}.png"
        with Image.open(path) as image:
            assert image.size == (64, 64), f"Tamaño incorrecto: {path}"
            assert image.mode == "RGBA", f"Falta alfa: {path}"
            assert image.getchannel("A").getbbox(), f"Icono vacío: {path}"

    mod_info = (VERSION_ROOT / "mod.info").read_text(encoding="utf-8")
    model_prefix = "WorldStaticModel = MateArgentino.MateArgentino_"
    assert item_text.count(model_prefix + "YerbaEconomica3D") == 8
    assert item_text.count(model_prefix + "YerbaMedia3D") == 12
    assert item_text.count(model_prefix + "YerbaPremium3D") == 17
    assert item_text.count(model_prefix + "MateVacio3D") == 1
    assert item_text.count(model_prefix + "MateConYerba3D") == 40
    assert item_text.count(model_prefix + "MatePreparado3D") == 80
    assert item_text.count(model_prefix + "MateLavado3D") == 1
    assert item_text.count(model_prefix + "Termo3D") == 1
    assert "WorldStaticModel = MateArgentino_Mate" not in item_text

    models_text = (MEDIA / "scripts" / "MateArgentino_Models.txt").read_text(
        encoding="utf-8"
    )
    model_names = (
        "MateVacio3D",
        "MateConYerba3D",
        "MatePreparado3D",
        "MateLavado3D",
        "Termo3D",
        "YerbaEconomica3D",
        "YerbaMedia3D",
        "YerbaPremium3D",
    )
    for model_name in model_names:
        assert f"model MateArgentino_{model_name}" in models_text
        model_path = MEDIA / "models_X" / "MateArgentino" / f"{model_name}.fbx"
        texture_path = MEDIA / "textures" / "MateArgentino" / f"{model_name}.png"
        assert model_path.stat().st_size > 1000, f"FBX inválido: {model_path}"
        with Image.open(texture_path) as image:
            assert image.size == (128, 128), f"Textura inválida: {texture_path}"

    assert models_text.count("scale = 0.0024,") == 4
    assert "scale = 0.0033," in models_text
    assert models_text.count("scale = 0.005,") == 3
    assert "modversion=0.8.0" in mod_info
    print("OK: mecánica, audio, iconos y modelos 3D de suelo validados")


if __name__ == "__main__":
    main()
