"""Export blend file to GLB with non-destructive NLA-based multi-clip export."""
import bpy, sys, os

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2:
        print("Usage: export_glb.py -- blend_file output.glb"); sys.exit(1)

    blend_file, output_glb = args[0], args[1]
    bpy.ops.wm.open_mainfile(filepath=blend_file)
    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    if arm is None: print("ERROR: No armature"); sys.exit(1)

    # Select only armature + skinned meshes for export
    arm_bone_names = {b.name for b in arm.data.bones}
    bpy.ops.object.select_all(action='DESELECT')
    arm.select_set(True)
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            vg_names = {vg.name for vg in obj.vertex_groups} if obj.vertex_groups else set()
            if vg_names.intersection(arm_bone_names):
                obj.select_set(True)
            else:
                print(f"Excluding unskinned mesh: {obj.name}")
        elif obj.type in ('CAMERA', 'LIGHT'):
            print(f"Excluding {obj.type}: {obj.name}")

    # Ensure all pose bones use QUATERNION
    for pb in arm.pose.bones:
        pb.rotation_mode = 'QUATERNION'

    if arm.animation_data is None:
        arm.animation_data_create()

    # Clear existing NLA tracks (keep active action for NLA evaluation)
    for t in list(arm.animation_data.nla_tracks):
        arm.animation_data.nla_tracks.remove(t)

    # Build NLA strips for each action (skip T-Pose and empty actions)
    anim_actions = [a for a in bpy.data.actions if a.fcurves and 'T-Pose' not in a.name and a.name != 'Action']
    anim_actions.sort(key=lambda a: a.name)

    for a in anim_actions:
        trk = arm.animation_data.nla_tracks.new()
        trk.name = a.name
        stp = trk.strips.new(a.name, 1, a)
        frame_end = max(int(a.frame_range[1]), 1)
        stp.frame_start = 1
        stp.frame_end = frame_end

    arm.animation_data.use_nla = True
    bpy.context.scene.render.fps = 30
    bpy.context.scene.frame_end = max((int(a.frame_range[1]) for a in anim_actions), default=30)

    # Reset pose bones to rest for clean NLA evaluation
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='POSE')
    bpy.ops.pose.select_all(action='SELECT')
    bpy.ops.pose.transforms_clear()
    bpy.ops.object.mode_set(mode='OBJECT')

    # Export GLB
    os.makedirs(os.path.dirname(output_glb), exist_ok=True)
    bpy.ops.export_scene.gltf(
        filepath=output_glb, export_format="GLB",
        use_selection=True,
        export_animations=True, export_nla_strips=True,
        export_skins=True, export_image_format="AUTO",
        export_texcoords=True, export_normals=True,
        export_materials="EXPORT", export_apply=False,
        export_force_sampling=True,
    )
    sz = os.path.getsize(output_glb)/1024
    print(f"Exported: {output_glb} ({sz:.0f} KB, {len(anim_actions)} clips)")

    # Keep actions alive
    for a in bpy.data.actions:
        a.use_fake_user = True

    # Save directly in-place (no delete-before-save to avoid corruption on crash)
    bpy.ops.wm.save_as_mainfile(filepath=blend_file)

if __name__ == "__main__": main()
