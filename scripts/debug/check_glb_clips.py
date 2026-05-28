"""Check all animation clips in a GLB file."""
import bpy, sys, os
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not args: sys.exit(1)
bpy.ops.import_scene.gltf(filepath=args[0])
for a in bpy.data.actions:
    if a.fcurves:
        rot = len([fc for fc in a.fcurves if 'rotation' in fc.data_path])
        loc = len([fc for fc in a.fcurves if 'location' in fc.data_path])
        print(f"{a.name}: {len(a.fcurves)} fcurves ({rot} rot, {loc} loc), range {int(a.frame_range[0])}-{int(a.frame_range[1])}")
if not any(a.fcurves for a in bpy.data.actions):
    print("No animation clips found")
