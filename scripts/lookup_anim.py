"""Lookup animation name by number or name in a GLB file.
Usage: blender --background --python lookup_anim.py -- model.glb source_identifier
Outputs the animation name to stdout."""
import bpy, sys, os
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if len(args) < 2:
    sys.exit(1)
glb = args[0]; identifier = args[1]
bpy.ops.import_scene.gltf(filepath=glb)
names = sorted([a.name for a in bpy.data.actions if a.fcurves and 'T-Pose' not in a.name and a.name != 'Action'])
result = ""
if identifier.isdigit():
    idx = int(identifier) - 1
    if 0 <= idx < len(names):
        result = names[idx]
elif identifier in names:
    result = identifier
if result:
    print(f"ANIM_NAME:{result}")
else:
    print(f"ANIM_NAME:ERROR: '{identifier}' not found", file=sys.stderr)
    sys.exit(1)
