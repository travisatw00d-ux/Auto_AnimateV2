"""
Rename bones in character.blend from Mixamo back to AccuRIG.
Used before BVH retargeting (which expects AccuRIG names).
Usage: blender --background character.blend --python revert_to_accurig.py -- character.blend
"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bone_mappings import TO_ACCURIG

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    char_blend = args[0] if args else None

    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    if arm is None:
        print("ERROR: No armature")
        sys.exit(1)

    # Rename bones Mixamo -> AccuRIG
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    renamed = 0
    for eb in arm.data.edit_bones:
        if eb.name in TO_ACCURIG:
            new_name = TO_ACCURIG[eb.name]
            if new_name not in arm.data.edit_bones:
                eb.name = new_name
                renamed += 1
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"Renamed {renamed} bones to AccuRIG")

    # Rename vertex groups
    vg_renamed = 0
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            for vg in obj.vertex_groups:
                if vg.name in TO_ACCURIG:
                    new_name = TO_ACCURIG[vg.name]
                    if new_name not in obj.vertex_groups:
                        vg.name = new_name
                        vg_renamed += 1
    if vg_renamed:
        print(f"Renamed {vg_renamed} vertex groups to AccuRIG")
    else:
        print(f"No vertex groups needed renaming")

    if char_blend:
        bpy.ops.wm.save_as_mainfile(filepath=char_blend)
        print(f"Saved: {char_blend}")

if __name__ == "__main__":
    main()
