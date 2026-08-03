"""Print animated transform ranges for selected nodes in a binary glTF file."""

import json
from pathlib import Path
import struct
import sys


COMPONENT = {5126: ("f", 4)}
WIDTH = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}


def load_glb(path: Path):
    raw = path.read_bytes()
    json_len, json_type = struct.unpack_from("<II", raw, 12)
    if json_type != 0x4E4F534A:
        raise ValueError("Primer bloque GLB no es JSON")
    doc = json.loads(raw[20 : 20 + json_len])
    pos = 20 + json_len
    bin_len, bin_type = struct.unpack_from("<II", raw, pos)
    if bin_type != 0x004E4942:
        raise ValueError("Segundo bloque GLB no es BIN")
    return doc, raw[pos + 8 : pos + 8 + bin_len]


def accessor_values(doc, blob, index):
    accessor = doc["accessors"][index]
    view = doc["bufferViews"][accessor["bufferView"]]
    fmt, size = COMPONENT[accessor["componentType"]]
    width = WIDTH[accessor["type"]]
    stride = view.get("byteStride", size * width)
    start = view.get("byteOffset", 0) + accessor.get("byteOffset", 0)
    unpack = struct.Struct("<" + fmt * width)
    return [unpack.unpack_from(blob, start + i * stride) for i in range(accessor["count"])]


def main():
    path = Path(sys.argv[1])
    doc, blob = load_glb(path)
    animation = doc["animations"][0]
    names = {i: node.get("name", f"node-{i}") for i, node in enumerate(doc["nodes"])}
    wanted = {"Bip01_L_UpperArm", "Bip01_L_Forearm", "Bip01_L_Hand", "Bip01_Prop2"}
    print("animation", animation.get("name"), "channels", len(animation["channels"]))
    for channel in animation["channels"]:
        target = channel["target"]
        name = names[target["node"]]
        if name not in wanted:
            continue
        sampler = animation["samplers"][channel["sampler"]]
        values = accessor_values(doc, blob, sampler["output"])
        mins = tuple(round(min(row[i] for row in values), 6) for i in range(len(values[0])))
        maxs = tuple(round(max(row[i] for row in values), 6) for i in range(len(values[0])))
        print(name, target["path"], "keys", len(values), "min", mins, "max", maxs)


if __name__ == "__main__":
    main()
