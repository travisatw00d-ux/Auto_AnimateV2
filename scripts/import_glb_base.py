"""
Import a GLB file as the character base (armature, mesh, textures, all animations).
Alternative to create_character_blend.py for GLB inputs.
Usage: blender --background --python import_glb_base.py -- model.glb output.blend
"""
import bpy, sys, os

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2:
        print("Usage: import_glb_base.py -- model.glb output.blend")
        sys.exit(1)

    model_glb = args[0]
    output_blend = args[1]

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=model_glb)

    os.makedirs(os.path.dirname(os.path.abspath(output_blend)), exist_ok=True)
    if os.path.exists(output_blend):
        os.remove(output_blend)
    bpy.ops.wm.save_as_mainfile(filepath=output_blend)
    print(f"Saved: {output_blend}")

if __name__ == "__main__":
    main()
