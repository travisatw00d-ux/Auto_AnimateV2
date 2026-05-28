"""
Transfer textures from a textured FBX model onto a character blend file.
Exports textures to disk, then re-imports them in the character blend.
Usage: blender --background --python transfer_model_textures.py -- model.fbx char.blend output.blend
"""
import bpy, sys, os, shutil

def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if len(args) < 3:
        print("Usage: transfer_model_textures.py -- model.fbx char.blend output.blend")
        sys.exit(1)

    model_fbx = args[0]
    char_blend = args[1]
    output_blend = args[2]

    out_dir = os.path.dirname(os.path.abspath(output_blend))
    tex_dir = os.path.join(out_dir, "textures")
    os.makedirs(tex_dir, exist_ok=True)

    # === STEP 1: Extract textures from model FBX ===
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=model_fbx)

    # Unpack textures to disk and capture their socket roles from the node tree
    tex_entries = []
    model_mesh = next((o for o in bpy.data.objects if o.type == 'MESH' and o.vertex_groups), None)
    if model_mesh is None:
        model_mesh = next((o for o in bpy.data.objects if o.type == 'MESH'), None)
    model_mat = model_mesh.material_slots[0].material if model_mesh and model_mesh.material_slots else None

    # Build a map: image name -> Principled BSDF socket name
    img_to_socket = {}
    if model_mat and model_mat.node_tree:
        for n in model_mat.node_tree.nodes:
            if n.type == 'TEX_IMAGE' and n.image:
                socket = 'Base Color'
                for o in n.outputs:
                    for l in o.links:
                        nxt = l.to_node
                        if nxt.type == 'BSDF_PRINCIPLED':
                            socket = l.to_socket.name
                        elif nxt.type == 'NORMAL_MAP':
                            for o2 in nxt.outputs:
                                for l2 in o2.links:
                                    if l2.to_node.type == 'BSDF_PRINCIPLED':
                                        socket = l2.to_socket.name
                img_to_socket[n.image.name] = socket

    IMAGE_EXTS = {'.png', '.jpg', '.jpeg', '.tga', '.bmp', '.exr', '.tif', '.tiff'}

    for img in bpy.data.images:
        if img.size[0] == 0:
            continue
        name = img.name
        ext = os.path.splitext(name)[1].lower()
        if ext not in IMAGE_EXTS:
            name += ".png"
        path = os.path.join(tex_dir, name)
        if img.packed_file:
            img.filepath_raw = path
            img.save()
            img.unpack(method='REMOVE')
            socket = img_to_socket.get(img.name, 'Base Color')
            tex_entries.append((name, socket))
            print(f"  Unpacked: {name} ({img.size[0]}x{img.size[1]}) -> {socket}")
        elif img.filepath and os.path.exists(img.filepath):
            if not os.path.exists(path):
                shutil.copy2(img.filepath, path)
            socket = img_to_socket.get(img.name, 'Base Color')
            tex_entries.append((name, socket))
            print(f"  Copied: {name} -> {socket}")

    if not tex_entries:
        print("WARNING: No textures found in model FBX -- keeping original material")
        bpy.ops.wm.open_mainfile(filepath=char_blend)
        if os.path.exists(output_blend): os.remove(output_blend)
        bpy.ops.wm.save_as_mainfile(filepath=output_blend)
        print(f"Saved: {output_blend} (material kept as-is)")
        return

    # === STEP 2: Apply textures to character blend ===
    bpy.ops.wm.open_mainfile(filepath=char_blend)
    char_mesh = next((o for o in bpy.data.objects if o.type == 'MESH' and o.vertex_groups), None)
    if char_mesh is None:
        char_mesh = next((o for o in bpy.data.objects if o.type == 'MESH'), None)
    if char_mesh is None:
        print("ERROR: No mesh in character blend")
        sys.exit(1)

    # Remove existing materials from character mesh
    char_mesh.data.materials.clear()

    # Find or create material
    mat = None
    for m in bpy.data.materials:
        if 'tripo_mat' in m.name:
            mat = m
            break
    if mat is None:
        mat = bpy.data.materials.new(name=f"tripo_mat")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    # Create Principled BSDF
    bsdf = nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.location = (0, 0)

    output = nodes.new('ShaderNodeOutputMaterial')
    output.location = (300, 0)
    links.new(bsdf.outputs['BSDF'], output.inputs['Surface'])

    # Load textures using captured socket info
    SOCKET_NAMES = {
        'Base Color': bsdf.inputs['Base Color'],
        'Normal': bsdf.inputs['Normal'],
        'Roughness': bsdf.inputs['Roughness'],
        'Metallic': bsdf.inputs['Metallic'],
    }
    Y_POSITIONS = {'Base Color': 200, 'Normal': 0, 'Roughness': -200, 'Metallic': -400}

    for tf, socket_name in tex_entries:
        path = os.path.join(tex_dir, tf)
        if not os.path.exists(path):
            continue

        img = bpy.data.images.load(path)
        img.pack()
        tex_node = nodes.new('ShaderNodeTexImage')
        tex_node.image = img
        tex_node.location = (-300, Y_POSITIONS.get(socket_name, 200))

        target = SOCKET_NAMES.get(socket_name)
        if target is not None:
            links.new(tex_node.outputs['Color'], target)
        else:
            links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])

    # Assign material to mesh
    char_mesh.data.materials.append(mat)
    print(f"Material '{mat.name}' assigned with {len(tex_entries)} textures")

    if os.path.exists(output_blend): os.remove(output_blend)
    bpy.ops.wm.save_as_mainfile(filepath=output_blend)
    print(f"Saved: {output_blend}")

if __name__ == "__main__":
    main()
