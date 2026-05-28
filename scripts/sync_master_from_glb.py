"""
Sync master.blend with the current GLB file.
Reads animation names directly from the GLB binary (no Blender import)
so action names match exactly and armature bone orientations are preserved.
Usage: blender --background --python sync_master_from_glb.py -- master.blend model.glb
"""
import bpy, sys, os, json, struct

def read_glb_animation_names(filepath):
    """Parse GLB binary directly to get animation names without any Blender import."""
    names = []
    with open(filepath, 'rb') as f:
        header = f.read(12)
        if len(header) < 12:
            return names
        while True:
            chunk_head = f.read(8)
            if len(chunk_head) < 8:
                break
            chunk_len = struct.unpack('<I', chunk_head[:4])[0]
            chunk_type = struct.unpack('<I', chunk_head[4:8])[0]
            chunk_data = f.read(chunk_len)
            if chunk_type == 0x4E4F534A:
                gltf = json.loads(chunk_data.decode('utf-8'))
                for anim in gltf.get('animations', []):
                    if 'name' in anim:
                        names.append(anim['name'])
                break
    return names

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 2:
        print("Usage: sync_master_from_glb.py -- master.blend model.glb")
        sys.exit(1)

    master_blend = args[0]
    model_glb = args[1]

    if not os.path.exists(master_blend):
        print("No master.blend - nothing to sync")
        sys.exit(0)

    if not os.path.exists(model_glb):
        print("No GLB found - cannot sync")
        sys.exit(1)

    glb_names = set(read_glb_animation_names(model_glb))
    print(f"GLB animations ({len(glb_names)}): {sorted(glb_names) if glb_names else '(none)'}")

    bpy.ops.wm.open_mainfile(filepath=master_blend)

    removed = 0
    for a in list(bpy.data.actions):
        if a.name in ('T-Pose', 'Action', 'Dope Sheet Action'):
            continue
        try:
            if a.name not in glb_names and a.fcurves:
                bpy.data.actions.remove(a)
                removed += 1
                print(f"  Removed: {a.name}")
        except ReferenceError:
            print(f"  Skipped corrupted action: {a.name}")

    print(f"Removed {removed} stale actions from master")

    if removed > 0:
        bpy.ops.wm.save_as_mainfile(filepath=master_blend)
        print(f"Master saved: {master_blend}")
    else:
        print("Master already in sync")

if __name__ == "__main__":
    main()
