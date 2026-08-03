from __future__ import annotations

import importlib.util
import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "art-3d" / "animation-preview"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_PATH = OUTPUT_DIR / "mate_sip_preview.mp4"
GIF_PATH = OUTPUT_DIR / "mate_sip_preview.gif"
STILL_PATH = OUTPUT_DIR / "mate_sip_keypose.png"
BLEND_PATH = OUTPUT_DIR / "mate_sip_preview.blend"
FRAMES_DIR = OUTPUT_DIR / "frames"
FRAMES_DIR.mkdir(parents=True, exist_ok=True)
SOUND_PATH = (
    ROOT
    / "Contents"
    / "mods"
    / "MateArgentino"
    / "42"
    / "media"
    / "sound"
    / "MateArgentino_RuidoMate.mp3"
)


def load_model_tools():
    source = ROOT / "tools" / "create_3d_models.py"
    spec = importlib.util.spec_from_file_location("mate_model_tools", source)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def material(name: str, color: tuple[float, float, float, float], metallic=0.0):
    mat = bpy.data.materials.new(name)
    mat.diffuse_color = color
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = 0.58
    bsdf.inputs["Metallic"].default_value = metallic
    return mat


def add_sphere(name, location, scale, mat):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=32, ring_count=16, location=location
    )
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def add_cube(name, location, scale, mat, bevel=0.08):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.data.materials.append(mat)
    modifier = obj.modifiers.new("Rounded", "BEVEL")
    modifier.width = bevel
    modifier.segments = 3
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    return obj


def add_segment(name, start, end, radius, mat):
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=1, depth=2)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(mat)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    set_segment(obj, start, end, radius, 1)
    return obj


def set_segment(obj, start, end, radius, frame):
    start_v = Vector(start)
    end_v = Vector(end)
    direction = end_v - start_v
    obj.location = (start_v + end_v) / 2
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(direction)
    obj.scale = (radius, radius, direction.length / 2)
    obj.keyframe_insert("location", frame=frame)
    obj.keyframe_insert("rotation_quaternion", frame=frame)
    obj.keyframe_insert("scale", frame=frame)


def set_transform(obj, location, rotation, frame):
    obj.location = location
    obj.rotation_mode = "XYZ"
    obj.rotation_euler = rotation
    obj.keyframe_insert("location", frame=frame)
    obj.keyframe_insert("rotation_euler", frame=frame)


def look_at(obj, point):
    direction = Vector(point) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def add_text(body, location, size, mat, align="CENTER"):
    bpy.ops.object.text_add(location=location, rotation=(math.radians(74), 0, 0))
    text = bpy.context.object
    text.data.body = body
    text.data.align_x = align
    text.data.size = size
    text.data.extrude = 0.004
    text.data.materials.append(mat)
    return text


def configure_interpolation():
    for action in bpy.data.actions:
        curves = getattr(action, "fcurves", ())
        for curve in curves:
            for point in curve.keyframe_points:
                point.interpolation = "BEZIER"
                point.easing = "EASE_IN_OUT"


def add_sound(scene):
    if not SOUND_PATH.is_file():
        return
    editor = scene.sequence_editor_create()
    strips = getattr(editor, "strips", None)
    if strips is None:
        strips = editor.sequences
    start = 37
    channel = 1
    while start < 100:
        strip = strips.new_sound(
            f"Mate sip {channel}", str(SOUND_PATH), channel, start
        )
        strip.volume = 0.9
        start = int(strip.frame_final_end)
        channel += 1


def main():
    tools = load_model_tools()
    tools.clear_scene()

    skin = material("Skin", (0.68, 0.48, 0.34, 1))
    shirt = material("Shirt", (0.13, 0.20, 0.24, 1))
    trousers = material("Trousers", (0.08, 0.09, 0.11, 1))
    shoe = material("Shoes", (0.025, 0.025, 0.03, 1))
    accent = material("Accent", (0.47, 0.88, 0.57, 1), metallic=0.15)
    white = material("White", (0.92, 0.95, 0.92, 1))

    add_cube("Torso", (0, 0.04, 1.36), (0.68, 0.34, 0.76), shirt, 0.16)
    add_sphere("Head", (0, -0.02, 2.10), (0.29, 0.27, 0.34), skin)
    add_cube("Neck", (0, 0.0, 1.82), (0.17, 0.16, 0.18), skin, 0.06)
    add_segment("LegL", (-0.24, 0.03, 0.78), (-0.27, 0.02, 0.12), 0.18, trousers)
    add_segment("LegR", (0.24, 0.03, 0.78), (0.27, 0.02, 0.12), 0.18, trousers)
    add_cube("ShoeL", (-0.27, -0.11, 0.08), (0.20, 0.34, 0.10), shoe, 0.05)
    add_cube("ShoeR", (0.27, -0.11, 0.08), (0.20, 0.34, 0.10), shoe, 0.05)

    left_shoulder = (0.60, 0.02, 1.68)
    left_elbow = (0.73, -0.02, 1.18)
    left_wrist = (0.62, -0.09, 0.79)
    add_segment("LeftUpperArm", left_shoulder, left_elbow, 0.16, shirt)
    add_segment("LeftForearm", left_elbow, left_wrist, 0.13, skin)
    add_sphere("LeftHand", left_wrist, (0.14, 0.10, 0.18), skin)

    shoulder = (-0.60, 0.02, 1.68)
    poses = {
        1: ((-0.70, -0.03, 1.20), (-0.60, -0.18, 0.83), (-0.66, -0.22, 0.78)),
        24: ((-0.66, -0.10, 1.30), (-0.51, -0.29, 1.12), (-0.53, -0.33, 1.07)),
        42: ((-0.58, -0.20, 1.46), (-0.31, -0.36, 1.55), (-0.34, -0.39, 1.50)),
        82: ((-0.58, -0.20, 1.46), (-0.31, -0.36, 1.55), (-0.34, -0.39, 1.50)),
        102: ((-0.66, -0.10, 1.30), (-0.51, -0.29, 1.12), (-0.53, -0.33, 1.07)),
        124: ((-0.70, -0.03, 1.20), (-0.60, -0.18, 0.83), (-0.66, -0.22, 0.78)),
    }

    upper = add_segment("RightUpperArm", shoulder, poses[1][0], 0.16, shirt)
    forearm = add_segment("RightForearm", poses[1][0], poses[1][1], 0.13, skin)
    hand = add_sphere("RightHand", poses[1][2], (0.14, 0.10, 0.18), skin)

    mate = tools.create_mate("AnimationMate", "prepared")
    mate.scale = (0.72, 0.72, 0.72)
    mate.rotation_mode = "XYZ"

    mate_transforms = {
        1: ((-0.70, -0.25, 0.73), (0, math.radians(2), 0)),
        24: ((-0.57, -0.37, 1.01), (0, math.radians(5), 0)),
        42: ((-0.38, -0.43, 1.48), (0, math.radians(9), 0)),
        82: ((-0.38, -0.43, 1.48), (0, math.radians(9), 0)),
        102: ((-0.57, -0.37, 1.01), (0, math.radians(5), 0)),
        124: ((-0.70, -0.25, 0.73), (0, math.radians(2), 0)),
    }

    for frame, (elbow, wrist, hand_position) in poses.items():
        set_segment(upper, shoulder, elbow, 0.16, frame)
        set_segment(forearm, elbow, wrist, 0.13, frame)
        hand.location = hand_position
        hand.keyframe_insert("location", frame=frame)
        location, rotation = mate_transforms[frame]
        set_transform(mate, location, rotation, frame)

    configure_interpolation()

    bpy.ops.mesh.primitive_plane_add(size=14, location=(0, 0, -0.03))
    floor = bpy.context.object
    floor.data.materials.append(material("Floor", (0.035, 0.045, 0.04, 1)))

    add_text("PREVIEW DE ANIMACION · SIN IMPLEMENTAR", (-0.03, 0.75, 2.85), 0.13, white)
    add_text("solo antebrazo + recorrido corto + mate vertical", (-0.03, 0.72, 2.65), 0.085, accent)

    world = bpy.context.scene.world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (
        0.008,
        0.012,
        0.010,
        1,
    )
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.22

    bpy.ops.object.light_add(type="AREA", location=(-3.5, -4.8, 5.5))
    key = bpy.context.object
    key.data.energy = 1050
    key.data.shape = "DISK"
    key.data.size = 4.0
    look_at(key, (0, 0, 1.3))
    bpy.ops.object.light_add(type="AREA", location=(3.0, -1.0, 3.5))
    fill = bpy.context.object
    fill.data.energy = 750
    fill.data.color = (0.42, 0.75, 0.52)
    fill.data.size = 3.5
    look_at(fill, (0, 0, 1.4))

    bpy.ops.object.camera_add(location=(3.7, -7.8, 3.0))
    camera = bpy.context.object
    camera.data.lens = 62
    look_at(camera, (-0.05, -0.03, 1.38))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    try:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    except TypeError:
        scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 720
    scene.render.resolution_y = 720
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.film_transparent = False
    scene.render.fps = 30
    scene.frame_start = 1
    scene.frame_end = 124
    scene.view_settings.look = "AgX - Medium High Contrast"

    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
    scene.render.resolution_x = 540
    scene.render.resolution_y = 540
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(FRAMES_DIR / "frame_")
    bpy.ops.render.render(animation=True)

    scene.frame_set(58)
    scene.render.resolution_x = 720
    scene.render.resolution_y = 720
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(STILL_PATH)
    bpy.ops.render.render(write_still=True)
    print(f"GIF_TARGET={GIF_PATH}")
    print(f"FRAMES={FRAMES_DIR}")
    print(f"STILL={STILL_PATH}")
    print(f"BLEND={BLEND_PATH}")


if __name__ == "__main__":
    main()
