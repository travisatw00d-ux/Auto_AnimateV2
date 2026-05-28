"""
Rename bones in a Mixamo FBX back to AccuRIG names.
Usage: blender --background --python rename_mixamo.py -- input.fbx output.fbx
"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bone_mappings import TO_ACCURIG

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2:
        print("Usage: rename_mixamo.py -- input_mixamo.fbx output_accurig.fbx")
        sys.exit(1)

    input_fbx = args[0]
    output_fbx = args[1]

    if not os.path.exists(input_fbx):
        print(f"ERROR: File not found: {input_fbx}")
        sys.exit(1)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=input_fbx, automatic_bone_orientation=True)

    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    if arm is None:
        print("ERROR: No armature found in FBX")
        sys.exit(1)

    action = arm.animation_data.action if arm.animation_data else None
    print(f"Action: {action.name if action else 'None'}, bones: {len(arm.data.bones)}")

    # Rename bones in Edit mode
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
    print(f"Renamed {renamed} bones back to AccuRIG")

    # Fix fcurve data_paths
    if action:
        fixed = 0
        for fc in action.fcurves:
            for mix_name, acc_name in TO_ACCURIG.items():
                old = f'pose.bones["{mix_name}"]'
                new = f'pose.bones["{acc_name}"]'
                if old in fc.data_path:
                    fc.data_path = fc.data_path.replace(old, new)
                    fixed += 1
                    break
        print(f"Fixed {fixed} fcurve data paths")

    # Ensure action is properly assigned with a slot (Blender 4.x requirement)
    if action:
        if arm.animation_data is None:
            arm.animation_data_create()
        arm.animation_data.action = action
        if action.slots:
            arm.animation_data.action_slot = action.slots[0]
        else:
            slot = action.slots.new(id_type='OBJECT', name='Slot')
            arm.animation_data.action_slot = slot
        print(f"Action assigned: {action.name}")

    # Export
    bpy.ops.export_scene.fbx(
        filepath=output_fbx,
        use_selection=False,
        object_types={'ARMATURE', 'MESH'},
        add_leaf_bones=False,
        bake_anim=False,
        apply_scale_options='FBX_SCALE_ALL',
    )
    print(f"Exported: {output_fbx}")

if __name__ == "__main__":
    main()
