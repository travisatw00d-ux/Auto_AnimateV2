"""fbx_to_glb.py — Convert FBX to GLB preserving textures and animations.

Usage:
  blender --background --python fbx_to_glb.py -- --fbx file.fbx --output file.glb
  blender --background --python fbx_to_glb.py -- --fbx file.fbx --texture-glb tex.glb --output file.glb
"""
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
tex_glb_path = os.path.abspath(args.get('texture-glb', '')) if args.get('texture-glb') else None
output = os.path.abspath(args.get('output', ''))

if not os.path.exists(fbx_path):
    print(f"ERROR: File not found: {fbx_path}")
    sys.exit(1)

fbx_dir = os.path.dirname(fbx_path)
fbx_name = os.path.splitext(os.path.basename(fbx_path))[0]

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
for b in list(bpy.data.meshes): bpy.data.meshes.remove(b)
for b in list(bpy.data.armatures): bpy.data.armatures.remove(b)
for b in list(bpy.data.actions): bpy.data.actions.remove(b)
for b in list(bpy.data.materials): bpy.data.materials.remove(b)
for b in list(bpy.data.images): bpy.data.images.remove(b)

# ---- Import FBX ----
bpy.ops.import_scene.fbx(filepath=fbx_path, use_anim=True)

armature = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
all_meshes = [o for o in bpy.data.objects if o.type == 'MESH']

print(f"FBX imported: meshes={[m.name for m in all_meshes]}, armature={armature}")

# ---- DEBUG: dump all objects ----
for o in bpy.data.objects:
    dims = o.dimensions if o.type == 'MESH' else (0, 0, 0)
    print(f"  {o.name}: type={o.type}, scale={tuple(o.scale)}, dims=({dims[0]:.3f}, {dims[1]:.3f}, {dims[2]:.3f})")
    if o.type == 'ARM':
        # Actually show armature info
        pass

# ---- Normalize armature scale: bake non-unit scale into bones ----
if armature:
    s = armature.scale.x
    if abs(s - 1.0) > 0.001:
        print(f"Normalizing armature scale: {s:.4f} -> 1.0 (baking into bones)")
        bpy.context.view_layer.objects.active = armature
        bpy.ops.object.mode_set(mode='EDIT')
        for b in armature.data.edit_bones:
            b.head *= s
            b.tail *= s
        bpy.ops.object.mode_set(mode='OBJECT')
        armature.scale = (1.0, 1.0, 1.0)
        # Also adjust mesh vertex positions to match new bone space
        # (original vertices are in world space at ~1m, bones were at 0.0446m world,
        #  now bones are at 0.0446m local with scale 1.0)
        # The mesh already has scale 1.0 and its vertices are at ~1m.
        # No vertex adjustment needed since the bone world positions are preserved.

# ---- Select all and export ----
bpy.ops.object.select_all(action='SELECT')

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
