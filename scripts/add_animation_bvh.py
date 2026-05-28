"""
Step 1: Open character, import BVH, scale source, build bone list.
Step 2: Attempt Rokoko retarget. Fallback to direct constraints if needed.
Step 3: Fix mesh, strip bad fcurves, export FBX.
"""
import bpy, sys, os, mathutils

RETARGET_ID = '_RSL_PIPE'

args = sys.argv[sys.argv.index('--') + 1:]
char_path = args[0]
bvh_path = args[1]
out_dir = args[2].rstrip('\\/"')

char_name = os.path.splitext(os.path.basename(char_path))[0]
anim_name = os.path.splitext(os.path.basename(bvh_path))[0]

# -- Open character --
bpy.ops.wm.open_mainfile(filepath=char_path)

# Find target armature (the AccuRIG skeleton)
target = None
for o in bpy.data.objects:
    if o.type == 'ARMATURE':
        target = o
        break
if not target:
    print("ERROR: No armature found"); sys.exit(1)

# -- Import BVH --
bpy.ops.import_anim.bvh(filepath=bvh_path, global_scale=1.0)

source = None
for o in bpy.data.objects:
    if o.type == 'ARMATURE' and o != target:
        source = o
        break
if not source:
    print("ERROR: BVH import failed"); sys.exit(1)

# -- Scale source to match target --
src_h = max(b.matrix_local.translation.z for b in source.data.bones) - min(b.matrix_local.translation.z for b in source.data.bones)
tgt_bone_h = max(b.matrix_local.translation.z for b in target.data.bones) - min(b.matrix_local.translation.z for b in target.data.bones)
tgt_s = target.scale.x
sf = (tgt_bone_h * tgt_s) / src_h

if abs(sf - 1.0) > 0.001:
    source.data.transform(mathutils.Matrix.Scale(sf, 4))
    source.scale = (1.0, 1.0, 1.0)
print(f"Source scaled by {sf:.4f}")

# -- Bone mapping for fallback --
BONE_MAP = [
    ("Hips","CC_Base_Hip"),("Spine1","CC_Base_Spine01"),("Spine2","CC_Base_Spine02"),
    ("Chest","CC_Base_NeckTwist01"),("Neck1","CC_Base_NeckTwist02"),("Head","CC_Base_Head"),
    ("LeftShoulder","CC_Base_L_Clavicle"),("LeftArm","CC_Base_L_Upperarm"),
    ("LeftForeArm","CC_Base_L_Forearm"),("LeftHand","CC_Base_L_Hand"),
    ("RightShoulder","CC_Base_R_Clavicle"),("RightArm","CC_Base_R_Upperarm"),
    ("RightForeArm","CC_Base_R_Forearm"),("RightHand","CC_Base_R_Hand"),
    ("LeftLeg","CC_Base_L_Thigh"),("LeftShin","CC_Base_L_Calf"),
    ("LeftFoot","CC_Base_L_Foot"),("RightLeg","CC_Base_R_Thigh"),
    ("RightShin","CC_Base_R_Calf"),("RightFoot","CC_Base_R_Foot"),
]

# -- Try Rokoko retarget first --
bpy.context.view_layer.objects.active = source
source.select_set(True)
bpy.context.scene.rsl_retargeting_armature_source = source
bpy.context.scene.rsl_retargeting_armature_target = target
bpy.context.scene.rsl_retargeting_use_pose = 'CURRENT'
bpy.context.scene.rsl_retargeting_auto_scaling = False

print("Building bone list...")
try:
    bpy.ops.rsl.build_bone_list()
except RuntimeError as e:
    print(f"  Bone list error: {e}")
    bl = bpy.context.scene.rsl_retargeting_bone_list
    while len(bl) > 0:
        bl.remove(0)
    bpy.ops.rsl.build_bone_list()

bl = bpy.context.scene.rsl_retargeting_bone_list
mapped = sum(1 for i in bl if i.bone_name_target)
print(f"  {mapped} bones mapped")

print("Running Rokoko retarget...")
try:
    bpy.ops.rsl.retarget_animation()
except:
    import traceback; traceback.print_exc()
    print("  (operator may have failed, checking result...)")

# -- Check if Rokoko produced animation --
has_anim = False
if target.animation_data and target.animation_data.action:
    a = target.animation_data.action
    rot_fcs = [fc for fc in a.fcurves if 'rotation_quaternion' in fc.data_path]
    if len(rot_fcs) > 10:
        has_anim = True
        print(f"Rokoko retargeted: {len(rot_fcs)} rotation fcurves")
    else:
        print(f"Rokoko produced only {len(rot_fcs)} rot fcurves -- using fallback")

# -- Fallback: Direct COPY_ROTATION constraints --
if not has_anim:
    print("Using direct COPY_ROTATION fallback...")
    for bone in target.pose.bones:
        for c in list(bone.constraints):
            if RETARGET_ID in c.name:
                bone.constraints.remove(c)
    if target.animation_data:
        target.animation_data.action = None

    added = 0
    for sn, tn in BONE_MAP:
        sb = source.pose.bones.get(sn)
        tb = target.pose.bones.get(tn)
        if not sb or not tb:
            continue
        c = tb.constraints.new('COPY_ROTATION')
        c.name = sn + RETARGET_ID
        c.target = source
        c.subtarget = sn
        c.target_space = 'WORLD'
        c.owner_space = 'WORLD'
        if tb.parent is None:
            cl = tb.constraints.new('COPY_LOCATION')
            cl.name = sn + RETARGET_ID + '_LOC'
            cl.target = source
            cl.subtarget = sn
            cl.target_space = 'WORLD'
            cl.owner_space = 'WORLD'
        tb.bone.select = True
        added += 1
    print(f"  Added {added} constraints")

    # Bake
    bpy.ops.object.select_all(action='DESELECT')
    target.select_set(True)
    bpy.context.view_layer.objects.active = target
    bpy.ops.object.mode_set(mode='POSE')
    fe = int(source.animation_data.action.frame_range[1])
    bpy.ops.nla.bake(frame_start=1, frame_end=fe, step=1, visual_keying=True, only_selected=True, bake_types={'POSE'})

    if hasattr(target.animation_data, "action_slot"):
        slots = target.animation_data.action_suitable_slots
        if slots: target.animation_data.action_slot = slots[0]

    for bone in target.pose.bones:
        for c in list(bone.constraints):
            if RETARGET_ID in c.name:
                bone.constraints.remove(c)
    bpy.ops.object.mode_set(mode='OBJECT')

# -- Post-process: clear stored pose, strip loc/scale --
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.select_all(action='SELECT')
bpy.ops.pose.transforms_clear()
bpy.ops.object.mode_set(mode='OBJECT')

if target.animation_data and target.animation_data.action:
    a = target.animation_data.action
    bad = [fc for fc in a.fcurves if '.location' in fc.data_path or '.scale' in fc.data_path]
    for fc in bad:
        a.fcurves.remove(fc)
    if bad:
        print(f"Stripped {len(bad)} location/scale fcurves")

# Remove the BVH source armature
bpy.data.objects.remove(source, do_unlink=True)
print("Removed BVH source armature")

# Ensure mesh is at correct scale
for child in target.children:
    if child.type == 'MESH':
        if abs(child.scale.x - 1.0) > 0.001:
            child.scale = (1.0, 1.0, 1.0)
            print(f"Mesh scale reset to 1.0")
        break

# Position camera
for cam in bpy.data.objects:
    if cam.type == 'CAMERA':
        cam.location = (0.0, -3.0, 1.5)
        cam.rotation_euler = (1.4, 0.0, 0.0)
        cam.data.clip_end = 100.0
        break

# Rename action
if target.animation_data and target.animation_data.action:
    target.animation_data.action.name = anim_name

# Force armature transform to identity
target.location = (0.0, 0.0, 0.0)
target.rotation_euler = (0.0, 0.0, 0.0)
target.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
target.scale = (1.0, 1.0, 1.0)

# Save blend
os.makedirs(os.path.dirname(char_path), exist_ok=True)
blend_out = os.path.join(os.path.dirname(char_path), f'{char_name}_{anim_name}.blend')
bpy.context.scene.render.fps = 30
if os.path.exists(blend_out): os.remove(blend_out)
bpy.ops.wm.save_as_mainfile(filepath=blend_out)
print(f"Saved: {blend_out}")

# Export FBX
os.makedirs(out_dir, exist_ok=True)
fbx_out = os.path.join(out_dir, f'{anim_name}.fbx')
bpy.ops.object.select_all(action='DESELECT')
target.select_set(True)
bpy.context.view_layer.objects.active = target
for child in target.children:
    if child.type == 'MESH':
        child.select_set(True)
bpy.ops.export_scene.fbx(filepath=fbx_out, use_selection=True, bake_anim=True, bake_anim_use_all_bones=True, bake_anim_step=1, bake_anim_simplify_factor=0.0, object_types={'ARMATURE','MESH'}, add_leaf_bones=False)
print(f"Exported: {fbx_out}")
print("DONE")
