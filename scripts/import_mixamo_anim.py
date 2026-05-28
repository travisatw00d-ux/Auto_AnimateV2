"""
Import Mixamo FBX, rename bones to AccuRIG, transfer action to target armature.
No intermediate FBX export needed - avoids action loss.
Usage: blender --background character.blend --python import_mixamo_anim.py -- char.blend mixamo.fbx output.fbx
"""
import bpy, sys, os, mathutils
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bone_mappings import TO_ACCURIG

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 3:
        print("Usage: blender --bg char.blend --python import_mixamo_anim.py -- char.blend mixamo.fbx output.fbx")
        sys.exit(1)

    char_blend = args[0]
    mixamo_fbx = args[1]
    output_fbx = args[2]

    # Character is already loaded via --background
    tgt = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    if tgt is None:
        print("ERROR: No target armature in character blend")
        sys.exit(1)
    print(f"Target: {tgt.name}")

    # Track existing objects so we can remove Mixamo imports
    existing_objects = set(o.name for o in bpy.data.objects)

    # Import Mixamo FBX
    bpy.ops.import_scene.fbx(filepath=mixamo_fbx, automatic_bone_orientation=True)
    src = next((o for o in bpy.data.objects if o.name not in existing_objects and o.type == 'ARMATURE'), None)
    if src is None:
        print("ERROR: No source armature in Mixamo FBX")
        sys.exit(1)
    print(f"Source: {src.name}")

    # Get the action
    if src.animation_data is None or src.animation_data.action is None:
        print("ERROR: No action on source armature")
        sys.exit(1)
    action = src.animation_data.action
    print(f"Action: {action.name}, frames {int(action.frame_range[0])}-{int(action.frame_range[1])}")

    # Capture source rest quaternions BEFORE renaming (by Mixamo bone name)
    src_rest = {}
    for sb in src.data.bones:
        src_rest[sb.name] = sb.matrix_local.to_quaternion()

    # Capture target rest quaternions (by AccuRIG name)
    tgt_rest = {}
    for tb in tgt.data.bones:
        tgt_rest[tb.name] = tb.matrix_local.to_quaternion()

    # Pre-compute corrections: source has Mixamo names, target has AccuRIG names
    corrections = {}
    for mix_name, acc_name in TO_ACCURIG.items():
        if mix_name in src_rest and acc_name in tgt_rest:
            c = tgt_rest[acc_name].inverted() @ src_rest[mix_name]
            corrections[mix_name] = c
    print(f"Corrections computed for {len(corrections)} bones")
    # Show which bones have significant corrections (non-identity)
    id_q = mathutils.Quaternion((1, 0, 0, 0))
    sig = sum(1 for c in corrections.values() if abs(c.dot(id_q)) < 0.999)
    print(f"Bones with significant rest difference: {sig}/{len(corrections)}")

    # Rename source bones from Mixamo to AccuRIG (for fcurve paths)
    bpy.context.view_layer.objects.active = src
    bpy.ops.object.mode_set(mode='EDIT')
    renamed = 0
    for eb in src.data.edit_bones:
        if eb.name in TO_ACCURIG:
            new_name = TO_ACCURIG[eb.name]
            if new_name not in src.data.edit_bones:
                eb.name = new_name
                renamed += 1
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Renamed {renamed} source bones to AccuRIG")

    # Also rename TARGET bones from Mixamo back to AccuRIG
    # (prep_for_mixamo.py renamed them for upload)
    bpy.context.view_layer.objects.active = tgt
    bpy.ops.object.mode_set(mode='EDIT')
    tgt_renamed = 0
    for eb in tgt.data.edit_bones:
        if eb.name in TO_ACCURIG:
            new_name = TO_ACCURIG[eb.name]
            if new_name not in tgt.data.edit_bones:
                eb.name = new_name
                tgt_renamed += 1
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Renamed {tgt_renamed} target bones back to AccuRIG")

    # Also rename vertex groups on target mesh
    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.name in existing_objects:
            vg_renamed = 0
            for vg in obj.vertex_groups:
                if vg.name in TO_ACCURIG:
                    new_name = TO_ACCURIG[vg.name]
                    if new_name not in obj.vertex_groups:
                        vg.name = new_name
                        vg_renamed += 1
            if vg_renamed:
                print(f"Renamed {vg_renamed} target vertex groups to AccuRIG")

    # Fix fcurve data_paths
    fixed = 0
    for fc in action.fcurves:
        for mix_name, acc_name in TO_ACCURIG.items():
            old = f'pose.bones["{mix_name}"]'
            new = f'pose.bones["{acc_name}"]'
            if old in fc.data_path:
                fc.data_path = fc.data_path.replace(old, new)
                fixed += 1
                break
    print(f"Fixed {fixed} fcurve paths")

    # Strip armature-object-scale fcurves (Mixamo sets 0.01) 
    # AND root bone location fcurves (causes character sway)
    stripped = 0
    for fc in list(action.fcurves):
        if fc.data_path == 'scale' and 'pose.bones' not in fc.data_path:
            action.fcurves.remove(fc)
            stripped += 1
        elif 'RL_BoneRoot' in fc.data_path and '.location' in fc.data_path:
            action.fcurves.remove(fc)
            stripped += 1
    if stripped:
        print(f"Stripped {stripped} scale/location fcurves")

    # Apply axis-alignment correction to keyframes for bones with different rests
    # Group fcurves by bone name
    bone_fcurves = {}
    for fc in action.fcurves:
        if 'rotation_quaternion' not in fc.data_path:
            continue
        bone = fc.data_path.split('"')[1]
        if bone not in bone_fcurves:
            bone_fcurves[bone] = {}
        bone_fcurves[bone][fc.array_index] = fc

    corrected = 0
    for acc_name, fcurves in bone_fcurves.items():
        # Find the corresponding Mixamo name to get the correction
        corr = None
        for mix_name, a_name in TO_ACCURIG.items():
            if a_name == acc_name and mix_name in corrections:
                corr = corrections[mix_name]
                break
        if corr is None:
            continue

        # Apply correction to each keyframe
        if len(fcurves) == 4:
            fc_w = fcurves[0]; fc_x = fcurves[1]; fc_y = fcurves[2]; fc_z = fcurves[3]
            for kp_idx in range(len(fc_w.keyframe_points)):
                q = mathutils.Quaternion((
                    fc_w.keyframe_points[kp_idx].co[1],
                    fc_x.keyframe_points[kp_idx].co[1],
                    fc_y.keyframe_points[kp_idx].co[1],
                    fc_z.keyframe_points[kp_idx].co[1],
                ))
                q_corrected = corr @ q @ corr.inverted()
                fc_w.keyframe_points[kp_idx].co = (fc_w.keyframe_points[kp_idx].co[0], q_corrected.w)
                fc_x.keyframe_points[kp_idx].co = (fc_x.keyframe_points[kp_idx].co[0], q_corrected.x)
                fc_y.keyframe_points[kp_idx].co = (fc_y.keyframe_points[kp_idx].co[0], q_corrected.y)
                fc_z.keyframe_points[kp_idx].co = (fc_z.keyframe_points[kp_idx].co[0], q_corrected.z)
            corrected += 1

    print(f"Corrected {corrected} bones with axis-alignment")

    # Transfer action to target armature
    if tgt.animation_data is None:
        tgt.animation_data_create()
    tgt.animation_data.action = action
    if not any(s.name == tgt.name for s in action.slots):
        for s in list(action.slots): action.slots.remove(s)
        slot = action.slots.new(id_type='OBJECT', name=tgt.name)
    else:
        slot = next(s for s in action.slots if s.name == tgt.name)
    tgt.animation_data.action_slot = slot
    print("Action transferred to target")

    # Rename action to friendly clip name (from animation filename)
    anim_name = os.path.splitext(os.path.basename(mixamo_fbx))[0]
    action.name = anim_name
    print(f"Action renamed: {anim_name}")

    # Remove all Mixamo-imported objects first
    for obj in list(bpy.data.objects):
        if obj.name not in existing_objects:
            bpy.data.objects.remove(obj, do_unlink=True)

    # Save character.blend so user can inspect the result
    bpy.context.scene.render.fps = 30
    bpy.context.scene.frame_set(1)
    bpy.context.scene.frame_end = int(action.frame_range[1])
    bpy.context.view_layer.update()
    if os.path.exists(char_blend): os.remove(char_blend)
    bpy.ops.wm.save_as_mainfile(filepath=char_blend)
    print(f"Saved: {char_blend} (frame range: 1-{bpy.context.scene.frame_end}, fps=30)")

if __name__ == "__main__":
    main()
