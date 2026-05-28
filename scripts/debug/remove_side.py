"""Remove stale LeftSideStep action from master.blend."""
import bpy, os
path = r"C:\Dev\Auto-AnimateV2\temp\MainCharacter\master.blend"
bpy.ops.wm.open_mainfile(filepath=path)
if "LeftSideStep" in bpy.data.actions:
    bpy.data.actions.remove(bpy.data.actions["LeftSideStep"])
    print("Removed stale LeftSideStep")
if os.path.exists(path):
    os.remove(path)
bpy.ops.wm.save_as_mainfile(filepath=path)
