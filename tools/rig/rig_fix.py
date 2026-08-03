import bpy

# Fixes two bugs in Paddlefruit Community Rig v4.0.1 (PZ_HumanRig.py) that break
# the "Add Animation to Rig" (zomboid.remap_animation) operator.
# Run this in Blender's Scripting workspace AFTER the rig's own script has been
# loaded (Blender asks to run PY-PZ_HumanRig.py when you open MateSip_rig.blend).

ns = {}
src = bpy.data.texts['PY-PZ_HumanRig.py'].as_string()
exec(compile(src, 'PY-PZ_HumanRig.py', 'exec'), ns)

# Bug 1: 'imported_animation_active_index' is commented out of the property group.
PG = ns['PZ_HumanRigGlobalProperties']
if not hasattr(PG, 'imported_animation_active_index'):
    PG.imported_animation_active_index = bpy.props.IntProperty(default=0)

# Bug 2: control_dict maps Bip01_L/R_Hand to bones that do not exist in the rig
# (they are named CTRL-HandFK.L / CTRL-HandFK.R).
op = ns['PZ_HumanRig_RemapAnimation']
op.control_dict['Bip01_L_Hand'] = 'CTRL-HandFK.L'
op.control_dict['Bip01_R_Hand'] = 'CTRL-HandFK.R'

print("Rig remap fixed. To re-import a .x, use the Python console:")
print("    import bpy")
print("    s = bpy.context.scene")
print("    s.pz_human_imported_animations.clear()")
print("    a = s.pz_human_imported_animations.add()")
print("    a.anim_path = r'C:\\path\\to\\file.x'")
print("    a.file_type = '.x'")
print("    s.pz_human_global_props.imported_animation_active_index = 0")
print("    bpy.ops.zomboid.remap_animation()")
