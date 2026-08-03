#!/usr/bin/env python
"""Build a PZ-compatible Bob_MateSip.x from the manually baked Blender export.

The Blender DirectX exporter writes the complete control rig.  Project Zomboid only
needs the deform-bone animation blocks, so this script combines those blocks with a
known-good vanilla Bob skeleton.
"""

from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "art-3d" / "manual-animation-export" / "Bob_MateSip_fullrig.x"
VANILLA = Path(r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid\media\anims_X\Bob\Bob_DrinkFromBottle.x")
OUTPUT = ROOT / "Contents" / "mods" / "MateArgentino" / "42" / "media" / "anims_X" / "Bob" / "Bob_MateSip.x"

WANTED = [
    "Bip01_Spine",
    "Bip01_Spine1",
    "Bip01_Neck",
    "Bip01_Head",
    "Bip01_L_Clavicle",
    "Bip01_L_UpperArm",
    "Bip01_L_Forearm",
    "Bip01_L_Hand",
    "Bip01_L_Finger0",
    "Bip01_L_Finger1",
    "Bip01_Prop2",
]


def balanced_block(text: str, start: int) -> tuple[str, int]:
    """Return the brace-balanced block starting at an `Animation {` token."""
    brace = text.find("{", start)
    if brace < 0:
        raise ValueError("Bloque sin llave de apertura")
    depth = 0
    for pos in range(brace, len(text)):
        if text[pos] == "{":
            depth += 1
        elif text[pos] == "}":
            depth -= 1
            if depth == 0:
                return text[start : pos + 1], pos + 1
    raise ValueError("Bloque sin llave de cierre")


def animation_blocks(text: str, set_name: str | None = None) -> dict[str, str]:
    wanted_name = re.escape(set_name) if set_name else r"[A-Za-z0-9_]+"
    marker = re.search(rf"^AnimationSet\s+{wanted_name}\s*\{{", text, re.MULTILINE)
    if not marker:
        raise ValueError("No se encontro AnimationSet")
    cursor = marker.end()
    blocks: dict[str, str] = {}
    token = re.compile(r"(?m)^\s*Animation\s*\{")
    while match := token.search(text, cursor):
        block, cursor = balanced_block(text, match.start())
        target = re.search(r"\{\s*([A-Za-z0-9_]+)\s*\}", block)
        if not target:
            raise ValueError("Animation sin hueso objetivo")
        blocks[target.group(1)] = block.strip()
    return blocks


def key_block(block: str, kind: str) -> tuple[int, int, str]:
    match = re.search(rf"AnimationKey\s+{kind}\s*\{{", block)
    if not match:
        raise ValueError(f"No se encontro AnimationKey {kind}")
    value, end = balanced_block(block, match.start())
    return match.start(), end, value


def replace_key(block: str, kind: str, replacement: str) -> str:
    start, end, _ = key_block(block, kind)
    return block[:start] + replacement + block[end:]


def sanitized_block(bone: str, baked: str, vanilla: str) -> str:
    """Keep baked rotations, but prevent Blender scale/translation distortion."""
    scale = (
        "AnimationKey S {\n"
        "\t\t\t1;\n"
        "\t\t\t2;\n"
        "\t\t\t0;3;1.000000,1.000000,1.000000;;,\n"
        "\t\t\t19840;3;1.000000,1.000000,1.000000;;;\n"
        "\t\t}"
    )
    result = replace_key(baked, "S", scale)
    if bone != "Bip01_Prop2":
        # Evaluated Blender control matrices contain moving translations caused by
        # constraints/shear. PZ interprets those as bone lengths and stretches the
        # character. Use the stable rest translation from a vanilla clip instead.
        _, _, vanilla_translation = key_block(vanilla, "T")
        vanilla_translation = re.sub(
            r"(?m)^(\s*)\d+(;3;[^\r\n]+;;;\s*)$",
            r"\g<1>19840\g<2>",
            vanilla_translation,
            count=1,
        )
        result = replace_key(result, "T", vanilla_translation)
    return result


def main() -> None:
    source_text = SOURCE.read_text(encoding="utf-8-sig")
    vanilla_text = VANILLA.read_text(encoding="utf-8-sig")
    blocks = animation_blocks(source_text, "Bob_MateSip")
    vanilla_blocks = animation_blocks(vanilla_text)
    missing = [bone for bone in WANTED if bone not in blocks]
    if missing:
        raise ValueError(f"Faltan bloques: {', '.join(missing)}")
    missing_vanilla = [bone for bone in WANTED if bone not in vanilla_blocks]
    if missing_vanilla:
        raise ValueError(f"Faltan bloques vanilla: {', '.join(missing_vanilla)}")

    marker = re.search(r"^AnimationSet\s+", vanilla_text, re.MULTILINE)
    if not marker:
        raise ValueError("El archivo vanilla no contiene AnimationSet")
    prefix = vanilla_text[: marker.start()].rstrip()
    # Remove only the concrete data block at the tail, preserving its template.
    prefix, count = re.subn(
        r"AnimTicksPerSecond\s*\{\s*\d+\s*;\s*\}\s*$", "", prefix, count=1
    )
    if count != 1:
        raise ValueError("No se pudo reemplazar AnimTicksPerSecond vanilla")

    selected = "\n\n".join(
        sanitized_block(bone, blocks[bone], vanilla_blocks[bone]) for bone in WANTED
    )
    output_text = (
        prefix.rstrip()
        + "\n\nAnimTicksPerSecond {\n 4800;\n}\n\n"
        + "AnimationSet Bob_MateSip {\n"
        + selected
        + "\n}\n"
    )
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(output_text, encoding="utf-8", newline="\n")
    print(f"Generado: {OUTPUT}")
    print(f"Bloques: {len(WANTED)} ({', '.join(WANTED)})")


if __name__ == "__main__":
    main()
