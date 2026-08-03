import json
import struct
from pathlib import Path


SOURCE = Path(r"E:\Repos\Test\MateArgentino\art-3d\manual-animation-export\Bob_MateSip_baked.glb")
OUTPUT = Path(r"E:\Repos\Test\MateArgentino\Contents\mods\MateArgentino\42\media\anims_X\Bob\Bob_MateSip.glb")
KEEP = {
    "Bip01_Spine", "Bip01_Spine1", "Bip01_Neck", "Bip01_Head",
    "Bip01_L_Clavicle", "Bip01_L_UpperArm", "Bip01_L_Forearm",
    "Bip01_L_Hand", "Bip01_L_Finger0", "Bip01_L_Finger1",
    "Bip01_Prop2",
}

raw = SOURCE.read_bytes()
magic, version, _ = struct.unpack_from("<4sII", raw, 0)
if magic != b"glTF" or version != 2:
    raise SystemExit("GLB invalido")

offset = 12
chunks = []
while offset < len(raw):
    length, kind = struct.unpack_from("<II", raw, offset)
    offset += 8
    chunks.append((kind, raw[offset:offset + length]))
    offset += length

json_chunk = next(data for kind, data in chunks if kind == 0x4E4F534A)
document = json.loads(json_chunk.decode("utf-8").rstrip("\x00 "))

for animation in document.get("animations", []):
    old_samplers = animation["samplers"]
    selected_channels = []
    used_sampler_indices = []
    for channel in animation["channels"]:
        node_index = channel["target"]["node"]
        node_name = document["nodes"][node_index].get("name")
        if node_name in KEEP:
            selected_channels.append(channel)
            used_sampler_indices.append(channel["sampler"])
    unique_indices = list(dict.fromkeys(used_sampler_indices))
    remap = {old: new for new, old in enumerate(unique_indices)}
    for channel in selected_channels:
        channel["sampler"] = remap[channel["sampler"]]
    animation["channels"] = selected_channels
    animation["samplers"] = [old_samplers[index] for index in unique_indices]
    animation["name"] = "Bob_MateSip"

encoded = json.dumps(document, separators=(",", ":")).encode("utf-8")
encoded += b" " * ((4 - len(encoded) % 4) % 4)
output_chunks = [(0x4E4F534A, encoded)] + [
    (kind, data) for kind, data in chunks if kind != 0x4E4F534A
]
total = 12 + sum(8 + len(data) for _, data in output_chunks)
result = bytearray(struct.pack("<4sII", b"glTF", 2, total))
for kind, data in output_chunks:
    result.extend(struct.pack("<II", len(data), kind))
    result.extend(data)
OUTPUT.write_bytes(result)
print("EXPORTED", OUTPUT)
for animation in document.get("animations", []):
    names = {
        document["nodes"][channel["target"]["node"]].get("name")
        for channel in animation["channels"]
    }
    print("ANIMATION", animation["name"], "CHANNELS", len(animation["channels"]))
    print("BONES", sorted(names))
