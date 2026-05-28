"""Extract a single animation clip from a GLB file into a separate GLB.
Usage: blender --background --python extract_anim.py -- source.glb animation_name output.glb
"""
import bpy, sys, os
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(args) < 3:
    print("Usage: extract_anim.py -- source.glb anim_name output.glb"); sys.exit(1)
src_glb, anim_name, out_glb = args[0], args[1], args[2]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.gltf(filepath=src_glb)

# Remove all actions except the target one
for a in list(bpy.data.actions):
    if a.name != anim_name:
        bpy.data.actions.remove(a)

# Remove actions with no fcurves
for a in list(bpy.data.actions):
    if not a.fcurves:
        bpy.data.actions.remove(a)

# Set up NLA for the single action
arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
if arm:
    if arm.animation_data is None:
        arm.animation_data_create()
    for t in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(t)
    arm.animation_data.action = None
    for a in bpy.data.actions:
        if a.fcurves:
            trk = arm.animation_data.nla_tracks.new()
            trk.name = a.name
            stp = trk.strips.new(a.name, 1, a)
            stp.frame_start = 1
            stp.frame_end = max(int(a.frame_range[1]), 1)
    arm.animation_data.use_nla = True

# Select only armature + skinned meshes
arm_bone_names = {b.name for b in arm.data.bones} if arm else set()
bpy.ops.object.select_all(action='DESELECT')
if arm:
    arm.select_set(True)
for obj in bpy.data.objects:
    if obj.type == 'MESH':
        vg_names = {vg.name for vg in obj.vertex_groups} if obj.vertex_groups else set()
        if vg_names.intersection(arm_bone_names):
            obj.select_set(True)

bpy.ops.export_scene.gltf(
    filepath=out_glb, export_format="GLB",
    use_selection=True,
    export_animations=True, export_nla_strips=True,
    export_skins=True, export_image_format="AUTO",
    export_texcoords=True, export_normals=True,
    export_materials="EXPORT", export_apply=True,
)
print(f"Exported: {out_glb}")
