"""Merge action: save fcurve data from source, recreate in master. Replaces if name already exists."""
import bpy, sys, os

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2: print("Usage: merge_action.py -- master.blend source.blend"); sys.exit(1)

    master_blend, source_blend = args[0], args[1]

    # Step 1: Extract action data from source blend
    bpy.ops.wm.open_mainfile(filepath=source_blend)
    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    if arm is None or arm.animation_data is None or arm.animation_data.action is None:
        print("ERROR: No action in source"); sys.exit(1)

    source_action = arm.animation_data.action
    action_name = source_action.name
    for s in ('.001','.002','.003'):
        if action_name.endswith(s): action_name = action_name[:-len(s)]

    # Save fcurve data as raw Python tuples
    fcurve_data = []
    for fc in source_action.fcurves:
        pts = [(float(kp.co[0]), float(kp.co[1])) for kp in fc.keyframe_points]
        fcurve_data.append((fc.data_path, fc.array_index, pts))
    print(f"Source: {action_name}, {len(source_action.fcurves)} fcurves, {len(fcurve_data[0][2]) if fcurve_data else 0} pts")

    # Step 2: Create action in master with saved data
    bpy.ops.wm.open_mainfile(filepath=master_blend)
    master_arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    if master_arm is None: print("ERROR: No armature in master"); sys.exit(1)
    existing = {a.name for a in bpy.data.actions}
    if action_name in existing:
        print(f"Action '{action_name}' already exists in master - replacing")
        old = bpy.data.actions[action_name]
        bpy.data.actions.remove(old)

    new = bpy.data.actions.new(name=action_name)
    new.use_fake_user = True
    new.slots.new(id_type='OBJECT', name=master_arm.name)
    for dpath, index, pts in fcurve_data:
        nfc = new.fcurves.new(dpath, index=index)
        nfc.keyframe_points.add(len(pts))
        for i, (t, v) in enumerate(pts):
            nfc.keyframe_points[i].co = (t, v)
        for kp in nfc.keyframe_points:
            kp.interpolation = 'LINEAR'

    bpy.context.scene.render.fps = 30
    # Save directly in-place (no delete-before-save to avoid corruption on crash)
    bpy.ops.wm.save_as_mainfile(filepath=master_blend)
    print(f"Master saved: {master_blend}")

if __name__ == "__main__": main()
