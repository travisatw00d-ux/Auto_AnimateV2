"""Print bone names from a BVH file."""
import bpy, sys, os
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not args: sys.exit(1)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_anim.bvh(filepath=args[0])
arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
if arm:
    print(f"BVH bones ({len(arm.data.bones)}):")
    for b in arm.data.bones:
        heirs = ', children: ' + ', '.join(c.name for c in b.children) if b.children else ''
        print(f"  {b.name}{heirs}")
    action = arm.animation_data.action if arm.animation_data else None
    if action:
        print(f"Action: {action.name}, frames: {int(action.frame_range[0])}-{int(action.frame_range[1])}")
else:
    print("No armature found in BVH")
