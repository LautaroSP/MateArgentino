from __future__ import annotations

import math
from pathlib import Path

import bpy
from mathutils import Vector


ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "Contents" / "mods" / "MateArgentino" / "42"
MODEL_DIR = MOD / "media" / "models_X" / "MateArgentino"
TEXTURE_DIR = MOD / "media" / "textures" / "MateArgentino"
ART_DIR = ROOT / "art-3d"
PREVIEW = ROOT / "MateArgentino_modelos3D_custom_preview.png"

MODEL_DIR.mkdir(parents=True, exist_ok=True)
TEXTURE_DIR.mkdir(parents=True, exist_ok=True)
ART_DIR.mkdir(parents=True, exist_ok=True)

ATLAS_SIZE = 128
CELLS = 4


def clear_scene() -> None:
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    for datablocks in (
        bpy.data.meshes,
        bpy.data.curves,
        bpy.data.materials,
        bpy.data.cameras,
        bpy.data.lights,
    ):
        for block in list(datablocks):
            if block.users == 0:
                datablocks.remove(block)


def make_atlas(name: str, colors: dict[str, tuple[float, float, float, float]]):
    image = bpy.data.images.new(name, width=ATLAS_SIZE, height=ATLAS_SIZE, alpha=True)
    pixels = [0.0] * (ATLAS_SIZE * ATLAS_SIZE * 4)
    roles = list(colors)
    for role_index, role in enumerate(roles):
        cell_x = role_index % CELLS
        cell_y = role_index // CELLS
        color = colors[role]
        for y in range(cell_y * 32, (cell_y + 1) * 32):
            for x in range(cell_x * 32, (cell_x + 1) * 32):
                shade = 0.92 + 0.08 * (((x * 13 + y * 7) % 11) / 10)
                offset = (y * ATLAS_SIZE + x) * 4
                pixels[offset : offset + 4] = [
                    min(1, color[0] * shade),
                    min(1, color[1] * shade),
                    min(1, color[2] * shade),
                    color[3],
                ]
    image.pixels = pixels
    destination = (
        ART_DIR / "preview-textures"
        if name.startswith("Preview")
        else TEXTURE_DIR
    )
    destination.mkdir(parents=True, exist_ok=True)
    image.filepath_raw = str(destination / f"{name}.png")
    image.file_format = "PNG"
    image.save()
    return image, {role: index for index, role in enumerate(roles)}


def make_material(name: str, image, metallic: float = 0.0, roughness: float = 0.62):
    material = bpy.data.materials.new(name)
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    texture = material.node_tree.nodes.new("ShaderNodeTexImage")
    texture.image = image
    material.node_tree.links.new(texture.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Metallic"].default_value = metallic
    bsdf.inputs["Roughness"].default_value = roughness
    return material


def apply_role(obj, role: str, image, role_indices, metallic: float = 0.0) -> None:
    if obj.type != "MESH":
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        bpy.ops.object.convert(target="MESH")
    material = make_material(f"{obj.name}_{role}", image, metallic=metallic)
    obj.data.materials.append(material)
    uv = obj.data.uv_layers.active or obj.data.uv_layers.new(name="UVMap")
    index = role_indices[role]
    cell_x = index % CELLS
    cell_y = index // CELLS
    center = ((cell_x + 0.5) / CELLS, (cell_y + 0.5) / CELLS)
    for loop in uv.data:
        loop.uv = center
    obj["mate_role"] = role


def bevel(obj, width: float, segments: int = 2) -> None:
    modifier = obj.modifiers.new("Soft edges", "BEVEL")
    modifier.width = width
    modifier.segments = segments
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.modifier_apply(modifier=modifier.name)


def add_cylinder(name, radius, depth, location, role, image, roles, vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth, location=location
    )
    obj = bpy.context.object
    obj.name = name
    apply_role(obj, role, image, roles, metallic=0.72 if role == "metal" else 0.0)
    return obj


def add_cube(name, dimensions, location, role, image, roles, bevel_width=0.0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.dimensions = dimensions
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel_width:
        bevel(obj, bevel_width, 3)
    apply_role(obj, role, image, roles)
    return obj


def add_uv_sphere(name, scale, location, role, image, roles):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32, ring_count=16, location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    apply_role(obj, role, image, roles)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    return obj


def cylinder_between(name, start, end, radius, role, image, roles):
    start_v = Vector(start)
    end_v = Vector(end)
    direction = end_v - start_v
    obj = add_cylinder(
        name,
        radius,
        direction.length,
        (start_v + end_v) / 2,
        role,
        image,
        roles,
        20,
    )
    obj.rotation_mode = "QUATERNION"
    obj.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(direction)
    obj.rotation_mode = "XYZ"
    return obj


def add_gourd_body(parts, image, roles):
    profile = [
        (0.000, 0.058),
        (0.018, 0.082),
        (0.070, 0.108),
        (0.135, 0.118),
        (0.190, 0.105),
        (0.220, 0.096),
        (0.232, 0.102),
    ]
    segments = 40
    vertices = []
    faces = []
    for z, radius in profile:
        for segment in range(segments):
            angle = 2 * math.pi * segment / segments
            vertices.append((radius * math.cos(angle), radius * math.sin(angle), z))
    for ring in range(len(profile) - 1):
        for segment in range(segments):
            nxt = (segment + 1) % segments
            a = ring * segments + segment
            b = ring * segments + nxt
            c = (ring + 1) * segments + nxt
            d = (ring + 1) * segments + segment
            faces.append((a, b, c, d))
    faces.append(tuple(reversed(range(segments))))
    mesh = bpy.data.meshes.new("MateGourdMesh")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    body = bpy.data.objects.new("MateGourd", mesh)
    bpy.context.collection.objects.link(body)
    apply_role(body, "gourd", image, roles)
    for polygon in body.data.polygons:
        polygon.use_smooth = True
    parts.append(body)

    bpy.ops.mesh.primitive_torus_add(
        major_radius=0.095,
        minor_radius=0.008,
        major_segments=40,
        minor_segments=10,
        location=(0, 0, 0.232),
    )
    rim = bpy.context.object
    rim.name = "MateRim"
    apply_role(rim, "metal", image, roles, metallic=0.8)
    parts.append(rim)

    inside = add_cylinder(
        "MateInterior", 0.086, 0.010, (0, 0, 0.224), "inside", image, roles
    )
    parts.append(inside)


def join_parts(parts, name, image):
    bpy.ops.object.select_all(action="DESELECT")
    for part in parts:
        part.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    bpy.ops.object.join()
    obj = bpy.context.object
    obj.name = name
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    xs = [vertex.co.x for vertex in obj.data.vertices]
    ys = [vertex.co.y for vertex in obj.data.vertices]
    zs = [vertex.co.z for vertex in obj.data.vertices]
    offset = Vector(
        (
            -(min(xs) + max(xs)) / 2,
            -(min(ys) + max(ys)) / 2,
            -min(zs),
        )
    )
    for vertex in obj.data.vertices:
        vertex.co += offset
    obj.location = (0, 0, 0)
    # Project Zomboid's world-item renderer expects one material/texture for a
    # ModelScript. Keep the atlas UVs but collapse Blender's material slots.
    obj.data.materials.clear()
    obj.data.materials.append(make_material(f"{name}_Atlas", image))
    for polygon in obj.data.polygons:
        polygon.material_index = 0
    return obj


def create_mate(name: str, state: str):
    palettes = {
        "empty": {
            "gourd": (0.28, 0.105, 0.035, 1),
            "metal": (0.62, 0.67, 0.65, 1),
            "inside": (0.055, 0.025, 0.012, 1),
            "yerba": (0.18, 0.28, 0.07, 1),
        },
        "dry": {
            "gourd": (0.31, 0.115, 0.038, 1),
            "metal": (0.72, 0.77, 0.75, 1),
            "inside": (0.06, 0.03, 0.015, 1),
            "yerba": (0.20, 0.39, 0.075, 1),
        },
        "prepared": {
            "gourd": (0.32, 0.12, 0.04, 1),
            "metal": (0.76, 0.80, 0.78, 1),
            "inside": (0.06, 0.03, 0.015, 1),
            "yerba": (0.12, 0.25, 0.045, 1),
        },
        "washed": {
            "gourd": (0.27, 0.095, 0.03, 1),
            "metal": (0.58, 0.61, 0.59, 1),
            "inside": (0.05, 0.025, 0.012, 1),
            "yerba": (0.20, 0.19, 0.075, 1),
        },
    }
    image, roles = make_atlas(name, palettes[state])
    parts = []
    add_gourd_body(parts, image, roles)
    if state != "empty":
        yerba = add_cylinder(
            "YerbaSurface", 0.084, 0.012, (0, 0, 0.229), "yerba", image, roles
        )
        parts.append(yerba)
        bombilla = cylinder_between(
            "Bombilla",
            (-0.012, 0.0, 0.210),
            (0.075, 0.0, 0.445),
            0.006,
            "metal",
            image,
            roles,
        )
        parts.append(bombilla)
        filter_tip = add_uv_sphere(
            "BombillaFilter",
            (0.011, 0.011, 0.018),
            (-0.012, 0.0, 0.205),
            "metal",
            image,
            roles,
        )
        parts.append(filter_tip)
    return join_parts(parts, name, image)


def create_thermo(name: str):
    image, roles = make_atlas(
        name,
        {
            "metal": (0.62, 0.68, 0.69, 1),
            "dark": (0.035, 0.045, 0.042, 1),
            "highlight": (0.84, 0.87, 0.86, 1),
        },
    )
    parts = []
    body = add_cylinder(name, 0.082, 0.390, (0, 0, 0.215), "metal", image, roles)
    bevel(body, 0.009, 3)
    parts.append(body)
    bpy.ops.mesh.primitive_cone_add(
        vertices=36,
        radius1=0.082,
        radius2=0.060,
        depth=0.060,
        location=(0, 0, 0.440),
    )
    shoulder = bpy.context.object
    apply_role(shoulder, "highlight", image, roles)
    parts.append(shoulder)
    cap = add_cylinder("ThermoCap", 0.060, 0.070, (0, 0, 0.505), "dark", image, roles)
    bevel(cap, 0.005, 2)
    parts.append(cap)
    base = add_cylinder("ThermoBase", 0.075, 0.018, (0, 0, 0.012), "dark", image, roles)
    parts.append(base)
    for index, (start, end) in enumerate(
        [
            ((0.082, 0, 0.135), (0.135, 0, 0.165)),
            ((0.135, 0, 0.165), (0.135, 0, 0.350)),
            ((0.135, 0, 0.350), (0.078, 0, 0.390)),
        ]
    ):
        parts.append(
            cylinder_between(
                f"ThermoHandle{index}", start, end, 0.011, "dark", image, roles
            )
        )
    return join_parts(parts, name, image)


def create_yerba(name: str, quality: str):
    quality_colors = {
        "economica": ((0.44, 0.12, 0.055, 1), (0.22, 0.055, 0.025, 1)),
        "media": ((0.88, 0.57, 0.035, 1), (0.50, 0.28, 0.015, 1)),
        "premium": ((0.02, 0.35, 0.13, 1), (0.01, 0.18, 0.065, 1)),
    }
    primary, accent = quality_colors[quality]
    image, roles = make_atlas(
        name,
        {
            "primary": primary,
            "cream": (0.77, 0.69, 0.51, 1),
            "accent": accent,
            "leaf": (0.12, 0.30, 0.08, 1),
        },
    )
    parts = [
        add_cube(
            "YerbaPackage",
            (0.273, 0.115, 0.300),
            (0, 0, 0.160),
            "primary",
            image,
            roles,
            0.009,
        ),
        add_cube(
            "YerbaLabel",
            (0.229, 0.008, 0.145),
            (0, -0.060, 0.155),
            "cream",
            image,
            roles,
            0.006,
        ),
        add_cube(
            "YerbaFold",
            (0.267, 0.125, 0.026),
            (0, 0, 0.315),
            "accent",
            image,
            roles,
            0.004,
        ),
    ]
    for x, z, rotation in [(-0.046, 0.155, -0.38), (0.0, 0.175, 0), (0.046, 0.155, 0.38)]:
        leaf = add_uv_sphere(
            "Leaf",
            (0.018, 0.006, 0.045),
            (x, -0.067, z),
            "leaf",
            image,
            roles,
        )
        leaf.rotation_euler.y = rotation
        parts.append(leaf)
    return join_parts(parts, name, image)


def export_model(obj, name: str) -> None:
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    filepath = MODEL_DIR / f"{name}.fbx"
    bpy.ops.export_scene.fbx(
        filepath=str(filepath),
        use_selection=True,
        object_types={"MESH"},
        axis_forward="-Z",
        axis_up="Y",
        apply_unit_scale=False,
        add_leaf_bones=False,
        bake_anim=False,
        path_mode="STRIP",
    )


def build_models():
    creators = [
        ("MateVacio3D", lambda: create_mate("MateVacio3D", "empty")),
        ("MateConYerba3D", lambda: create_mate("MateConYerba3D", "dry")),
        ("MatePreparado3D", lambda: create_mate("MatePreparado3D", "prepared")),
        ("MateLavado3D", lambda: create_mate("MateLavado3D", "washed")),
        ("Termo3D", lambda: create_thermo("Termo3D")),
        (
            "YerbaEconomica3D",
            lambda: create_yerba("YerbaEconomica3D", "economica"),
        ),
        ("YerbaMedia3D", lambda: create_yerba("YerbaMedia3D", "media")),
        ("YerbaPremium3D", lambda: create_yerba("YerbaPremium3D", "premium")),
    ]
    built = {}
    for name, creator in creators:
        clear_scene()
        obj = creator()
        export_model(obj, name)
        built[name] = str(MODEL_DIR / f"{name}.fbx")
    return built


def look_at(obj, point):
    direction = Vector(point) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_preview():
    clear_scene()
    preview_objects = [
        (create_mate("PreviewMateVacio", "empty"), (-2.55, 0.75, 0), 4.4),
        (create_mate("PreviewMateCargado", "dry"), (-0.85, 0.75, 0), 4.4),
        (create_mate("PreviewMatePreparado", "prepared"), (0.85, 0.75, 0), 4.4),
        (create_mate("PreviewMateLavado", "washed"), (2.55, 0.75, 0), 4.4),
        (create_thermo("PreviewTermo"), (-2.55, -0.95, 0), 3.6),
        (create_yerba("PreviewYerbaEco", "economica"), (-0.85, -0.95, 0), 4.2),
        (create_yerba("PreviewYerbaMedia", "media"), (0.85, -0.95, 0), 4.2),
        (create_yerba("PreviewYerbaPremium", "premium"), (2.55, -0.95, 0), 4.2),
    ]
    for obj, (x, y, z), magnification in preview_objects:
        obj.location = (x, y, z)
        obj.scale = (magnification,) * 3

    bpy.ops.mesh.primitive_plane_add(size=12, location=(0, 0, -0.01))
    floor = bpy.context.object
    floor_mat = bpy.data.materials.new("Floor")
    floor_mat.diffuse_color = (0.035, 0.055, 0.042, 1)
    floor.data.materials.append(floor_mat)

    world = bpy.context.scene.world or bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (
        0.012,
        0.018,
        0.014,
        1,
    )
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.28

    bpy.ops.object.light_add(type="AREA", location=(-3.5, -4.5, 6.0))
    key = bpy.context.object
    key.data.energy = 1150
    key.data.shape = "DISK"
    key.data.size = 5.0
    look_at(key, (0, 0, 0.7))
    bpy.ops.object.light_add(type="AREA", location=(4.5, 1.5, 4.0))
    fill = bpy.context.object
    fill.data.energy = 850
    fill.data.color = (0.55, 0.75, 0.62)
    fill.data.size = 4.0
    look_at(fill, (0, 0, 0.6))

    bpy.ops.object.camera_add(location=(6.7, -10.5, 6.4))
    camera = bpy.context.object
    camera.data.lens = 57
    look_at(camera, (0, 0, 0.78))
    bpy.context.scene.camera = camera

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1400
    scene.render.resolution_y = 900
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(PREVIEW)
    scene.render.film_transparent = False
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.look = "AgX - Medium High Contrast"
    bpy.ops.wm.save_as_mainfile(filepath=str(ART_DIR / "MateArgentino_Models.blend"))
    bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    build_models()
    setup_preview()
    print(f"Generated custom PZ models in {MODEL_DIR}")
    print(f"Rendered preview to {PREVIEW}")
