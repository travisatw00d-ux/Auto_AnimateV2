"""
Take a textured GLB + AccuRIG FBX -> output FBX with Mixamo bone names + working textures.
Usage: blender --background --python prep_for_mixamo.py -- textured.glb accurig.fbx output.fbx
"""
import bpy, sys, os, shutil
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bone_mappings import TO_MIXAMO

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 3:
        print("Usage: prep_for_mixamo.py -- textured.glb accurig.fbx output.fbx")
        sys.exit(1)

    glb_path = args[0]
    fbx_path = args[1]
    output_fbx = args[2]

    for p in [glb_path, fbx_path]:
        if not os.path.exists(p):
            print(f"ERROR: Not found: {p}")
            sys.exit(1)

    bpy.ops.wm.read_factory_settings(use_empty=True)

    # === STEP 1: Import GLB to get textures/materials ===
    print(f"Importing GLB: {os.path.basename(glb_path)}")
    bpy.ops.import_scene.gltf(filepath=glb_path)
    glb_mesh = next((o for o in bpy.data.objects if o.type == 'MESH'), None)
    if glb_mesh is None:
        print("ERROR: No mesh in GLB")
        sys.exit(1)
    print(f"  GLB mesh: {glb_mesh.name} ({len(glb_mesh.data.vertices)} verts, {len(glb_mesh.material_slots)} mats)")

    # Capture GLB material
    glb_mat = glb_mesh.material_slots[0].material if glb_mesh.material_slots else None
    if glb_mat:
        print(f"  Material: {glb_mat.name}")

    # === STEP 2: Import AccuRIG FBX ===
    print(f"Importing FBX: {os.path.basename(fbx_path)}")
    bpy.ops.import_scene.fbx(filepath=fbx_path)

    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    fbx_mesh = next((o for o in bpy.data.objects if o.type == 'MESH' and o != glb_mesh), None)
    if arm is None:
        print("ERROR: No armature in FBX")
        sys.exit(1)
    print(f"  Armature: {arm.name} ({len(arm.data.bones)} bones)")
    if fbx_mesh:
        print(f"  FBX mesh: {fbx_mesh.name} ({len(fbx_mesh.data.vertices)} verts, {len(fbx_mesh.material_slots)} mats)")

    # === STEP 3: Transfer material from GLB mesh to FBX mesh ===
    if glb_mat and fbx_mesh:
        for i, slot in enumerate(fbx_mesh.material_slots):
            slot.material = glb_mat
        print(f"  Material transferred: {glb_mat.name}")

    # === STEP 4: Unpack GLB textures to output folder ===
    out_dir = os.path.dirname(os.path.abspath(output_fbx))
    tex_out = os.path.join(out_dir, "textures")
    os.makedirs(tex_out, exist_ok=True)

    for img in bpy.data.images:
        if img.packed_file:
            fname = img.name
            if not os.path.splitext(fname)[1]:
                fname += ".png"
            img_path = os.path.join(tex_out, fname)
            img.filepath_raw = img_path
            img.save()
            img.unpack(method='REMOVE')
            print(f"  Unpacked: {img.name} ({img.size[0]}x{img.size[1]}) -> {fname}")

    # === STEP 5: Rename bones to Mixamo names ===
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    renamed = 0
    for eb in arm.data.edit_bones:
        if eb.name in TO_MIXAMO:
            new_name = TO_MIXAMO[eb.name]
            if new_name not in arm.data.edit_bones:
                eb.name = new_name
                renamed += 1
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"  Renamed {renamed} bones to Mixamo")

    # Also rename vertex groups on all meshes
    vg_total = 0
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            for vg in obj.vertex_groups:
                if vg.name in TO_MIXAMO:
                    new_name = TO_MIXAMO[vg.name]
                    if new_name not in obj.vertex_groups:
                        vg.name = new_name
                        vg_total += 1
    if vg_total:
        print(f"  Renamed {vg_total} vertex groups to Mixamo names")

    # === STEP 6: Remove GLB mesh ===
    if glb_mesh:
        bpy.data.objects.remove(glb_mesh, do_unlink=True)

    # === STEP 7: Export ===
    print(f"\nExporting: {os.path.basename(output_fbx)}")
    bpy.ops.export_scene.fbx(
        filepath=output_fbx,
        use_selection=False,
        object_types={'ARMATURE', 'MESH'},
        add_leaf_bones=False,
        bake_anim=False,
        path_mode='COPY',
        embed_textures=False,
        apply_scale_options='FBX_SCALE_ALL',
    )
    print(f"Done: {output_fbx}")
    print(f"Textures: {tex_out}")
    print("Ready for Mixamo.com upload")

if __name__ == "__main__":
    main()
