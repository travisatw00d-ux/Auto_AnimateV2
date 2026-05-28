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

fbx_mesh = next((o for o in bpy.data.objects if o.type == 'MESH'), None)
fbx_arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)

print(f"FBX imported: mesh={fbx_mesh}, armature={fbx_arm}")

# ---- If a texture GLB was provided, transfer its material ----
if tex_glb_path and os.path.isfile(tex_glb_path):
    fbx_objs = set(bpy.data.objects)
    print(f"Importing texture GLB: {tex_glb_path}")
    bpy.ops.import_scene.gltf(filepath=tex_glb_path)
    tex_mesh = next((o for o in bpy.data.objects if o.type == 'MESH' and o not in fbx_objs), None)
    if tex_mesh and tex_mesh.data.materials and fbx_mesh:
        mat = tex_mesh.data.materials[0]
        fbx_mesh.data.materials.clear()
        fbx_mesh.data.materials.append(mat)
        print(f"Transferred material '{mat.name}' from texture GLB")
    for o in list(bpy.data.objects):
        if o not in fbx_objs:
            bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes):
        if m.users == 0: bpy.data.meshes.remove(m)
else:
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

# ---- Export GLB ----
bpy.ops.object.select_all(action='SELECT')
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
print(f"Exported: {output}")
