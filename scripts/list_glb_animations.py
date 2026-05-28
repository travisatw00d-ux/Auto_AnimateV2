"""
List animation names in a GLB file, write numbered list to a text file.
Usage: blender --background --python list_glb_animations.py -- model.glb output_list.txt
"""
import bpy, sys, os

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2:
        print("Usage: list_glb_animations.py -- model.glb output_list.txt")
        sys.exit(1)

    model_glb = args[0]
    output_file = args[1]

    if not os.path.exists(model_glb):
        print(f"ERROR: File not found: {model_glb}")
        sys.exit(1)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=model_glb)

    names = []
    for a in bpy.data.actions:
        if a.name in ('Action',) or not a.fcurves:
            continue
        names.append(a.name)

    names.sort()

    with open(output_file, 'w', encoding='utf-8') as f:
        for i, name in enumerate(names, 1):
            f.write(f"{i}. {name}\n")

    if names:
        print(f"Found {len(names)} animations, written to {output_file}")
    else:
        print("No animations found in GLB")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("(none)\n")

if __name__ == "__main__":
    main()
