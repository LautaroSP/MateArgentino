#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Genera una version espejada de Bob_MateSip.x: el movimiento de beber pasa del
brazo derecho al izquierdo (Bip01_R_* -> Bip01_L_*), el brazo derecho queda sin
keys (neutro) y Bip01_Prop2 (el mate) se espeja a la izquierda.

Estrategia (misma que export_mate_sip_x.py, validada contra el juego):
  - PZ aplica las rotaciones locales del clip (keys R) directamente como transform
    local de cada hueso, compuestas sobre el pose base del personaje (0-pose =
    keys de tick 0 del teacup vanilla).
  - Composicion del juego: world(bone) = local(bone) * world(parent) (row-vector,
    verificado en AnimationPlayer.getUnweightedModelTransform).
  - Para espejar el brazo a la izquierda basta espejar la rotacion local de cada
    hueso R (rotar su eje en el plano sagital: quaternion (w,x,y,z) -> (w,-x,y,z))
    y usar la traslacion local (FrameTransformMatrix) del hueso L correspondiente,
    que es el espejo de la del hueso R en el esqueleto del personaje.
  - El torso (Spine/Spine1/Neck/Head) no se toca: es el mismo para ambos lados.
  - El brazo derecho (Bip01_R_*) NO lleva bloques Animation -> queda en neutro.

Uso:  python tools/export_mate_sip_mirror.py
Requiere: la instalacion de Project Zomboid (para leer los vanilla .x) y Python 3.
"""
import os
import re
import math
import sys
from pathlib import Path

GAME = r"C:\Program Files (x86)\Steam\steamapps\common\ProjectZomboid"
VANILLA_X = os.path.join(GAME, "media", "anims_X", "Bob", "Bob_DrinkFromTeacup.x")
OUT_X = (
    Path(__file__).resolve().parent.parent
    / "Contents" / "mods" / "MateArgentino" / "42"
    / "media" / "anims_X" / "Bob" / "Bob_MateSip.x"
)

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

# huesos del torso que se conservan tal cual (mismo para ambos brazos)
TORSO_BONES = ["Bip01_Spine", "Bip01_Spine1", "Bip01_Neck", "Bip01_Head"]

# huesos del brazo derecho que se espejan al izquierdo
MIRROR_PAIRS = [
    ("Bip01_L_Clavicle", "Bip01_R_Clavicle"),
    ("Bip01_L_UpperArm", "Bip01_R_UpperArm"),
    ("Bip01_L_Forearm", "Bip01_R_Forearm"),
    ("Bip01_L_Hand", "Bip01_R_Hand"),
    ("Bip01_L_Finger0", "Bip01_R_Finger0"),
    ("Bip01_L_Finger1", "Bip01_R_Finger1"),
]

# Bip01_Prop2 se espeja sobre su propio eje (quat -> (w,-x,y,z))
MIRROR_SELF = ["Bip01_Prop2"]

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

    def mirror_q(q):
        """Espejo de la rotacion local en el plano sagital.

        Convencion validada contra los pares L/R vanilla del juego (p.ej.
        Bob_Seated_SitDown_R_1hand.x vs _L_1hand.x): el hueso L lleva la
        rotacion del R conjugada por una vuelta de 180 grados sobre el eje
        vertical (R_y(pi)). En (w,x,y,z) equivale a (w,-x,y,-z) (la variante
        (-w,x,-y,z) del vanilla es el mismo giro, solo que con el signo global
        invertido, lo cual representa la misma rotacion).
        """
        return (q[0], -q[1], q[2], -q[3])

    # Mapa: hueso de salida -> (hueso fuente en el vanilla, aplicar_espejo)
    out_bones = {}
    for b in TORSO_BONES:
        out_bones[b] = (b, False)
    for lb, rb in MIRROR_PAIRS:
        out_bones[lb] = (rb, True)
    for b in MIRROR_SELF:
        out_bones[b] = (b, True)

    poses = {}
    poses_src = {}
    for b, (src, do_mirror) in out_bones.items():
        if src not in a_local:
            print(f"  [warn] hueso {src} no presente; se omite {b}")
            continue
        q_neutral = key_at(src, 0)
        sipA = key_at(src, SIP_A_FRAME)
        sipB = key_at(src, SIP_B_FRAME)
        if q_neutral is None:
            print(f"  [warn] {src} sin keys vanilla en tick 0; se omite {b}")
            continue
        if sipA is None or sipB is None:
            print(f"  [warn] {src} sin keys vanilla; solo neutral")
            sipA = sipB = q_neutral
        poses_src.setdefault(src, {"neutral": qnorm(q_neutral), "sipA": qnorm(sipA), "sipB": qnorm(sipB)})
        if do_mirror:
            q_neutral, sipA, sipB = mirror_q(q_neutral), mirror_q(sipA), mirror_q(sipB)
        poses[b] = {"neutral": qnorm(q_neutral), "sipA": qnorm(sipA), "sipB": qnorm(sipB)}

    # Keyframes por frame (0..DURATION)
    pose_lookup = {"neutral": "neutral", "sipA": "sipA", "sipB": "sipB"}
    per_frame = {}
    per_frame_src = {}
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
        per_frame_src[f] = {
            s: slerp(poses_src[s][pose_lookup[pa]], poses_src[s][pose_lookup[pb]], t)
            for s in poses_src
        }

    # Verificacion en memoria: el espejo debe conmutar con el slerp, de modo
    # que per_frame[Lb][f] == mirror_q(per_frame_src[Rb][f]) para todo frame.
    max_dev = 0.0
    for f in range(0, DURATION_FRAMES + 1):
        for lb, (rb, do_mirror) in out_bones.items():
            if not do_mirror or lb not in per_frame[f] or rb not in per_frame_src[f]:
                continue
            q = per_frame[f][lb]
            m = mirror_q(per_frame_src[f][rb])
            # comparable a menos de un signo global
            dev = max(abs(q[i] - m[i]) for i in range(4))
            dev = min(dev, max(abs(q[i] + m[i]) for i in range(4)))
            max_dev = max(max_dev, dev)
    print("Verificacion espejo (L = R_y(pi) de R, por frame): max_dev=%.6f" % max_dev)

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
    # Auto-verificacion: re-parsear el output
    # ------------------------------------------------------------------
    st = _parse(OUT_X.read_text(encoding="utf-8"))
    okeys = {}
    anim_bones = []
    for anim in _find_all(st, "Animation"):
        if not anim.children:
            continue
        bone = anim.children[0].args.strip().split()[0]
        anim_bones.append(bone)
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

    expected_bones = set(poses)
    got_bones = set(anim_bones)
    missing = expected_bones - got_bones
    extra = got_bones - expected_bones
    print("Bloques Animation:", len(anim_bones), "->", sorted(anim_bones))
    print("  missing:", sorted(missing) or "ninguno", " extra:", sorted(extra) or "ninguno")
    assert not missing, "faltan huesos en el output"
    assert not extra, "huesos de mas en el output"

    # El brazo derecho no debe llevar keys (queda neutro)
    r_arm = [b for b in got_bones if b.startswith("Bip01_R_")]
    print("Huesos R con bloque:", r_arm or "ninguno (brazo derecho neutro)")

    # Round-trip: los keys leidos del output deben coincidir con per_frame
    max_rt = 0.0
    for f in range(0, DURATION_FRAMES + 1):
        tick = f * TICKS_PER_FRAME
        for b, q in per_frame[f].items():
            got = okeys.get(b, {}).get(tick)
            if got is None:
                max_rt = 1e9
                continue
            dev = max(abs(got[i] - q[i]) for i in range(4))
            dev = min(dev, max(abs(got[i] + q[i]) for i in range(4)))
            max_rt = max(max_rt, dev)
    print("Round-trip output vs per_frame: max_dev=%.6f" % max_rt)
    assert max_rt < 1e-4, "el texto escrito no reproduce per_frame"

    # Sanidad world (modelo del juego, solo informativo): mano L y mate cerca
    # de la cabeza en los frames de sorbo.
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

    def local_at(name, tick):
        m = list(a_local[name])
        q = okeys.get(name, {}).get(tick)
        if q is not None:
            rm = q_to_rot_mat(q)
            m[0:3] = rm[0:3]
            m[4:7] = rm[3:6]
            m[8:11] = rm[6:9]
        return m

    def world_at(name, tick, memo):
        if name in memo:
            return memo[name]
        w = local_at(name, tick)
        if name in oparents:
            w = _mul(w, world_at(oparents[name], tick, memo))
        memo[name] = w
        return w

    def origin(m):
        return (m[12], m[13], m[14])

    print("Sanidad world (FTM+keys):")
    for f in (0, 42, 65, 124):
        tick = f * TICKS_PER_FRAME
        memo = {}
        lhand = origin(world_at("Bip01_L_Hand", tick, memo))
        head = origin(world_at("Bip01_Head", tick, memo))
        prop2 = origin(world_at("Bip01_Prop2", tick, memo))
        d = math.sqrt(sum((lhand[i] - head[i]) ** 2 for i in range(3)))
        dp2 = math.sqrt(sum((prop2[i] - head[i]) ** 2 for i in range(3)))
        print(f"frame {f:3d} (tick {tick:6d}): lhand={tuple(round(x,3) for x in lhand)} "
              f"head={tuple(round(x,3) for x in head)} "
              f"dist(lhand,head)={d:.3f} dist(prop2,head)={dp2:.3f}")

if __name__ == "__main__":
    main()
