"""
Import LeftSideStep.bvh (AccuRIG skeleton), convert EULER to QUATERNION,
and save to master.blend preserving all other actions.
"""
import bpy, os, sys, mathutils

master_path = r"C:\Dev\Auto-AnimateV2\temp\MainCharacter\master.blend"
bvh_path = r"C:\Dev\Animations\LeftSideStep.bvh"

bpy.ops.wm.open_mainfile(filepath=master_path)
tgt = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
if tgt is None:
    print("ERROR: No target armature"); sys.exit(1)

if "LeftSideStep" in bpy.data.actions:
    bpy.data.actions.remove(bpy.data.actions["LeftSideStep"])

for pb in tgt.pose.bones:
    pb.rotation_mode = 'QUATERNION'

bpy.ops.import_anim.bvh(filepath=bvh_path, global_scale=1.0)

src = None
for o in bpy.data.objects:
    if o.type == 'ARMATURE' and o != tgt and o.animation_data and o.animation_data.action:
        src = o
        break
if src is None:
    print("ERROR: No source armature with action"); sys.exit(1)

action = src.animation_data.action

# Strip location and scale fcurves
for fc in list(action.fcurves):
    if '.location' in fc.data_path or '.scale' in fc.data_path:
        action.fcurves.remove(fc)

# Collect EULER fcurve data BEFORE removing them
euler_data = {}
for fc in list(action.fcurves):
    if 'rotation_euler' in fc.data_path:
        bone = fc.data_path.split('"')[1]
        if bone not in euler_data:
            euler_data[bone] = {}
        euler_data[bone][fc.array_index] = [(kp.co[0], kp.co[1]) for kp in fc.keyframe_points]

# Remove EULER fcurves and create QUATERNION fcurves
converted = 0
for bone_name, channels in euler_data.items():
    if len(channels) < 3:
        continue
    pts_x = channels.get(0, [])
    pts_y = channels.get(1, [])
    pts_z = channels.get(2, [])
    if not pts_x or not pts_y or not pts_z:
        continue
    path = f'pose.bones["{bone_name}"].rotation_quaternion'
    nw = action.fcurves.new(path, index=0)
    nx = action.fcurves.new(path, index=1)
    ny = action.fcurves.new(path, index=2)
    nz = action.fcurves.new(path, index=3)
    count = len(pts_x)
    nw.keyframe_points.add(count)
    nx.keyframe_points.add(count)
    ny.keyframe_points.add(count)
    nz.keyframe_points.add(count)
    for i in range(count):
        t = pts_x[i][0]
        e = mathutils.Euler((pts_x[i][1], pts_y[i][1], pts_z[i][1]), 'XYZ')
        q = e.to_quaternion()
        nw.keyframe_points[i].co = (t, q.w)
        nx.keyframe_points[i].co = (t, q.x)
        ny.keyframe_points[i].co = (t, q.y)
        nz.keyframe_points[i].co = (t, q.z)
    converted += 1

# Remove the old EULER fcurves after data has been saved
for fc in list(action.fcurves):
    if 'rotation_euler' in fc.data_path:
        action.fcurves.remove(fc)

# Set LINEAR interpolation
for fc in action.fcurves:
    if 'rotation_quaternion' in fc.data_path:
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'

print(f"LeftSideStep: {len(action.fcurves)} fcurves, {converted} bones converted to QUATERNION")

# Transfer to target
if tgt.animation_data is None:
    tgt.animation_data_create()
tgt.animation_data.action = action
action.name = "LeftSideStep"

bpy.data.objects.remove(src, do_unlink=True)

if os.path.exists(master_path):
    os.remove(master_path)
bpy.ops.wm.save_as_mainfile(filepath=master_path)
print(f"Master saved: {master_path}")
