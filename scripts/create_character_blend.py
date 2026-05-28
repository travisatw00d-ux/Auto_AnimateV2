"""
Import a model FBX and save as a Blender character.blend file.
Usage: blender --background --python create_character_blend.py -- model.fbx character.blend
"""
import bpy, sys, os

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2:
        print("Usage: create_character_blend.py -- model.fbx character.blend")
        sys.exit(1)

    model_fbx = args[0]
    blend_path = args[1]

    if not os.path.exists(model_fbx):
        print(f"ERROR: File not found: {model_fbx}")
        sys.exit(1)

    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=model_fbx, automatic_bone_orientation=True)

    # Ensure mesh has an Armature modifier (FBX round-trip can strip it)
    arm = next((o for o in bpy.data.objects if o.type == 'ARMATURE'), None)
    if arm:
        for obj in bpy.data.objects:
            if obj.type == 'MESH':
                has_arm_mod = any(m.type == 'ARMATURE' for m in obj.modifiers)
                if not has_arm_mod:
                    mod = obj.modifiers.new(name='Armature', type='ARMATURE')
                    mod.object = arm
                    print(f"Added Armature modifier to {obj.name}")

    # Save as blend
    os.makedirs(os.path.dirname(os.path.abspath(blend_path)), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print(f"Created: {blend_path}")

if __name__ == "__main__":
    main()
