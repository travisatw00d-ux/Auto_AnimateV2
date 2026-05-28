import bpy, sys, os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

def parse_args(argv):
    d = {}
    i = 0
    while i < len(argv):
        if argv[i].startswith('--'):
            key = argv[i][2:]
            if i + 1 < len(argv) and not argv[i+1].startswith('--'):
                d[key] = argv[i+1]
                i += 2
            else:
                d[key] = True
                i += 1
        else:
            i += 1
    return d

args = parse_args(argv)
fbx_path = os.path.abspath(args.get('fbx', ''))
output = os.path.abspath(args.get('output', ''))

if not os.path.exists(fbx_path):
    print(f"ERROR: File not found: {fbx_path}")
    sys.exit(1)

def purge_scene():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()
    for coll in list(bpy.data.collections):
        if coll.name != 'Master Collection':
            bpy.data.collections.remove(coll)
    for b in list(bpy.data.meshes): bpy.data.meshes.remove(b)
    for b in list(bpy.data.armatures): bpy.data.armatures.remove(b)
    for b in list(bpy.data.actions): bpy.data.actions.remove(b)
    for b in list(bpy.data.materials): bpy.data.materials.remove(b)
    for b in list(bpy.data.images): bpy.data.images.remove(b)
    for b in list(bpy.data.lights): bpy.data.lights.remove(b)
    for b in list(bpy.data.cameras): bpy.data.cameras.remove(b)
    for b in list(bpy.data.curves): bpy.data.curves.remove(b)
    for b in list(bpy.data.lattices): bpy.data.lattices.remove(b)
    for b in list(bpy.data.metaballs): bpy.data.metaballs.remove(b)
    for b in list(bpy.data.texts): bpy.data.texts.remove(b)
    for b in list(bpy.data.volumes): bpy.data.volumes.remove(b)
    for b in list(bpy.data.grease_pencils): bpy.data.grease_pencils.remove(b)

purge_scene()

# ---- Import FBX ----
bpy.ops.import_scene.fbx(filepath=fbx_path, use_anim=True)

fbx_names = {o.name for o in bpy.data.objects}

armature = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
all_meshes = [o for o in bpy.data.objects if o.type == 'MESH']

print(f"FBX imported: meshes={[m.name for m in all_meshes]}, armature={armature}")

# ---- DEBUG: dump all objects ----
for o in bpy.data.objects:
    dims = o.dimensions if o.type == 'MESH' else (0, 0, 0)
    parent = o.parent.name if o.parent else "None"
    print(f"  {o.name}: type={o.type}, parent={parent}, scale={tuple(round(s,6) for s in o.scale)}, dims=({dims[0]:.3f}, {dims[1]:.3f}, {dims[2]:.3f})")

# ---- Delete any objects that aren't from the FBX import ----
for o in list(bpy.data.objects):
    if o.name not in fbx_names:
        print(f"  Removing non-FBX object: {o.name}")
        bpy.data.objects.remove(o, do_unlink=True)

# ---- Bake armature scale into bones (using transform_apply) ----
if armature and abs(armature.scale.x - 1.0) > 0.001:
    print(f"Applying armature scale: {armature.scale.x:.4f} -> 1.0")
    bpy.context.view_layer.objects.active = armature
    bpy.ops.object.transform_apply(scale=True)

# ---- Apply transforms on meshes too ----
for m in all_meshes:
    if any(abs(s - 1.0) > 0.001 for s in m.scale):
        bpy.context.view_layer.objects.active = m
        bpy.ops.object.transform_apply(scale=True)

# ---- Ensure armature modifier is connected ----
for m in all_meshes:
    for mod in m.modifiers:
        if mod.type == 'ARMATURE' and mod.object != armature:
            print(f"  Fixing armature mod on '{m.name}': {mod.object} -> {armature}")
            mod.object = armature

# ---- Snap to ground: find lowest mesh vertex and move everything down ----
import mathutils
world_min_z = float('inf')
for m in all_meshes:
    mat = m.matrix_world
    for corner in m.bound_box:
        world_corner = mat @ mathutils.Vector(corner)
        world_min_z = min(world_min_z, world_corner.z)

snap_z = world_min_z
if abs(snap_z) > 0.001:
    print(f"Snapping to ground: shifting by {-snap_z:.4f}")
    armature.location.z -= snap_z

# ---- Pack textures ----
bpy.ops.file.pack_all()

# ---- Export GLB ----
bpy.ops.export_scene.gltf(
    filepath=output,
    export_format='GLB',
    export_texcoords=True,
    export_normals=True,
    export_skins=True,
    export_animations=True,
    export_morph=False,
    export_image_format='AUTO',
)
out_size = os.path.getsize(output)
in_size = os.path.getsize(fbx_path)
print(f"Exported: {fbx_path} ({in_size} bytes) -> {output} ({out_size} bytes)")
