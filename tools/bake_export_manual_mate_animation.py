import bpy
from pathlib import Path


ROOT = Path(r"E:\Repos\Test\MateArgentino")
OUTPUT = ROOT / "art-3d" / "manual-animation-export" / "Bob_MateSip_baked.glb"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

RIG_NAME = "OBJ-HumanRig (0)"
MATE_NAME = "MatePreparado3D"
ACTION_NAME = "Bob_MateSip_manual"
FRAMES = range(0, 125)
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

scene = bpy.context.scene
scene.frame_start = 0
scene.frame_end = 124
scene.render.fps = 30
rig = bpy.data.objects[RIG_NAME]
mate = bpy.data.objects[MATE_NAME]
rig.animation_data.action = bpy.data.actions[ACTION_NAME]

# Capture the evaluated result exactly as the user sees it. For Prop2 use the
# visible mate object's origin, so its manually adjusted grip becomes part of
# the baked animation instead of an external Blender-only constraint offset.
captured = {name: {} for name in BONES}
for frame in FRAMES:
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    rig_eval = rig.evaluated_get(depsgraph)
    for name in BONES:
        captured[name][frame] = rig_eval.pose.bones[name].matrix.copy()
    mate_eval = mate.evaluated_get(depsgraph)
    captured["Bip01_Prop2"][frame] = (
        rig.matrix_world.inverted() @ mate_eval.matrix_world
    )

# Replace the control-rig action with plain keys on the deform bones.
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

bpy.ops.export_scene.gltf(
    filepath=str(OUTPUT),
    export_format="GLB",
    use_selection=True,
    export_animations=True,
    export_animation_mode="ACTIVE_ACTIONS",
    export_frame_range=True,
    export_force_sampling=True,
    export_skins=True,
    export_def_bones=True,
    export_morph=False,
    export_lights=False,
    export_cameras=False,
)
print("EXPORTED", OUTPUT)
