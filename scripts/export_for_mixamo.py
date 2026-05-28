"""
Export AccuRIG FBX with Mixamo bone names for use with Mixamo.com.
Usage: blender --background --python export_mixamo.py -- input.fbx output.fbx
"""
import bpy, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from bone_mappings import TO_MIXAMO

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2:
        print("Usage: export_mixamo.py -- input_accurig.fbx output_mixamo.fbx")
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
        print("ERROR: No armature in FBX")
        sys.exit(1)

    # Rename bones to Mixamo
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode='EDIT')
    renamed = 0
    for eb in arm.data.edit_bones:
        if eb.name in TO_MIXAMO:
            new_name = TO_MIXAMO[eb.name]
            if new_name not in arm.data.edit_bones:
                eb.name = new_name
                renamed += 1
    bpy.ops.object.mode_set(mode='OBJECT')

    # Rename vertex groups
    for obj in bpy.data.objects:
        if obj.type == 'MESH':
            for vg in obj.vertex_groups:
                if vg.name in TO_MIXAMO:
                    vg.name = TO_MIXAMO[vg.name]

    # Export
    bpy.ops.export_scene.fbx(
        filepath=output_fbx,
        use_selection=False,
        object_types={'ARMATURE', 'MESH'},
        add_leaf_bones=False,
        bake_anim=False,
    )
    print(f"Exported Mixamo-ready FBX: {output_fbx}")
    print(f"Renamed {renamed} bones to Mixamo names")

if __name__ == "__main__":
    main()
