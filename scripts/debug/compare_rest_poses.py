"""Compare rest poses between a GLB import and the FBX-based character blend."""
import bpy, sys, os

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(args) < 2:
    print("Usage: compare_rest_poses.py -- model.glb master.blend")
    sys.exit(1)

model_glb, master_blend = args[0], args[1]

# Import GLB in fresh session
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=model_glb)
glb_arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
if glb_arm:
    glb_rest = {}
    for b in glb_arm.data.bones:
        glb_rest[b.name] = b.matrix_local
    print(f"GLB armature: {glb_arm.name}, {len(glb_rest)} bones")

# Open master.blend
bpy.ops.wm.open_mainfile(filepath=master_blend)
fbx_arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
if fbx_arm:
    fbx_rest = {}
    for b in fbx_arm.data.bones:
        fbx_rest[b.name] = b.matrix_local
    print(f"FBX armature: {fbx_arm.name}, {len(fbx_rest)} bones")

# Compare rest poses for matching bones
print("\nBone rest pose comparison (bones with >0.5 degree difference):")
count = 0
for name in sorted(set(glb_rest.keys()) & set(fbx_rest.keys())):
    q_glb = glb_rest[name].to_quaternion()
    q_fbx = fbx_rest[name].to_quaternion()
    angle_diff = abs(q_glb.rotation_difference(q_fbx).angle * 180 / 3.14159)
    pos_glb = glb_rest[name].translation
    pos_fbx = fbx_rest[name].translation
    pos_diff = (pos_glb - pos_fbx).length
    if angle_diff > 0.5 or pos_diff > 0.001:
        print(f"  {name}: rot diff={angle_diff:.2f}°, pos diff={pos_diff:.6f}m")
        count += 1
print(f"Total with significant differences: {count}")

# Specific check for right arm bones
print("\nRight arm specific:")
for name in ['CC_Base_R_Clavicle', 'CC_Base_R_Upperarm', 'CC_Base_R_Forearm', 'CC_Base_R_Hand']:
    if name in glb_rest and name in fbx_rest:
        q_glb = glb_rest[name].to_quaternion()
        q_fbx = fbx_rest[name].to_quaternion()
        angle_diff = abs(q_glb.rotation_difference(q_fbx).angle * 180 / 3.14159)
        pos_diff = (glb_rest[name].translation - fbx_rest[name].translation).length
        print(f"  {name}: rot diff={angle_diff:.4f}°, pos diff={pos_diff:.6f}m")
