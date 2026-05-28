"""
Rebuild master.blend to match the current GLB file.
Imports the GLB into a fresh scene and saves as master.blend.
Usage: blender --background --python sync_master_from_glb.py -- master.blend model.glb
"""
import bpy, sys, os

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2:
        print("Usage: sync_master_from_glb.py -- master.blend model.glb")
        sys.exit(1)

    master_blend = args[0]
    model_glb = args[1]

    if not os.path.exists(model_glb):
        print("No GLB found - cannot sync")
        sys.exit(1)

    # Start fresh, import GLB, save as master
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=model_glb)

    glb_actions = [a for a in bpy.data.actions if a.fcurves and 'T-Pose' not in a.name and a.name != 'Action']
    print(f"GLB animations ({len(glb_actions)}): {[a.name for a in glb_actions]}")

    if os.path.exists(master_blend):
        os.remove(master_blend)
    bpy.ops.wm.save_as_mainfile(filepath=master_blend)
    print(f"Master rebuilt from GLB: {master_blend}")

if __name__ == "__main__":
    main()
