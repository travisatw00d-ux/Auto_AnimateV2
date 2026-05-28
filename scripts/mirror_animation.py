"""
Mirror any animation in a GLB file: negate X for location, negate YZ for quaternion
(arm bones excluded from quaternion mirror to avoid shoulder pivot issues).

Usage:
  blender --background --python mirror_animation.py -- <glb_path> <source_anim> <dest_anim>
  
Example:
  blender --background --python mirror_animation.py -- "model.glb" "LeftFrontSideStep" "RightFrontSideStep"
"""
import bpy, sys, os

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(args) < 3:
    print("Usage: blender --background --python mirror_animation.py -- <glb_path> <source_anim> <dest_anim>")
    sys.exit(1)

glb_path = args[0]
src_name = args[1]
dst_name = args[2]

# Bones that should NOT have quaternion mirrored (arms keep original rotation)
NO_QUAT_BONES = ["Clavicle", "Upperarm", "Forearm", "Hand", "Thumb", "Index", "Mid", "Ring", "Pinky", "Elbow"]

# Fresh start
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
for coll in list(bpy.data.collections): bpy.data.collections.remove(coll)
for mesh in list(bpy.data.meshes): bpy.data.meshes.remove(mesh)
for arm in list(bpy.data.armatures): bpy.data.armatures.remove(arm)
for act in list(bpy.data.actions): bpy.data.actions.remove(act)
for mat in list(bpy.data.materials): bpy.data.materials.remove(mat)
for img in list(bpy.data.images): bpy.data.images.remove(img)

bpy.ops.import_scene.gltf(filepath=glb_path)

src = bpy.data.actions.get(src_name)
if not src:
    print(f"ERROR: '{src_name}' not found in {glb_path}")
    sys.exit(1)

old = bpy.data.actions.get(dst_name)
if old:
    bpy.data.actions.remove(old)

dst = src.copy()
dst.name = dst_name

for fc in list(dst.fcurves):
    dp = fc.data_path
    path, dot, attr = dp.rpartition('.')

    # Negate X for location
    if attr == 'location' and fc.array_index == 0:
        for kp in fc.keyframe_points:
            kp.co.y = -kp.co.y
            kp.handle_left.y = -kp.handle_left.y
            kp.handle_right.y = -kp.handle_right.y

    # Negate YZ for rotation quaternion (skip arm bones)
    if attr == 'rotation_quaternion' and fc.array_index in (2, 3):
        skip = any(kw in dp for kw in NO_QUAT_BONES)
        if not skip:
            for kp in fc.keyframe_points:
                kp.co.y = -kp.co.y
                kp.handle_left.y = -kp.handle_left.y
                kp.handle_right.y = -kp.handle_right.y

# Set root Y offset to 0.17
dp_root = 'pose.bones["RL_BoneRoot"].location'
for fc in dst.fcurves:
    if fc.data_path == dp_root and fc.array_index == 1:
        for kp in fc.keyframe_points:
            kp.co.y = 0.17
            kp.handle_left.y = 0.17
            kp.handle_right.y = 0.17
        break

print(f"Mirrored: {src_name} -> {dst_name}")

# Keep only armature + mesh
keep = {'Armature.001', 'tripo_node_25fa9213_3918_48e4_9500_07f6d78ef73cmesh.001'}
for o in list(bpy.data.objects):
    if o.name not in keep:
        md = o.data if o.type == 'MESH' else None
        bpy.data.objects.remove(o, do_unlink=True)
        if md and md.users == 0:
            bpy.data.meshes.remove(md)

bpy.ops.export_scene.gltf(
    filepath=glb_path,
    export_format='GLB',
    export_texcoords=True,
    export_normals=True,
    export_skins=True,
    export_animations=True,
    export_morph=False,
    export_image_format='JPEG'
)
print(f"GLB updated: {glb_path}")

