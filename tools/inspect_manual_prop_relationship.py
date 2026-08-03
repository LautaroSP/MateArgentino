import bpy

rig = bpy.data.objects["OBJ-HumanRig (0)"]
obj = bpy.data.objects.get("MatePreparado3D")
print("MATE", obj, "parent", obj.parent if obj else None)

for bone_name in ("CTRL-Prop.L", "Bip01_Prop2", "CTRL-HandFK.L"):
    bone = rig.pose.bones.get(bone_name)
    print("\nBONE", bone_name, bone)
    if bone:
        for con in bone.constraints:
            print(
                " CONSTRAINT", con.type, con.name,
                "target", getattr(con, "target", None),
                "subtarget", getattr(con, "subtarget", None),
                "owner_space", getattr(con, "owner_space", None),
                "target_space", getattr(con, "target_space", None),
                "influence", con.influence,
            )

if obj:
    print("\nOBJECT CONSTRAINTS")
    for con in obj.constraints:
        print(
            con.type, con.name,
            "target", getattr(con, "target", None),
            "subtarget", getattr(con, "subtarget", None),
            "owner_space", getattr(con, "owner_space", None),
            "target_space", getattr(con, "target_space", None),
            "influence", con.influence,
            "inverse", tuple(round(v, 5) for row in getattr(con, "inverse_matrix", []) for v in row) if hasattr(con, "inverse_matrix") else None,
        )

    for frame in (0, 20, 42, 60, 75, 100, 124):
        bpy.context.scene.frame_set(frame)
        prop = rig.pose.bones["Bip01_Prop2"]
        prop_world = rig.matrix_world @ prop.matrix
        relative = prop_world.inverted() @ obj.matrix_world
        loc, rot, scale = relative.decompose()
        print(
            "FRAME", frame,
            "REL_LOC", tuple(round(x, 6) for x in loc),
            "REL_ROT", tuple(round(x, 6) for x in rot.to_euler("XYZ")),
            "REL_SCALE", tuple(round(x, 6) for x in scale),
        )
