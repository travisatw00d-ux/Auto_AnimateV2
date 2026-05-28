"""fbx_to_glb.py -- Convert FBX to GLB preserving textures and animations.

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

# ---- Select only skinned meshes + armature (exclude orphan spheres) ----
skinned = []
for m in all_meshes:
    bone_names = {b.name for b in (armature.data.bones if armature else [])}
    vg_names = {vg.name for vg in m.vertex_groups}
    is_skinned = armature and (bone_names & vg_names)
    if is_skinned:
        skinned.append(m)
    else:
        print(f"  SKIP (not skinned): {m.name}")

if not skinned:
    print("WARNING: No skinned meshes found, falling back to all meshes")
    skinned = all_meshes

print(f"Export selection: armature={armature.name if armature else 'NONE'}, "
      f"skinned={[m.name for m in skinned]}")

# ---- If a texture GLB was provided, transfer its material ----
if tex_glb_path and os.path.isfile(tex_glb_path) and skinned:
    fbx_objs = set(bpy.data.objects)
    print(f"Importing texture GLB: {tex_glb_path}")
    bpy.ops.import_scene.gltf(filepath=tex_glb_path)
    tex_mesh = next((o for o in bpy.data.objects if o.type == 'MESH' and o not in fbx_objs), None)
    if tex_mesh and tex_mesh.data.materials and skinned[0]:
        mat = tex_mesh.data.materials[0]
        skinned[0].data.materials.clear()
        skinned[0].data.materials.append(mat)
        print(f"Transferred material '{mat.name}' from texture GLB")
    for o in list(bpy.data.objects):
        if o not in fbx_objs:
            bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        if m.users == 0: bpy.data.meshes.remove(m)
else:
    # ---- Resolve textures from sidecar files ----
    texture_exts = {'.png', '.jpg', '.jpeg', '.tga', '.bmp'}
    texture_candidates = []
    if os.path.isdir(fbx_dir):
        for root, dirs, files in os.walk(fbx_dir):
            for f in files:
                if os.path.splitext(f)[1].lower() in texture_exts:
                    texture_candidates.append(os.path.join(root, f))

    for img in list(bpy.data.images):
        if img.has_data:
            continue
        img_name_lower = img.name.lower()
        img_words = set(img_name_lower.replace('-',' ').replace('_',' ').replace('.',' ').split())
        best = None
        best_score = 0
        for candidate in texture_candidates:
            c_name = os.path.splitext(os.path.basename(candidate))[0].lower()
            c_words = set(c_name.replace('-',' ').replace('_',' ').replace('.',' ').split())
            common = len(img_words & c_words)
            if common > best_score or (common == best_score and c_name == fbx_name.lower()):
                best = candidate
                best_score = common
        if best:
            try:
                img.filepath = best
                img.reload()
                img.update()
                if img.has_data:
                    img.pack()
                    print(f"Loaded texture: {best}")
            except Exception as e:
                print(f"Warning: could not load {best}: {e}")

# ---- Pack textures ----
bpy.ops.file.pack_all()

# ---- Select only what we want to export ----
bpy.ops.object.select_all(action='DESELECT')
if armature:
    armature.select_set(True)
    bpy.context.view_layer.objects.active = armature
for m in skinned:
    m.select_set(True)

# ---- Export GLB ----
bpy.ops.export_scene.gltf(
    filepath=output,
    export_format='GLB',
    use_selection=True,
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
