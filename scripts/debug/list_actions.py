"""Debug: list actions with fcurves in a blend file."""
import bpy, sys, os
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if not args: sys.exit(1)
bpy.ops.wm.open_mainfile(filepath=args[0])
names = [a.name for a in bpy.data.actions if a.fcurves]
print(f"DEBUG [{os.path.basename(args[0])}] actions ({len(names)}): {names}")
