#!/usr/bin/env python
"""Genera Bob_MateSip.x usando el brazo izquierdo vanilla.

El clip conserva Prop2 fijado a la mano: sus canales de rotacion y traslacion
se muestrean juntos desde Bob_DrinkFromTeacup. No anima torso, brazo derecho ni
tren inferior.
"""
import re
import sys
from pathlib import Path

import export_mate_sip_x as base


SOURCE = Path(
    r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid"
    r"\media\anims_X\Bob\Bob_DrinkFromBottle.x"
)
OUTPUT = (
    Path(__file__).resolve().parent.parent
    / "Contents" / "mods" / "MateArgentino" / "42"
    / "media" / "anims_X" / "Bob" / "Bob_MateSip.x"
)

FPS = 30
TICKS_PER_SECOND = 4800
TICKS_PER_FRAME = TICKS_PER_SECOND // FPS
DURATION_FRAMES = 108
SIP_SOURCE_TICK = 4800

BONES = [
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


def read_tracks(path):
    root = base._parse(path.read_text(encoding="utf-8", errors="replace"))
    tracks = {}
    for animation in base._find_all(root, "Animation"):
        if not animation.children:
            continue
        bone = animation.children[0].args.strip().split()[0]
        if bone not in BONES:
            continue
        bone_tracks = tracks.setdefault(bone, {})
        for key in animation.children:
            if key.name not in ("R", "S", "T"):
                continue
            nums = base._floats(key.args)
            count = int(nums[1])
            cursor = 2
            samples = []
            while cursor < len(nums) and len(samples) < count:
                tick = int(nums[cursor])
                key_type = int(nums[cursor + 1])
                width = 4 if key_type == 4 else 3
                value = tuple(nums[cursor + 2:cursor + 2 + width])
                samples.append((tick, value))
                cursor += 2 + width
            bone_tracks[key.name] = samples
    return tracks


def lerp(a, b, amount):
    return tuple(x + (y - x) * amount for x, y in zip(a, b))


def sample(samples, tick, rotation=False):
    if tick <= samples[0][0]:
        return samples[0][1]
    if tick >= samples[-1][0]:
        return samples[-1][1]
    for (ta, va), (tb, vb) in zip(samples, samples[1:]):
        if ta <= tick <= tb:
            amount = (tick - ta) / (tb - ta)
            if rotation:
                qa = (va[3], va[0], va[1], va[2])
                qb = (vb[3], vb[0], vb[1], vb[2])
                q = base.slerp(qa, qb, amount)
                return (q[1], q[2], q[3], q[0])
            return lerp(va, vb, amount)
    return samples[-1][1]


def source_tick(frame):
    if frame <= 12:
        return 0
    if frame <= 36:
        return (frame - 12) / 24 * SIP_SOURCE_TICK
    if frame <= 72:
        return SIP_SOURCE_TICK
    if frame <= 96:
        return (96 - frame) / 24 * SIP_SOURCE_TICK
    return 0


def fmt(values):
    return ",".join(f"{value:.6f}" for value in values)


def rigid_inverse(matrix):
    """Inverse of a row-vector rigid transform [R 0; t 1]."""
    result = [0.0] * 16
    result[0], result[1], result[2] = matrix[0], matrix[4], matrix[8]
    result[4], result[5], result[6] = matrix[1], matrix[5], matrix[9]
    result[8], result[9], result[10] = matrix[2], matrix[6], matrix[10]
    result[15] = 1.0
    tx, ty, tz = matrix[12], matrix[13], matrix[14]
    result[12] = -(tx * result[0] + ty * result[4] + tz * result[8])
    result[13] = -(tx * result[1] + ty * result[5] + tz * result[9])
    result[14] = -(tx * result[2] + ty * result[6] + tz * result[10])
    return result


def rotation_from_matrix(matrix):
    q = base.rot_mat_to_q((
        matrix[0], matrix[1], matrix[2],
        matrix[4], matrix[5], matrix[6],
        matrix[8], matrix[9], matrix[10],
    ))
    return (q[1], q[2], q[3], q[0])


def main():
    if not SOURCE.exists():
        sys.exit(f"No se encontro la animacion vanilla: {SOURCE}")
    tracks = read_tracks(SOURCE)
    missing = [bone for bone in BONES if bone not in tracks]
    if missing:
        sys.exit(f"Faltan canales vanilla: {missing}")

    _, parents, rest_local = base._load_skeleton(SOURCE)

    def local_matrix(bone, tick):
        matrix = list(rest_local[bone])
        bone_tracks = tracks.get(bone)
        if bone_tracks:
            rotation = sample(bone_tracks["R"], tick, rotation=True)
            q = (rotation[3], rotation[0], rotation[1], rotation[2])
            rot = base.q_to_rot_mat(q)
            matrix[0:3] = rot[0:3]
            matrix[4:7] = rot[3:6]
            matrix[8:11] = rot[6:9]
            translation = sample(bone_tracks["T"], tick)
            matrix[12:15] = translation
        return matrix

    def relative_to_bip01(bone, tick):
        matrix = local_matrix(bone, tick)
        parent = parents[bone]
        while parent != "Bip01":
            matrix = base._mul(matrix, local_matrix(parent, tick))
            parent = parents[parent]
        return matrix

    hand_at_zero = relative_to_bip01("Bip01_L_Hand", 0)
    prop_at_zero = local_matrix("Bip01_Prop2", 0)
    grip = base._mul(prop_at_zero, rigid_inverse(hand_at_zero))
    # Keep the vanilla cup orientation relative to the wrist, but eliminate its
    # positional offset. Prop2's origin must coincide with the hand every frame.
    grip[12], grip[13], grip[14] = 0.0, 0.0, 0.0

    prop_pose = {}
    for frame in range(DURATION_FRAMES + 1):
        hand = relative_to_bip01("Bip01_L_Hand", source_tick(frame))
        prop_pose[frame] = base._mul(grip, hand)

    raw = SOURCE.read_text(encoding="utf-8", errors="replace")
    marker = re.search(r"^AnimationSet\s+", raw, re.MULTILINE)
    if not marker:
        sys.exit("No se encontro AnimationSet")
    prefix = raw[:marker.start()]
    old_ticks = re.search(
        r"AnimTicksPerSecond\s*\{\s*\d+\s*;\s*\}\s*$",
        prefix,
        re.MULTILINE,
    )
    if old_ticks:
        prefix = prefix[:old_ticks.start()]

    lines = [prefix, f"AnimTicksPerSecond  {{\n {TICKS_PER_SECOND};\n}}\n\n"]
    lines.append("AnimationSet Bob_MateSip {\n\n")

    for bone in BONES:
        lines.extend([" Animation {\n", f"  {{ {bone} }}\n\n"])
        for kind, key_type, width in (("S", 1, 3), ("R", 0, 4), ("T", 2, 3)):
            samples = tracks[bone][kind]
            lines.append(f"  AnimationKey {kind} {{\n   {key_type};\n   {DURATION_FRAMES + 1};\n")
            for frame in range(DURATION_FRAMES + 1):
                if bone == "Bip01_Prop2" and kind == "R":
                    value = rotation_from_matrix(prop_pose[frame])
                elif bone == "Bip01_Prop2" and kind == "T":
                    value = tuple(prop_pose[frame][12:15])
                else:
                    value = sample(samples, source_tick(frame), rotation=(kind == "R"))
                suffix = ";;,\n" if frame < DURATION_FRAMES else ";;;\n"
                lines.append(
                    f"   {frame * TICKS_PER_FRAME};{width};{fmt(value)}{suffix}"
                )
            lines.append("  }\n\n")
        lines.append(" }\n\n")

    lines.append("}\n")
    OUTPUT.write_text("".join(lines), encoding="utf-8", newline="\n")

    start = tuple(prop_pose[0][12:15])
    sip = tuple(prop_pose[36][12:15])
    max_hand_error = 0.0
    for frame, prop in prop_pose.items():
        hand = relative_to_bip01("Bip01_L_Hand", source_tick(frame))
        error = sum((prop[i] - hand[i]) ** 2 for i in (12, 13, 14)) ** 0.5
        max_hand_error = max(max_hand_error, error)
    print("Escrito:", OUTPUT)
    print("Huesos:", ", ".join(BONES))
    print("Prop2 T neutral:", tuple(round(v, 4) for v in start))
    print("Prop2 T sorbo:  ", tuple(round(v, 4) for v in sip))
    print("Error maximo Prop2/mano:", f"{max_hand_error:.8f}")
    print("Duracion:", DURATION_FRAMES / FPS, "segundos")


if __name__ == "__main__":
    main()
