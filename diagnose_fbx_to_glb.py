"""
Diagnostic: Import FBX → Export GLB → Re-import GLB → Compare.
Run: blender --background --python diagnose_fbx_to_glb.py -- input.fbx output.glb
"""
import bpy, sys, os, json

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(argv) < 2:
    print("Usage: diagnose_fbx_to_glb.py -- input.fbx output.glb")
    sys.exit(1)

fbx_path = os.path.abspath(argv[0])
glb_path = os.path.abspath(argv[1])

def dump_scene(label):
    print(f"\n=== {label} ===")
    for o in bpy.data.objects:
        d = o.dimensions if o.type == 'MESH' else (0,0,0)
        print(f"  [{o.name}] type={o.type} loc={tuple(o.location)} "
              f"rot={tuple(o.rotation_euler)} scale={tuple(o.scale)} "
              f"dims=({d[0]:.4f},{d[1]:.4f},{d[2]:.4f}) parent={o.parent.name if o.parent else None}")
        if o.type == 'MESH':
            m = o.data
            vgs = [vg.name for vg in o.vertex_groups]
            mods = [(mod.type, mod.object.name if mod.object else None) for mod in o.modifiers]
            print(f"    verts={len(m.vertices)} polys={len(m.polygons)} "
                  f"vgroups={len(vgs)} mods={mods}")
            if vgs:
                print(f"    sample vgroups={vgs[:5]}...")
            for slot in o.material_slots:
                if slot.material and slot.material.node_tree:
                    for n in slot.material.node_tree.nodes:
                        if n.type == 'TEX_IMAGE' and n.image:
                            print(f"    tex={n.image.name} {n.image.size[0]}x{n.image.size[1]} "
                                  f"cs={n.image.colorspace_settings.name}")
        if o.type == 'ARMATURE':
            bones = o.data.bones
            b_lens = [b.length for b in bones]
            print(f"    bones={len(bones)} avg_len={sum(b_lens)/len(b_lens):.4f} "
                  f"min={min(b_lens):.4f} max={max(b_lens):.4f}")
            # Check first bone world position
            import mathutils
            if bones:
                b = bones[0]
                mat = o.matrix_world @ b.matrix_local
                print(f"    first bone: '{b.name}' local_head={tuple(b.head_local)} "
                      f"world_pos={tuple(mat.to_translation())}")
    print(f"  --- total objects: {len(bpy.data.objects)} ---")

# ── Phase 1: Import FBX ──
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path, use_anim=True)
dump_scene("FBX IMPORTED")

armature = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
all_meshes = [o for o in bpy.data.objects if o.type == 'MESH']

# Record FBX state for later comparison
fbx_object_names = {o.name for o in bpy.data.objects}
fbx_mesh_count = len(all_meshes)

# ── Phase 2: Export to GLB ──
bpy.ops.object.select_all(action='SELECT')
bpy.ops.export_scene.gltf(
    filepath=glb_path,
    export_format='GLB',
    export_texcoords=True,
    export_normals=True,
    export_skins=True,
    export_animations=True,
    export_morph=False,
    export_image_format='AUTO',
)
glb_size = os.path.getsize(glb_path)
print(f"\nGLB exported: {glb_path} ({glb_size} bytes)")

# ── Phase 3: Re-import GLB into fresh scene ──
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=glb_path)
dump_scene("GLB RE-IMPORTED")

# ── Phase 4: Compare ──
print("\n=== COMPARISON ===")
print(f"FBX objects: {fbx_object_names}")
print(f"GLB objects: {[o.name for o in bpy.data.objects]}")
print(f"FBX mesh count: {fbx_mesh_count}")
print(f"GLB mesh count: {len([o for o in bpy.data.objects if o.type == 'MESH'])}")
print(f"GLB size: {glb_size} bytes")

# Check if there are unexpected meshes in GLB
glb_meshes = [o for o in bpy.data.objects if o.type == 'MESH']
glb_arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
print(f"GLB armature: {glb_arm.name if glb_arm else 'NONE'}")
if glb_arm:
    glb_bones = glb_arm.data.bones
    b_lens = [b.length for b in glb_bones]
    print(f"GLB bones: {len(glb_bones)} avg_len={sum(b_lens)/len(b_lens):.4f}")
    import mathutils
    if glb_bones:
        b = glb_bones[0]
        mat = glb_arm.matrix_world @ b.matrix_local
        print(f"GLB first bone: '{b.name}' local_head={tuple(b.head_local)} "
              f"world_pos={tuple(mat.to_translation())}")

# Check mesh dimensions in GLB
for m in glb_meshes:
    d = m.dimensions
    print(f"GLB mesh '{m.name}': dims=({d[0]:.4f},{d[1]:.4f},{d[2]:.4f}) "
          f"scale={tuple(m.scale)}")

print("\nDiagnostic complete.")
