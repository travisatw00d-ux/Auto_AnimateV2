import bpy
bpy.ops.import_scene.gltf(filepath=r'C:\Dev\Character\Travis\TravisFinished.glb')
mesh = next((o for o in bpy.data.objects if o.type=='MESH'), None)
print('mesh:', mesh.name if mesh else None)
if mesh and mesh.data.materials:
    mat = mesh.data.materials[0]
    print('mat:', mat.name)
    if mat.node_tree:
        for n in mat.node_tree.nodes:
            print('node:', n.type, n.name)
            if n.type == 'TEX_IMAGE' and n.image:
                print('  image:', n.image.name, 'has_data:', n.image.has_data)
                n.image.update()
                print('  after update has_data:', n.image.has_data)
