"""
Import existing animation actions from a GLB file into master.blend.
Applies rest-pose correction to match the FBX armature's bone orientations.
Usage: blender --background --python import_glb_animations.py -- model.glb master.blend
"""
import bpy, sys, os, mathutils

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

    # Step 1: Import GLB and capture fcurve data + GLB rest poses
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.gltf(filepath=model_glb)

    glb_arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    glb_rest = {}
    if glb_arm:
        for b in glb_arm.data.bones:
            glb_rest[b.name] = b.matrix_local.to_quaternion()

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

    # Step 2: Open master.blend, capture FBX rest poses, compute corrections
    bpy.ops.wm.open_mainfile(filepath=master_blend)
    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    if arm is None:
        print("WARNING: No armature in master.blend")
        return

    fbx_rest = {}
    for b in arm.data.bones:
        fbx_rest[b.name] = b.matrix_local.to_quaternion()

    corrections = {}
    for name in glb_rest:
        if name in fbx_rest:
            corr = fbx_rest[name].inverted() @ glb_rest[name]
            if abs(corr.angle) > 0.001:
                corrections[name] = corr
    print(f"Rest-pose corrections: {len(corrections)} bones")
    if corrections:
        top = sorted(corrections.items(), key=lambda x: abs(x[1].angle), reverse=True)[:3]
        for n, c in top:
            print(f"  {n}: {c.angle*180/3.14159:.1f}°")

    # Step 3: Create actions with corrected rotation fcurves
    existing = {a.name for a in bpy.data.actions}
    for name, fcurve_data in glb_actions:
        if name in existing:
            print(f"  Skipping {name} (already in master)")
            continue
        new = bpy.data.actions.new(name=name)
        new.use_fake_user = True
        for dpath, index, pts in fcurve_data:
            nfc = new.fcurves.new(dpath, index=index)
            nfc.keyframe_points.add(len(pts))
            for i, (t, v) in enumerate(pts):
                nfc.keyframe_points[i].co = (t, v)

        # Apply rest-pose correction to rotation quaternion keyframes
        bone_fcurves = {}
        for fc in new.fcurves:
            if 'rotation_quaternion' in fc.data_path:
                bone = fc.data_path.split('"')[1]
                if bone not in bone_fcurves:
                    bone_fcurves[bone] = {}
                bone_fcurves[bone][fc.array_index] = fc

        corrected = 0
        for bone_name, fcs in bone_fcurves.items():
            corr = corrections.get(bone_name)
            if corr is None or len(fcs) < 4:
                continue
            fc_w = fcs.get(0); fc_x = fcs.get(1); fc_y = fcs.get(2); fc_z = fcs.get(3)
            if any(fc is None for fc in (fc_w, fc_x, fc_y, fc_z)):
                continue
            for kp_idx in range(len(fc_w.keyframe_points)):
                q = mathutils.Quaternion((
                    fc_w.keyframe_points[kp_idx].co[1],
                    fc_x.keyframe_points[kp_idx].co[1],
                    fc_y.keyframe_points[kp_idx].co[1],
                    fc_z.keyframe_points[kp_idx].co[1],
                ))
                q_c = corr @ q @ corr.inverted()
                fc_w.keyframe_points[kp_idx].co = (fc_w.keyframe_points[kp_idx].co[0], q_c.w)
                fc_x.keyframe_points[kp_idx].co = (fc_x.keyframe_points[kp_idx].co[0], q_c.x)
                fc_y.keyframe_points[kp_idx].co = (fc_y.keyframe_points[kp_idx].co[0], q_c.y)
                fc_z.keyframe_points[kp_idx].co = (fc_z.keyframe_points[kp_idx].co[0], q_c.z)
            corrected += 1
        if corrected:
            print(f"  {name}: corrected {corrected} bones")

    print(f"Added {len(glb_actions)} actions from GLB to master.blend")

    if os.path.exists(master_blend):
        os.remove(master_blend)
    bpy.ops.wm.save_as_mainfile(filepath=master_blend)
    print(f"Master saved: {master_blend}")

if __name__ == "__main__":
    main()
