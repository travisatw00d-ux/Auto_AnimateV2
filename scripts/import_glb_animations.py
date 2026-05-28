"""
Import existing animation actions from a GLB file into master.blend.
Preserves animations by appending actions directly from the GLB import.
Usage: blender --background --python import_glb_animations.py -- model.glb master.blend
"""
import bpy, sys, os

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2:
        print("Usage: import_glb_animations.py -- model.glb master.blend")
        sys.exit(1)

    model_glb = args[0]
    master_blend = args[1]

    if not os.path.exists(model_glb):
        print(f"ERROR: File not found: {model_glb}")
        sys.exit(1)
    if not os.path.exists(master_blend):
        print(f"ERROR: No master.blend at {master_blend}")
        sys.exit(1)

    # Step 1: Import GLB and save as temp blend
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=model_glb)

    glb_action_names = {a.name for a in bpy.data.actions if a.fcurves and 'T-Pose' not in a.name and a.name != 'Action'}
    if not glb_action_names:
        print("No animations found in GLB - nothing to import")
        return
    print(f"GLB has {len(glb_action_names)} animations: {sorted(glb_action_names)}")

    temp_blend = master_blend + ".glb_import.blend"
    if os.path.exists(temp_blend):
        os.remove(temp_blend)
    bpy.ops.wm.save_as_mainfile(filepath=temp_blend)

    # Step 2: Open master.blend and append actions from temp blend
    bpy.ops.wm.open_mainfile(filepath=master_blend)
    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    if arm is None:
        print("WARNING: No armature in master.blend")
        if os.path.exists(temp_blend):
            os.remove(temp_blend)
        return
    arm_name = arm.name

    with bpy.data.libraries.load(temp_blend, link=False) as (data_from, data_to):
        names_to_load = [n for n in data_from.actions if n not in bpy.data.actions and 'T-Pose' not in n and n != 'Action']
        if names_to_load:
            data_to.actions = names_to_load
            print(f"Appended {len(names_to_load)} actions: {names_to_load}")
        else:
            print("All GLB actions already in master")

    # Fix slot names on appended actions to match master armature
    for a in bpy.data.actions:
        if a.name not in glb_action_names:
            continue
        needs_fix = True
        for s in a.slots:
            if s.name == arm_name:
                needs_fix = False
                break
        if needs_fix:
            for s in list(a.slots):
                a.slots.remove(s)
            a.slots.new(id_type='OBJECT', name=arm_name)

    if os.path.exists(temp_blend):
        os.remove(temp_blend)
    if os.path.exists(master_blend):
        os.remove(master_blend)
    bpy.ops.wm.save_as_mainfile(filepath=master_blend)
    print(f"Master saved with appended GLB animations: {master_blend}")

if __name__ == "__main__":
    main()
