"""
Fix LeftSideStep shoulder rotation by rotating shoulder bones 180 degrees.
The retargeter maps shoulders incorrectly for this AccuRIG-skeleton BVH.
"""
import bpy, os, mathutils

master_path = r"C:\Dev\Auto-AnimateV2\temp\MainCharacter\master.blend"

bpy.ops.wm.open_mainfile(filepath=master_path)

# Remove the EULER-converted action and redo from the original retargeted version
# Actually, let's just fix the shoulder rotation on whatever version exists
a = bpy.data.actions.get("LeftSideStep")
if a is None:
    print("ERROR: LeftSideStep action not found")
    sys.exit(1)

# Rotate shoulder bones 180 degrees around Z axis (common fix for backwards arms)
fix_rot = mathutils.Quaternion((0, 0, 0, 1))  # identity, will be set per bone
# For CC_Base_L_Clavicle and CC_Base_R_Clavicle, rotate 180 deg around Z
z180 = mathutils.Quaternion((0, 0, 1), 3.14159)  # 180 degrees around Z

# Find and fix clavicle fcurves
import sys
fixed = 0
for fc in a.fcurves:
    if 'rotation_quaternion' not in fc.data_path:
        continue
    bone = fc.data_path.split('"')[1]
    if 'Clavicle' not in bone:
        continue
    # Rotate 180 degrees around Z for each keyframe
    for kp in fc.keyframe_points:
        # Build full quaternion from all 4 channels, then rotate
        pass  # We'll do this differently
    fixed += 1

# Simpler approach: directly modify the quaternion fcurve values
# Group fcurves by bone
bone_fcs = {}
for fc in a.fcurves:
    if 'rotation_quaternion' not in fc.data_path:
        continue
    bone = fc.data_path.split('"')[1]
    if 'Clavicle' not in bone:
        continue
    if bone not in bone_fcs:
        bone_fcs[bone] = {}
    bone_fcs[bone][fc.array_index] = fc

for bone_name, fcs in bone_fcs.items():
    if len(fcs) < 4:
        continue
    fc_w = fcs.get(0); fc_x = fcs.get(1); fc_y = fcs.get(2); fc_z = fcs.get(3)
    if any(fc is None for fc in (fc_w, fc_x, fc_y, fc_z)):
        continue
    for i in range(len(fc_w.keyframe_points)):
        q = mathutils.Quaternion((
            fc_w.keyframe_points[i].co[1],
            fc_x.keyframe_points[i].co[1],
            fc_y.keyframe_points[i].co[1],
            fc_z.keyframe_points[i].co[1],
        ))
        q_fixed = z180 @ q  # rotate 180 degrees around Z
        fc_w.keyframe_points[i].co = (fc_w.keyframe_points[i].co[0], q_fixed.w)
        fc_x.keyframe_points[i].co = (fc_x.keyframe_points[i].co[0], q_fixed.x)
        fc_y.keyframe_points[i].co = (fc_y.keyframe_points[i].co[0], q_fixed.y)
        fc_z.keyframe_points[i].co = (fc_z.keyframe_points[i].co[0], q_fixed.z)
    print(f"Fixed shoulder: {bone_name}")

if os.path.exists(master_path):
    os.remove(master_path)
bpy.ops.wm.save_as_mainfile(filepath=master_path)
print(f"Master saved: {master_path}")
