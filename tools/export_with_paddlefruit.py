"""Export the user's active animation through Paddlefruit's official PZ operator."""

from pathlib import Path
import bpy


ROOT = Path(r"E:\Repos\Test\MateArgentino")
OUT = ROOT / "art-3d" / "paddlefruit-export"
OUT.mkdir(parents=True, exist_ok=True)

rig = bpy.data.objects.get("OBJ-HumanRig (0)")
if rig is None:
    raise RuntimeError("No se encontro OBJ-HumanRig (0)")

action = bpy.data.actions.get("Bob_MateSip_manual")
if action is None:
    raise RuntimeError("No se encontro Bob_MateSip_manual")

bpy.ops.object.mode_set(mode="OBJECT") if bpy.context.object and bpy.context.object.mode != "OBJECT" else None
bpy.ops.object.select_all(action="DESELECT")
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
rig.animation_data_create()
rig.animation_data.action = action

# The in-game item is attached at Bip01_Prop2 with a zero model offset. Bake the
# visually adjusted mate object's origin into that deform bone so the result in PZ
# matches what the user positioned in Blender (instead of sitting on the wrist).
mate = bpy.data.objects.get("MatePreparado3D")
prop_bone = rig.pose.bones.get("Bip01_Prop2")
if mate is None or prop_bone is None:
    raise RuntimeError("No se encontro MatePreparado3D o Bip01_Prop2")
for constraint in prop_bone.constraints:
    constraint.mute = True
copy_location = prop_bone.constraints.new("COPY_LOCATION")
copy_location.name = "EXPORT Mate Location"
copy_location.target = mate
copy_location.owner_space = "WORLD"
copy_location.target_space = "WORLD"
copy_rotation = prop_bone.constraints.new("COPY_ROTATION")
copy_rotation.name = "EXPORT Mate Rotation"
copy_rotation.target = mate
copy_rotation.owner_space = "WORLD"
copy_rotation.target_space = "WORLD"
copy_rotation.mix_mode = "REPLACE"
prop_bone.scale = (1.0, 1.0, 1.0)

# The operator names the file after the action. Renaming here is session-only;
# this script never saves the .blend.
action.name = "Bob_MateSip"
props = rig.pz_human_props
props.file_output_path = str(OUT)
props.batch_export = False

result = bpy.ops.zomboid.export_glb()
target = OUT / "Bob_MateSip.glb"
if result != {"FINISHED"} or not target.exists():
    raise RuntimeError(f"Fallo el exportador: {result}, existe={target.exists()}")

print(f"PADDLEFRUIT_EXPORTED={target}")
print(f"SIZE={target.stat().st_size}")
