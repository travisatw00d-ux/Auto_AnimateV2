"""Print fcurve data_paths from a Mixamo FBX to understand the naming convention."""
import bpy, sys, os
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not args: sys.exit(1)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=args[0], automatic_bone_orientation=True)
arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
if arm:
    print(f"Bones ({len(arm.data.bones)}):")
    for b in list(arm.data.bones)[:10]:
        print(f"  {b.name}")
if arm and arm.animation_data and arm.animation_data.action:
    a = arm.animation_data.action
    paths = set()
    for fc in a.fcurves:
        paths.add(fc.data_path)
    print(f"\nFcurve data_paths ({len(paths)} unique):")
    for p in sorted(paths)[:15]:
        print(f"  {p}")
    print(f"Total fcurves: {len(a.fcurves)}")
