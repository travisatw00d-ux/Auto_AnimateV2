"""
Mirror animation with leg-only name swap + quat YZ negate.
Leg bones (Thigh/Calf/Foot/Toe): name swap L↔R + quat YZ negate
Arms + everything else: position-only (no name swap, no quat change)

Usage:
  blender --background --python mirror_front_step.py -- <glb_path> <source_anim> <dest_anim>
"""
import bpy, sys

args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(args) < 3:
    print("Usage: blender --background --python mirror_front_step.py -- <glb_path> <source_anim> <dest_anim>")
    sys.exit(1)

glb = args[0]
src_name = args[1]
dst_name = args[2]

bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()
for coll in list(bpy.data.collections): bpy.data.collections.remove(coll)
for mesh in list(bpy.data.meshes): bpy.data.meshes.remove(mesh)
for arm in list(bpy.data.armatures): bpy.data.armatures.remove(arm)
for act in list(bpy.data.actions): bpy.data.actions.remove(act)
for mat in list(bpy.data.materials): bpy.data.materials.remove(mat)
for img in list(bpy.data.images): bpy.data.images.remove(img)

bpy.ops.import_scene.gltf(filepath=glb)

src = bpy.data.actions.get(src_name)
if not src:
    print(f"ERROR: '{src_name}' not found")
    sys.exit(1)

old = bpy.data.actions.get(dst_name)
if old:
    bpy.data.actions.remove(old)

dst = src.copy()
dst.name = dst_name

    def is_leg_bone(path):
        return any(kw in path for kw in ["Thigh", "Calf", "Foot", "Toe"])

    leg_paths = set()
    for fc in dst.fcurves:
        if '.' in fc.data_path:
            p = fc.data_path.rsplit('.', 1)[0]
            if is_leg_bone(p):
                leg_paths.add(p)

    mirror_map = {}
    for p in leg_paths:
        for q in leg_paths:
            if p == q: continue
            p_s = p.replace('_L_', '_R_').replace('_L"', '_R"').replace('"L_', '"R_')
            p_s = p_s.replace('_L.', '_R.').replace('_L_', '_R_').replace('_L"', '_R"')
            if p_s == q:
                mirror_map[p] = q; mirror_map[q] = p

    for fc in list(dst.fcurves):
        dp = fc.data_path
        path, _dot, attr = dp.rpartition('.')

        # Location X negate for ALL bones
        if attr == 'location' and fc.array_index == 0:
            for kp in fc.keyframe_points:
                kp.co.y = -kp.co.y
                kp.handle_left.y = -kp.handle_left.y
                kp.handle_right.y = -kp.handle_right.y

        # Leg bones get name swap + quat YZ negate
        if is_leg_bone(dp):
            if path in mirror_map:
                fc.data_path = mirror_map[path] + '.' + attr
            if attr == 'rotation_quaternion' and fc.array_index in (2, 3):
                for kp in fc.keyframe_points:
                    kp.co.y = -kp.co.y
                    kp.handle_left.y = -kp.handle_left.y
                    kp.handle_right.y = -kp.handle_right.y

    # Set root Y offset
    dp_root = 'pose.bones["RL_BoneRoot"].location'
    for fc in dst.fcurves:
        if fc.data_path == dp_root and fc.array_index == 1:
            for kp in fc.keyframe_points:
                kp.co.y = 0.17
                kp.handle_left.y = 0.17
                kp.handle_right.y = 0.17
            break

    print(f"{dst_name}: leg-only mirror (same as sidestep)")

keep = {'Armature.001', 'tripo_node_25fa9213_3918_48e4_9500_07f6d78ef73cmesh.001'}
for o in list(bpy.data.objects):
    if o.name not in keep:
        md = o.data if o.type == 'MESH' else None
        bpy.data.objects.remove(o, do_unlink=True)
        if md and md.users == 0:
            bpy.data.meshes.remove(md)

bpy.ops.export_scene.gltf(
    filepath=glb,
    export_format='GLB',
    export_texcoords=True,
    export_normals=True,
    export_skins=True,
    export_animations=True,
    export_morph=False,
    export_image_format='JPEG'
)
print("GLB exported")

