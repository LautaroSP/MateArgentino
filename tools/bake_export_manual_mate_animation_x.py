import bpy
from pathlib import Path


ROOT = Path(r"E:\Repos\Test\MateArgentino")
OUTPUT = ROOT / "art-3d" / "manual-animation-export" / "Bob_MateSip_fullrig.x"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

RIG_NAME = "OBJ-HumanRig (0)"
MATE_NAME = "MatePreparado3D"
ACTION_NAME = "Bob_MateSip_manual"
FRAMES = range(0, 125)
BONES = [
    "Bip01_Spine", "Bip01_Spine1", "Bip01_Neck", "Bip01_Head",
    "Bip01_L_Clavicle", "Bip01_L_UpperArm", "Bip01_L_Forearm",
    "Bip01_L_Hand", "Bip01_L_Finger0", "Bip01_L_Finger1",
    "Bip01_Prop2",
]

scene = bpy.context.scene
scene.frame_start = 0
scene.frame_end = 124
scene.render.fps = 30
rig = bpy.data.objects[RIG_NAME]
mate = bpy.data.objects[MATE_NAME]
rig.animation_data.action = bpy.data.actions[ACTION_NAME]

captured = {name: {} for name in BONES}
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    rig_eval = rig.evaluated_get(depsgraph)
    for name in BONES:
        captured[name][frame] = rig_eval.pose.bones[name].matrix.copy()
    mate_eval = mate.evaluated_get(depsgraph)
    captured["Bip01_Prop2"][frame] = rig.matrix_world.inverted() @ mate_eval.matrix_world

if rig.mode != "OBJECT":
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="OBJECT")
for pose_bone in rig.pose.bones:
    for constraint in list(pose_bone.constraints):
        pose_bone.constraints.remove(constraint)
    pose_bone.matrix_basis.identity()

baked = bpy.data.actions.new("Bob_MateSip")
rig.animation_data.action = baked
for frame in FRAMES:
    scene.frame_set(frame)
    for name in BONES:
        bone = rig.pose.bones[name]
        bone.rotation_mode = "QUATERNION"
        bone.matrix = captured[name][frame]
        bone.keyframe_insert("location", frame=frame, group=name)
        bone.keyframe_insert("rotation_quaternion", frame=frame, group=name)
        bone.keyframe_insert("scale", frame=frame, group=name)

bpy.ops.object.select_all(action="DESELECT")
rig.hide_set(False)
rig.hide_viewport = False
rig.select_set(True)
bpy.context.view_layer.objects.active = rig

module = "bl_ext.user_default.io_directx_x"
if not hasattr(bpy.ops.export_scene, "directx_x"):
    bpy.ops.preferences.addon_enable(module=module)
if not hasattr(bpy.ops.export_scene, "directx_x"):
    raise RuntimeError("No se pudo habilitar io_directx_x")

bpy.ops.export_scene.directx_x(
    filepath=str(OUTPUT),
    use_selection=True,
    use_mesh_modifiers=False,
    global_scale=1.0,
    axis_forward="Z",
    axis_up="Y",
    export_normals=False,
    export_uvs=False,
    export_materials=False,
    export_textures=False,
    export_armature=True,
    export_weights=False,
    export_animation=True,
    anim_key_format="TRS",
    export_format="TEXT_X",
    write_templates=True,
    pz_compat=True,
    anim_frame_start=0,
    anim_frame_end=124,
)
print("EXPORTED", OUTPUT)
