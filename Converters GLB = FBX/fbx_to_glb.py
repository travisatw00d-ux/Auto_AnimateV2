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

def main():
    args = parse_args(argv)
    fbx_path = os.path.abspath(args.get('fbx', ''))
    tex_glb_path = os.path.abspath(args.get('texture-glb', '')) if args.get('texture-glb') else None
    output = os.path.abspath(args.get('output', ''))

    if not os.path.exists(fbx_path):
        print(f"ERROR: File not found: {fbx_path}")
        sys.exit(1)

    fbx_dir = os.path.dirname(fbx_path)
    fbx_name = os.path.splitext(os.path.basename(fbx_path))[0]

    # Clean scene
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = 'METRIC'
    bpy.context.scene.unit_settings.scale_length = 1.0

    # ---- Import FBX ----
    bpy.ops.import_scene.fbx(filepath=fbx_path, use_anim=True)

    # DEBUG: list everything in the scene
    print("=== Objects in scene ===")
    for o in bpy.data.objects:
        dims = o.dimensions if o.type == 'MESH' else (0,0,0)
        print(f"  {o.name}: type={o.type}, scale={tuple(o.scale)}, "
              f"dimensions=({dims[0]:.3f}, {dims[1]:.3f}, {dims[2]:.3f})")

    all_meshes = [o for o in bpy.data.objects if o.type == 'MESH']
    armature = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)

    # ---- Debug: print world-space bone lengths if armature exists ----
    if armature:
        s = armature.scale.x
        b_lens = [b.length * s for b in armature.data.bones]
        print(f"Armature: {armature.name}, {len(b_lens)} bones, "
              f"scale={s:.3f}, avg world bone={sum(b_lens)/len(b_lens):.3f}m")

    # ---- Scale correction: check if model is unreasonably large (>100m) ----
    max_dim = max((max(m.dimensions) for m in all_meshes if m.dimensions), default=0)
    print(f"Scale check: max mesh dimension = {max_dim:.1f}m")

    if max_dim > 100:
        print(f"Scale correction needed: max dimension {max_dim:.1f}m > 100m")
        print(f"Applying 0.01 scale to vertex data (cm -> m)")
        for obj in bpy.data.objects:
            if obj.type == 'MESH' and obj.data:
                for v in obj.data.vertices:
                    v.co *= 0.01
                obj.data.update()
        for obj in bpy.data.objects:
            if obj.type == 'ARMATURE' and obj.data:
                bpy.context.view_layer.objects.active = obj
                bpy.ops.object.mode_set(mode='EDIT')
                for b in obj.data.edit_bones:
                    b.head *= 0.01
                    b.tail *= 0.01
                bpy.ops.object.mode_set(mode='OBJECT')
                obj.data.update()
        for obj in bpy.data.objects:
            obj.scale = (1.0, 1.0, 1.0)
        all_meshes = [o for o in bpy.data.objects if o.type == 'MESH']
        armature = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
        for m in all_meshes:
            print(f"  after scale: {m.name} dimensions=({m.dimensions[0]:.3f}, "
                  f"{m.dimensions[1]:.3f}, {m.dimensions[2]:.3f})")

    # ---- Debug: mesh details ----
    print("=== Mesh details ===")
    for m in all_meshes:
        vgs = [vg.name for vg in m.vertex_groups]
        mods = [(mod.type, mod.object.name if mod.object else None) for mod in m.modifiers]
        print(f"  {m.name}: {len(m.data.vertices)} verts, {len(m.data.polygons)} polys, " 
              f"{len(vgs)} vgroups, modifiers={mods}")
        for slot in m.material_slots:
            mat = slot.material
            if mat and mat.node_tree:
                for node in mat.node_tree.nodes:
                    if node.type == 'TEX_IMAGE' and node.image:
                        img = node.image
                        print(f"    tex: {img.name} ({img.size[0]}x{img.size[1]}, "
                              f"{img.colorspace_settings.name})")

    # ---- Bake armature scale into bones (so armature scale = (1,1,1) for GLTF) ----
    if armature:
        s = armature.scale.x
        if abs(s - 1.0) > 0.001:
            print(f"Baking armature scale {s:.3f} into bones (resetting to 1.0)")
            bpy.context.view_layer.objects.active = armature
            bpy.ops.object.mode_set(mode='EDIT')
            for b in armature.data.edit_bones:
                b.head *= s
                b.tail *= s
            bpy.ops.object.mode_set(mode='OBJECT')
            armature.scale = (1.0, 1.0, 1.0)

    # ---- Identify skinned meshes (exclude orphan spheres) ----
    skinned_meshes = []
    for m in all_meshes:
        bone_names = {b.name for b in (armature.data.bones if armature else [])}
        vg_names = {vg.name for vg in m.vertex_groups}
        matching = bone_names & vg_names
        is_skinned = armature and len(matching) >= 5 and any(
            mod.type == 'ARMATURE' and mod.object == armature for mod in m.modifiers)
        if is_skinned:
            skinned_meshes.append(m)
        else:
            print(f"  SKIP (not skinned): {m.name} ({len(matching)} matching vgroups)")

    if not skinned_meshes:
        print("WARNING: No skinned meshes found, falling back to all meshes")
        skinned_meshes = all_meshes

    for mesh in skinned_meshes:
        has_mod = any(m.type == 'ARMATURE' and m.object == armature for m in mesh.modifiers)
        if not has_mod and armature:
            mod = mesh.modifiers.new(name='Armature', type='ARMATURE')
            mod.object = armature

    print(f"Exporting: armature={armature.name if armature else 'NONE'}, "
          f"skinned meshes={[m.name for m in skinned_meshes]}")

    # ---- If a texture GLB was provided, transfer its material ----
    if tex_glb_path and os.path.isfile(tex_glb_path) and skinned_meshes:
        fbx_objs = set(bpy.data.objects)
        print(f"Importing texture GLB: {tex_glb_path}")
        bpy.ops.import_scene.gltf(filepath=tex_glb_path)
        tex_mesh = next((o for o in bpy.data.objects if o.type == 'MESH' and o not in fbx_objs), None)
        if tex_mesh and tex_mesh.data.materials and skinned_meshes[0]:
            mat = tex_mesh.data.materials[0]
            skinned_meshes[0].data.materials.clear()
            skinned_meshes[0].data.materials.append(mat)
            print(f"Transferred material '{mat.name}' from texture GLB")
        for o in list(bpy.data.objects):
            if o not in fbx_objs:
                bpy.data.objects.remove(o, do_unlink=True)
        for m in list(bpy.data.meshes):
            if m.users == 0:
                bpy.data.meshes.remove(m)
    else:
        # ---- Texture lookup for unloaded images ----
        texture_exts = {'.png', '.jpg', '.jpeg', '.tga', '.bmp'}
        texture_candidates = []
        if os.path.isdir(fbx_dir):
            for root, dirs, files in os.walk(fbx_dir):
                for f in files:
                    if os.path.splitext(f)[1].lower() in texture_exts:
                        texture_candidates.append(os.path.join(root, f))

        if texture_candidates:
            for img in list(bpy.data.images):
                if img.has_data:
                    continue
                img_name_lower = img.name.lower()
                img_words = set(img_name_lower.replace('-', ' ').replace('_', ' ').replace('.', ' ').split())
                best = None
                best_score = 0
                for candidate in texture_candidates:
                    c_name = os.path.splitext(os.path.basename(candidate))[0].lower()
                    c_words = set(c_name.replace('-', ' ').replace('_', ' ').replace('.', ' ').split())
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

    # ---- Pack all textures into memory ----
    bpy.ops.file.pack_all()

    # ---- Select ONLY what we want to export ----
    bpy.ops.object.select_all(action='DESELECT')
    if armature:
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
    for m in skinned_meshes:
        m.select_set(True)

    # ---- Export GLB (use_selection=True is critical!) ----
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

if __name__ == "__main__":
    main()
