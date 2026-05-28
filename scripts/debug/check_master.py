"""Check LeftSideStep action in master.blend."""
import bpy
bpy.ops.wm.open_mainfile(filepath=r"C:\Dev\Auto-AnimateV2\temp\MainCharacter\master.blend")
a = bpy.data.actions.get("LeftSideStep")
if a:
    rot_euler = [fc for fc in a.fcurves if "rotation_euler" in fc.data_path]
    rot_quat = [fc for fc in a.fcurves if "rotation_quaternion" in fc.data_path]
    print(f"LeftSideStep: {len(a.fcurves)} fcurves")
    print(f"  EULER: {len(rot_euler)}, QUATERNION: {len(rot_quat)}")
    print(f"  Range: {int(a.frame_range[0])}-{int(a.frame_range[1])}")
else:
    print("LeftSideStep NOT in master.blend")
