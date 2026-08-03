#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Genera Contents/mods/MateArgentino/42/media/anims_X/Bob/Bob_MateSip.x

Estrategia (validada contra el juego):
  - El runtime de PZ aplica las rotaciones locales del clip (keys R) directamente como
    transform local de cada hueso, compuestas sobre el pose base del personaje. El pose
    base usa la convencion "0-pose" del humanoide (los keys del propio teacup en tick 0),
    NO el FrameTransformMatrix del skeleton ni el bind del modelo Male_Skeleton.
  - Usar el bind del modelo como neutral tuerce el torso ~180 grados (el personaje "se
    parte a la mitad"). Por eso el NEUTRAL es el key de tick 0 del vanilla teacup, que ES
    el 0-pose neutral del humanoide (brazo abajo, de pie).
  - Poses de la animacion:
      * NEUTRAL  = rotaciones locales del vanilla Bob_DrinkFromTeacup en tick 0
                   (0-pose humanoide: de pie, brazo abajo).
      * SIP  A/B = rotaciones locales del vanilla Bob_DrinkFromTeacup en los frames
                   1200 (copa en boca, cabeza erguida) y 6600 (cabeza inclinada, sorbo).
  - Timeline (124 frames @ 30fps, 160 ticks/frame, AnimTicksPerSecond 4800):
      0-20  neutral (brazo abajo)
      20-42 subida del brazo a la boca  -> pose A en 42
      42-55 sostiene copa en boca (pose A)
      55-65 inclina cabeza (pose B, el sorbo)
      65-75 sostiene el sorbo (pose B)
      75-82 vuelve a pose A
      82-102 baja el brazo -> neutral en 102
      102-124 neutral
    Se emiten TODOS los frames (0..124) con slerp entre keyframes.
  - Se animan solo los huesos del tren superior que cambian. Huesos sin keys quedan a
    cargo de la pose base del juego (idle), que es lo natural.

Uso:  python tools/export_mate_sip_x.py
Requiere: la instalacion de Project Zomboid (para leer los vanilla .x) y Python 3.
"""
import os
import re
import math
import sys
from pathlib import Path

GAME = r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid"
VANILLA_X = os.path.join(GAME, "media", "anims_X", "Bob", "Bob_DrinkFromTeacup.x")
OUT_X = Path(__file__).resolve().parent.parent / "Contents" / "mods" / "MateArgentino" / "42" / "media" / "anims_X" / "Bob" / "Bob_MateSip.x"

SIP_A_FRAME = 1200   # copa en boca, cabeza erguida
SIP_B_FRAME = 6600   # cabeza inclinada (sorbo)
ANIM_FPS = 30
TICKS_PER_SEC = 4800
TICKS_PER_FRAME = TICKS_PER_SEC // ANIM_FPS
DURATION_FRAMES = 124

KEYFRAMES = [
    (0, "neutral"),
    (20, "neutral"),
    (42, "sipA"),
    (55, "sipA"),
    (65, "sipB"),
    (75, "sipB"),
    (82, "sipA"),
    (102, "neutral"),
    (124, "neutral"),
]

ANIMATED_BONES = [
    "Bip01_Spine", "Bip01_Spine1", "Bip01_Neck", "Bip01_Head",
    "Bip01_R_Clavicle", "Bip01_R_UpperArm", "Bip01_R_Forearm", "Bip01_R_Hand",
    "Bip01_R_Finger0", "Bip01_R_Finger1", "Bip01_Prop2",
]

# ----------------------------------------------------------------------------
# .x parser (texto)
# ----------------------------------------------------------------------------
class Node:
    __slots__ = ("name", "args", "children")
    def __init__(self, name, args):
        self.name = name
        self.args = args
        self.children = []

def _parse(s):
    i = 0
    n = len(s)
    def skip_ws():
        nonlocal i
        while i < n and s[i] in " \t\r\n":
            i += 1
    def skip_comma():
        nonlocal i
        skip_ws()
        if i < n and s[i] == ",":
            i += 1
            skip_ws()
    def read_ident():
        nonlocal i
        skip_ws()
        j = i
        while j < n and s[j] not in " \t\r\n{};,()[]<>/":
            j += 1
        tok = s[i:j]
        i = j
        return tok
    def parse_node(name, args):
        nonlocal i
        node = Node(name, args)
        while True:
            skip_comma()
            if i >= n or s[i] == "}":
                if i < n:
                    i += 1
                return node
            c = s[i]
            if c == "{":
                i += 1
                node.children.append(parse_node("_anon_", ""))
            elif c == ";":
                i += 1
            elif c == '"':
                j = s.index('"', i + 1)
                node.args += " " + s[i + 1:j]
                i = j + 1
            elif c == "[":
                j = s.index("]", i)
                node.args += " [" + s[i + 1:j] + "]"
                i = j + 1
            elif c == "<":
                j = s.index(">", i)
                node.args += " <" + s[i + 1:j] + ">"
                i = j + 1
            elif c == "(":
                j = s.index(")", i)
                node.args += " " + s[i:j + 1]
                i = j + 1
            else:
                ident = read_ident()
                skip_ws()
                if i < n and s[i] == "{":
                    i += 1
                    child = parse_node(ident, "")
                    node.children.append(child)
                else:
                    node.args += " " + ident
    skip_ws()
    return parse_node("ROOT", "")

def _floats(s):
    return [float(x) for x in re.findall(r"[-+]?[0-9]*\.?[0-9]+(?:[eE][-+]?[0-9]+)?", s)]

def _find_all(node, name):
    out = []
    if node.name == name:
        out.append(node)
    for c in node.children:
        out.extend(_find_all(c, name))
    return out

def _find_first(node, name):
    for c in node.children:
        if c.name == name:
            return c
    for c in node.children:
        r = _find_first(c, name)
        if r:
            return r
    return None

def _is_bone_node(node):
    return any(c.name == "FrameTransformMatrix" for c in node.children)

def _matrix_of(bone_node):
    ftm = _find_first(bone_node, "FrameTransformMatrix")
    if ftm is None:
        return None
    nums = _floats(ftm.args)
    return nums if len(nums) >= 16 else None

def _mul(a, b):
    out = [0.0] * 16
    for r in range(4):
        for c in range(4):
            out[r * 4 + c] = sum(a[r * 4 + k] * b[k * 4 + c] for k in range(4))
    return out

def _load_skeleton(path):
    """Devuelve (node_by_name, parents, local_matrices)."""
    st = _parse(Path(path).read_text(encoding="utf-8", errors="replace"))
    node_by_name = {}
    parents = {}
    def walk(n):
        node_by_name[n.name] = n
        for c in n.children:
            if _is_bone_node(c):
                parents[c.name] = n.name
                walk(c)
    for r in [n for n in st.children if _is_bone_node(n)]:
        walk(r)
    local = {nm: _matrix_of(node) for nm, node in node_by_name.items()}
    return node_by_name, parents, local

# ----------------------------------------------------------------------------
# Quaterniones (w,x,y,z), matching mathutils/blender order
# ----------------------------------------------------------------------------
def qmul(a, b):
    aw, ax, ay, az = a
    bw, bx, by, bz = b
    return (aw * bw - ax * bx - ay * by - az * bz,
            aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw)

def qconj(a):
    w, x, y, z = a
    return (w, -x, -y, -z)

def qnorm(a):
    l = math.sqrt(sum(v * v for v in a))
    return tuple(v / l for v in a) if l else (1, 0, 0, 0)

def q_to_rot_mat(q):
    w, x, y, z = q
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return (1 - 2 * (yy + zz), 2 * (xy - wz), 2 * (xz + wy),
            2 * (xy + wz), 1 - 2 * (xx + zz), 2 * (yz - wx),
            2 * (xz - wy), 2 * (yz + wx), 1 - 2 * (xx + yy))

def rot_mat_to_q(m):
    m00, m01, m02, m10, m11, m12, m20, m21, m22 = m
    tr = m00 + m11 + m22
    if tr > 0:
        s = math.sqrt(tr + 1.0) * 2
        return qnorm(((0.25 * s, (m21 - m12) / s, (m02 - m20) / s, (m10 - m01) / s)))
    if m00 > m11 and m00 > m22:
        s = math.sqrt(1.0 + m00 - m11 - m22) * 2
        return qnorm((((m21 - m12) / s), 0.25 * s, (m01 + m10) / s, (m02 + m20) / s))
    if m11 > m22:
        s = math.sqrt(1.0 + m11 - m00 - m22) * 2
        return qnorm((((m02 - m20) / s), (m01 + m10) / s, 0.25 * s, (m12 + m21) / s))
    s = math.sqrt(1.0 + m22 - m00 - m11) * 2
    return qnorm((((m10 - m01) / s), (m02 + m20) / s, (m12 + m21) / s, 0.25 * s))

def rot_part_quat(matrix):
    m = (matrix[0], matrix[1], matrix[2],
         matrix[4], matrix[5], matrix[6],
         matrix[8], matrix[9], matrix[10])
    return rot_mat_to_q(m)

def slerp(a, b, t):
    a = qnorm(a)
    b = qnorm(b)
    d = a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3]
    if d < 0:
        b = (-b[0], -b[1], -b[2], -b[3])
        d = -d
    d = max(-1.0, min(1.0, d))
    if d > 0.9995:
        return qnorm(tuple(a[i] + t * (b[i] - a[i]) for i in range(4)))
    theta = math.acos(d)
    sin_t = math.sin(theta)
    if sin_t < 1e-8:
        return qnorm(a)
    wa = math.sin((1 - t) * theta) / sin_t
    wb = math.sin(t * theta) / sin_t
    return qnorm(tuple(wa * a[i] + wb * b[i] for i in range(4)))

def q_axis_angle(v):
    """Para debug: devuelve (axis, angle_deg)."""
    w, x, y, z = qnorm(v)
    ang = 2 * math.acos(max(-1.0, min(1.0, w)))
    l = math.sqrt(x * x + y * y + z * z)
    return ((x / l, y / l, z / l) if l else (0, 0, 1)), math.degrees(ang)

# ----------------------------------------------------------------------------
# Lectura de datos
# ----------------------------------------------------------------------------
def world_quats(node_by_name, parents, local):
    """world_q(bone) = world_q(parent) * q_local_rest(bone)."""
    world_q = {}
    def calc(name):
        if name in world_q:
            return world_q[name]
        m = local[name]
        q = rot_part_quat(m)
        if name in parents:
            q = qmul(q, calc(parents[name]))
        world_q[name] = qnorm(q)
        return world_q[name]
    for b in list(node_by_name.keys()):
        calc(b)
    return world_q

def anim_keys(path):
    """Devuelve {bone: {frame: quat(w,x,y,z)}} para los keys de rotacion."""
    st = _parse(Path(path).read_text(encoding="utf-8", errors="replace"))
    anims = {}
    for anim in _find_all(st, "Animation"):
        if not anim.children:
            continue
        bone = anim.children[0].args.strip()
        bone = bone.split()[0] if bone.split() else ""
        if not bone:
            continue
        for key in anim.children:
            if key.name not in ("R", "S", "T"):
                continue
            if key.name != "R":
                continue
            nums = _floats(key.args)
            if len(nums) < 2:
                continue
            nkeys = int(nums[1])
            i = 2
            entry = anims.setdefault(bone, {})
            while i < len(nums) and len(entry) < nkeys:
                frame = int(nums[i])
                kt = int(nums[i + 1])
                cnt = 4 if kt == 4 else 3
                vals = tuple(nums[i + 2:i + 2 + cnt])
                entry[frame] = (vals[3], vals[0], vals[1], vals[2])  # (x,y,z,w) -> (w,x,y,z)
                i += 2 + cnt
    return anims

def local_rest_translation(local, name):
    m = local[name]
    return (m[12], m[13], m[14])

def main():
    if not os.path.exists(VANILLA_X):
        sys.exit(f"No se encontro {VANILLA_X}. Ajusta GAME.")

    a_nodes, a_parents, a_local = _load_skeleton(VANILLA_X)

    keys = anim_keys(VANILLA_X)

    def key_at(bone, frame):
        d = keys.get(bone)
        if not d:
            return None
        frames = sorted(d)
        if frame <= frames[0]:
            return d[frames[0]]
        if frame >= frames[-1]:
            return d[frames[-1]]
        for i in range(len(frames) - 1):
            if frames[i] <= frame <= frames[i + 1]:
                a, b = frames[i], frames[i + 1]
                t = (frame - a) / (b - a)
                qa, qb = d[a], d[b]
                return slerp(qa, qb, t)
        return d[frames[0]]

    # Poses objetivo por hueso
    poses = {}
    for b in ANIMATED_BONES:
        if b not in a_local:
            print(f"  [warn] hueso {b} no presente; se omite")
            continue
        q_neutral = key_at(b, 0)
        sipA = key_at(b, SIP_A_FRAME)
        sipB = key_at(b, SIP_B_FRAME)
        if q_neutral is None:
            print(f"  [warn] {b} sin keys vanilla en tick 0; se omite")
            continue
        if sipA is None or sipB is None:
            print(f"  [warn] {b} sin keys vanilla; solo neutral")
            sipA = sipB = q_neutral
        poses[b] = {"neutral": qnorm(q_neutral), "sipA": qnorm(sipA), "sipB": qnorm(sipB)}

    # Keyframes por frame (0..DURATION)
    pose_lookup = {"neutral": "neutral", "sipA": "sipA", "sipB": "sipB"}
    per_frame = {}
    for f in range(0, DURATION_FRAMES + 1):
        # hallar el par de keyframes que contiene a f
        kf = KEYFRAMES[0]
        nxt = None
        for i in range(len(KEYFRAMES) - 1):
            if KEYFRAMES[i][0] <= f <= KEYFRAMES[i + 1][0]:
                kf, nxt = KEYFRAMES[i], KEYFRAMES[i + 1]
                break
        if nxt is None:
            nxt = kf
        fa, pa = kf
        fb, pb = nxt
        t = 0.0 if fb == fa else (f - fa) / (fb - fa)
        per_frame[f] = {
            b: slerp(poses[b][pose_lookup[pa]], poses[b][pose_lookup[pb]], t)
            for b in poses
        }

    # ------------------------------------------------------------------
    # Escritura del .x
    # ------------------------------------------------------------------
    raw = Path(VANILLA_X).read_text(encoding="utf-8", errors="replace")
    m = re.search(r"^AnimationSet\s+", raw, re.MULTILINE)
    if not m:
        sys.exit("No se encontro el AnimationSet vanilla")
    prefix = raw[:m.start()]

    # El prefix copiado del vanilla termina con su propio AnimTicksPerSecond;
    # se recorta para emitir uno solo (el del bloque de datos, abajo).
    # Ojo: NO casar el "template AnimTicksPerSecond" (viene primero), solo el
    # bloque de datos al final del prefix (despues del skeleton).
    m_atps = re.search(r"AnimTicksPerSecond\s*\{\s*\d+\s*;\s*\}\s*$", prefix, re.MULTILINE)
    if m_atps:
        prefix = prefix[:m_atps.start()]

    out_lines = []
    out_lines.append(prefix)
    out_lines.append("AnimTicksPerSecond  {\n %d;\n}\n\n" % TICKS_PER_SEC)
    out_lines.append("AnimationSet Bob_MateSip {\n\n")

    def fmt_vec(vals):
        return ",".join("%.6f" % v for v in vals)

    for b in sorted(poses):
        out_lines.append(" Animation {\n")
        out_lines.append("  { %s }\n\n" % b)

        out_lines.append("  AnimationKey S {\n   1;\n   2;\n")
        out_lines.append("   0;3;1.000000,1.000000,1.000000;;,\n")
        out_lines.append("   %d;3;1.000000,1.000000,1.000000;;;\n" % (DURATION_FRAMES * TICKS_PER_FRAME))
        out_lines.append("  }\n\n")

        out_lines.append("  AnimationKey R {\n   0;\n   %d;\n" % (DURATION_FRAMES + 1))
        for f in range(0, DURATION_FRAMES + 1):
            q = per_frame[f][b]
            tick = f * TICKS_PER_FRAME
            end = ";;,\n" if f < DURATION_FRAMES else ";;;\n"
            out_lines.append("   %d;4;%s%s" % (tick, fmt_vec((q[1], q[2], q[3], q[0])), end))
        out_lines.append("  }\n\n")

        tr = local_rest_translation(a_local, b)
        out_lines.append("  AnimationKey T {\n   2;\n   2;\n")
        out_lines.append("   0;3;%s;;,\n" % fmt_vec(tr))
        out_lines.append("   %d;3;%s;;;\n" % (DURATION_FRAMES * TICKS_PER_FRAME, fmt_vec(tr)))
        out_lines.append("  }\n")
        out_lines.append(" }\n\n")

    out_lines.append("}\n")

    OUT_X.parent.mkdir(parents=True, exist_ok=True)
    OUT_X.write_text("".join(out_lines), encoding="utf-8", newline="\n")
    print("Escrito:", OUT_X)
    print("Tamano:  %.1f KB" % (OUT_X.stat().st_size / 1024))

    # ------------------------------------------------------------------
    # Auto-verificacion: re-parsear el output y reportar pose world
    # ------------------------------------------------------------------
    st = _parse(OUT_X.read_text(encoding="utf-8"))
    onodes = {}
    oparents = {}
    def walk(n):
        onodes[n.name] = n
        for c in n.children:
            if _is_bone_node(c):
                oparents[c.name] = n.name
                walk(c)
    for r in [n for n in st.children if _is_bone_node(n)]:
        walk(r)
    okeys = {}
    for anim in _find_all(st, "Animation"):
        if not anim.children:
            continue
        bone = anim.children[0].args.strip().split()[0]
        for key in anim.children:
            if key.name != "R":
                continue
            nums = _floats(key.args)
            nkeys = int(nums[1])
            i = 2
            entry = okeys.setdefault(bone, {})
            while i < len(nums) and len(entry) < nkeys:
                frame = int(nums[i]); kt = int(nums[i + 1])
                cnt = 4 if kt == 4 else 3
                vals = tuple(nums[i + 2:i + 2 + cnt])
                entry[frame] = (vals[3], vals[0], vals[1], vals[2])
                i += 2 + cnt

    def local_at(name, tick):
        m = list(a_local[name])
        q = okeys.get(name, {}).get(tick)
        if q is None and name in keys:
            q = key_at(name, tick)
        if q is not None:
            rm = q_to_rot_mat(q)
            m[0:3] = rm[0:3]
            m[4:7] = rm[3:6]
            m[8:11] = rm[6:9]
        return m

    def world_at(name, tick, memo):
        if name in memo:
            return memo[name]
        if name not in oparents:
            w = local_at(name, tick)
        else:
            w = _mul(local_at(name, tick), world_at(oparents[name], tick, memo))
        memo[name] = w
        return w

    def origin(m):
        return (m[12], m[13], m[14])

    ref_head = None
    for f in (0, 42, 65, 124):
        tick = f * TICKS_PER_FRAME
        memo = {}
        hand = world_at("Bip01_R_Hand", tick, memo)
        head = world_at("Bip01_Head", tick, memo)
        prop2 = world_at("Bip01_Prop2", tick, memo)
        hp, hd, pp = origin(hand), origin(head), origin(prop2)
        d = math.sqrt(sum((hp[i] - hd[i]) ** 2 for i in range(3)))
        dp2 = math.sqrt(sum((pp[i] - hd[i]) ** 2 for i in range(3)))
        if ref_head is None:
            ref_head = hd
        print(f"frame {f:3d} (tick {tick:6d}): hand={tuple(round(x,3) for x in hp)} "
              f"head={tuple(round(x,3) for x in hd)} "
              f"dist(hand,head)={d:.3f} dist(prop2,head)={dp2:.3f}")

if __name__ == "__main__":
    main()
