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

    bpy.ops.export_scene.fbx(
        filepath=output_path,
        use_selection=False,
        object_types={'ARMATURE', 'MESH'},
        add_leaf_bones=False,
        bake_anim=False,
        apply_scale_options='FBX_SCALE_ALL',
        path_mode='COPY',
        embed_textures=True,
    )
    print(f"Converted: {input_path} -> {output_path}")

if __name__ == "__main__":
    main()
