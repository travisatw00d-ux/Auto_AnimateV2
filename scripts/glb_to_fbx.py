"""
Convert a .glb file to .fbx format.
Usage: blender --background --python glb_to_fbx.py -- input.glb output.fbx
"""
import bpy, sys, os

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2:
        print("Usage: glb_to_fbx.py -- input.glb output.fbx")
        sys.exit(1)

    input_path = args[0]
    output_path = args[1]

    if not os.path.exists(input_path):
        print(f"ERROR: File not found: {input_path}")
        sys.exit(1)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=input_path)

    armature = None
    meshes = []

    for obj in bpy.data.objects:
        if obj.type == 'ARMATURE':
            armature = obj
        elif obj.type == 'MESH':
            meshes.append(obj)

    for mesh in meshes:
        # Ensure armature modifier points to the armature
        has_mod = any(m.type == 'ARMATURE' and m.object == armature for m in mesh.modifiers)
        if not has_mod and armature:
            mod = mesh.modifiers.new(name='Armature', type='ARMATURE')
            mod.object = armature
        # Parent mesh to armature so FBX links them
        if mesh.parent != armature:
            mesh.parent = armature

    # Explicitly select armature and meshes
    print(f"Armature: {armature.name if armature else 'NONE'}")
    print(f"Meshes: {[m.name for m in meshes]}")
    for m in meshes:
        bone_names = {b.name for b in (armature.data.bones if armature else [])}
        vg_names = {vg.name for vg in m.vertex_groups}
        matching = bone_names & vg_names
        mods = [(mod.type, mod.object.name if mod.object else None) for mod in m.modifiers]
        print(f"  {m.name}: {len(m.vertex_groups)} vgroups, "
              f"{len(matching)} match bones, "
              f"modifiers={mods}")

    bpy.ops.object.select_all(action='DESELECT')
    if armature:
        armature.select_set(True)
        bpy.context.view_layer.objects.active = armature
    for m in meshes:
        m.select_set(True)

    bpy.ops.export_scene.fbx(
        filepath=output_path,
        use_selection=True,
        object_types={'ARMATURE', 'MESH'},
        add_leaf_bones=False,
        bake_anim=False,
        apply_scale_options='FBX_SCALE_ALL',
        path_mode='COPY',
        embed_textures=True,
        mesh_smooth_type='FACE',
        use_triangulate=True,
        use_mesh_modifiers=True,
        primary_bone_axis='Y',
        secondary_bone_axis='X',
        bake_space_transform=True,
    )
    print(f"Converted: {input_path} -> {output_path}")

if __name__ == "__main__":
    main()
