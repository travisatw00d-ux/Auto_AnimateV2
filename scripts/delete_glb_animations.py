"""
Delete animations by index from a GLB file and re-export.
Usage: blender --background --python delete_glb_animations.py -- model.glb indices
  indices: comma-separated 1-based numbers, e.g. "1,3,5"
"""
import bpy, sys, os

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2:
        print("Usage: delete_glb_animations.py -- model.glb 1,3,5")
        sys.exit(1)

    model_glb = args[0]
    indices_str = args[1]

    if not os.path.exists(model_glb):
        print(f"ERROR: File not found: {model_glb}")
        sys.exit(1)

    # Parse indices
    try:
        delete_indices = {int(x.strip()) for x in indices_str.split(',') if x.strip()}
    except ValueError:
        print("ERROR: Invalid index format - use comma-separated numbers")
        sys.exit(1)

    if not delete_indices:
        print("No indices specified - nothing to do")
        sys.exit(0)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=model_glb)

    # Build sorted list matching list_glb_animations.py ordering
    all_actions = [a for a in bpy.data.actions if a.name not in ('Action',) and a.fcurves]
    all_actions.sort(key=lambda a: a.name)

    total = len(all_actions)
    if total == 0:
        print("No animations found in GLB")
        sys.exit(1)

    # Validate
    max_idx = total
    invalid = [i for i in delete_indices if i < 1 or i > max_idx]
    if invalid:
        print(f"ERROR: Invalid index(es): {invalid} - valid range is 1-{max_idx}")
        sys.exit(1)

    # Collect names before removal
    to_delete_names = [all_actions[i - 1].name for i in sorted(delete_indices, reverse=True)]

    # Remove actions (reverse order so indices stay valid during iteration)
    for i in sorted(delete_indices, reverse=True):
        action = all_actions[i - 1]
        bpy.data.actions.remove(action, do_unlink=True)

    # Re-export GLB, overwriting original
    bpy.ops.object.select_all(action='DESELECT')
    for obj in bpy.data.objects:
        obj.select_set(True)
    bpy.ops.export_scene.gltf(
        filepath=model_glb,
        export_format='GLB',
        use_selection=True,
        export_texcoords=True,
        export_normals=True,
        export_skins=True,
        export_animations=True,
        export_image_format='AUTO',
        export_force_sampling=True,
    )

    # Print result
    remaining = [a.name for a in bpy.data.actions if a.fcurves]
    remaining.sort()
    print(f"Deleted ({len(to_delete_names)}): {', '.join(to_delete_names)}")
    if remaining:
        print(f"Remaining ({len(remaining)}): {', '.join(remaining)}")
    else:
        print("No animations remaining on model")
    print(f"GLB overwritten: {model_glb}")

if __name__ == "__main__":
    main()
