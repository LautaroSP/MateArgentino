import bpy
from pathlib import Path


ROOT = Path(r"E:\Repos\Test\MateArgentino")
OUTPUT = ROOT / "art-3d" / "manual-animation-export" / "Bob_MateSip.glb"
OUTPUT.parent.mkdir(parents=True, exist_ok=True)

rig = bpy.data.objects["OBJ-HumanRig (0)"]
action = bpy.data.actions["Bob_MateSip_manual"]
if rig.animation_data is None:
    rig.animation_data_create()
rig.animation_data.action = action

scene = bpy.context.scene
scene.frame_start = 0
scene.frame_end = 124
scene.render.fps = 30

if rig.mode != "OBJECT":
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="OBJECT")
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
