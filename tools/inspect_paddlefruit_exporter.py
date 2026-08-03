import bpy

source = bpy.data.texts["PY-PZ_HumanRig.py"].as_string()
for term in ('zomboid.export_glb', 'class PZ_OT_Export', 'def export_glb'):
    pos = source.find(term)
    if pos >= 0:
        print(f"\n=== {term} at {pos} ===")
        print(source[max(0, pos - 1000):pos + 6000])

op = bpy.ops.zomboid.export_glb.get_rna_type()
print("\n=== OPERATOR PROPERTIES ===")
for prop in op.properties:
    print(prop.identifier, prop.type, getattr(prop, "default", None))

rig = bpy.data.objects.get("OBJ-HumanRig (0)")
print("\n=== RIG RNA CANDIDATES ===")
for name in dir(rig):
    if any(part in name.lower() for part in ("export", "animation", "pz_human")):
        try:
            print(name, getattr(rig, name))
        except Exception as exc:
            print(name, exc)
