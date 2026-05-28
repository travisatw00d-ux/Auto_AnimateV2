"""
Import existing animation actions from a GLB file into master.blend.
Preserves animations by capturing fcurve data and recreating actions.
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

    # Step 1: Import GLB and capture fcurve data
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=model_glb)

    glb_actions = []
    for a in bpy.data.actions:
        if 'T-Pose' in a.name or a.name == 'Action' or not a.fcurves:
            continue
        name = a.name
        for s in ('.001','.002','.003'):
            if name.endswith(s): name = name[:-len(s)]
        fcurve_data = []
        for fc in a.fcurves:
            if '.scale' in fc.data_path:
                continue
            pts = [(float(kp.co[0]), float(kp.co[1])) for kp in fc.keyframe_points]
            fcurve_data.append((fc.data_path, fc.array_index, pts))
        glb_actions.append((name, fcurve_data))

    if not glb_actions:
        print("No animations found in GLB - nothing to import")
        return

    print(f"Captured {len(glb_actions)} animations: {[n for n,_ in glb_actions]}")

    # Step 2: Open master.blend and recreate actions with same fcurve data
    bpy.ops.wm.open_mainfile(filepath=master_blend)
    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    if arm is None:
        print("WARNING: No armature in master.blend")
        return

    existing = {a.name for a in bpy.data.actions}
    for name, fcurve_data in glb_actions:
        if name in existing:
            continue
        new = bpy.data.actions.new(name=name)
        new.use_fake_user = True
        for dpath, index, pts in fcurve_data:
            nfc = new.fcurves.new(dpath, index=index)
            nfc.keyframe_points.add(len(pts))
            for i, (t, v) in enumerate(pts):
                nfc.keyframe_points[i].co = (t, v)

    if os.path.exists(master_blend):
        os.remove(master_blend)
    bpy.ops.wm.save_as_mainfile(filepath=master_blend)
    print(f"Master saved: {master_blend}")

if __name__ == "__main__":
    main()
