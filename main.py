import bpy, os, subprocess, sys, logging

import logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())

def register():
    venv_site_pkg_file_path = os.path.join(os.path.dirname(__file__), '.venv/Lib/site-packages')

    logger.debug(f'Looking for site packages at: {venv_site_pkg_file_path}')

    if not os.path.exists(venv_site_pkg_file_path):
        exe_file_path = sys.executable
        venv_file_path = os.path.join(os.path.dirname(__file__), '.venv')
        logger.debug(f'Site packages not found, now installing venv at: {venv_file_path}')
        subprocess.run([exe_file_path, '-m' 'venv', venv_file_path])

        _venv_exe_file_path = os.path.join(os.path.dirname(__file__), '.venv/Scripts/python.exe')
        venv_pip_file_path = os.path.join(os.path.dirname(__file__), '.venv/Scripts/pip.exe')

        subprocess.run([venv_pip_file_path, 'install', 'UnityPy'])
    else:
        logger.debug(f'Site packages found at: {venv_site_pkg_file_path}, skipping install')
    sys.path.append(venv_site_pkg_file_path)

def unregister():
    venv_file_path = os.path.join(os.path.dirname(__file__), '.venv')

    logger.debug(f'Removing venv at : {venv_file_path}')

    try:
        subprocess.run(['rmdir', f'"{venv_file_path}"', '/q', '/s'])#
    except(Exception):
        logger.warn('Failed to remove .venv')

def invert_mirror_mapping(vec):
    return [vec[0]*-1, *vec[1:]]

def export(_context, filepath):
    
    import itertools, struct, uuid, UnityPy
    from UnityPy import Environment
    from UnityPy.enums import ClassIDType 
    from UnityPy.files import ObjectReader, SerializedFile
    from UnityPy.files.SerializedFile import SerializedType, FileIdentifier
    from UnityPy.helpers import Tpk

    base_bundle_fp: str = os.path.join(os.path.dirname(__file__), 'base_bundle')
    saved_bundle_fp: str = filepath

    env: Environment = UnityPy.load(base_bundle_fp)
    sf: SerializedFile = list(env.file.files.values())[0]
    
    sf._container = {}
    sf.container_ = {}

    sf.mark_changed()

    asset_bundle_asset = [asset for asset in sf.objects.values() if asset.type.name == 'AssetBundle'][0]
    gameobject_asset = [asset for asset in sf.objects.values() if asset.type.name == 'GameObject'][0]

    path_id_keys = [key for key in sf.objects.keys() if key != 1]

    for key in path_id_keys:
        del sf.objects[key]

    preload = []
    container = []

    tree_map = {}
    
    class EmptyObject(object):
        def __init__(self, **kwargs):
            self.__class__ = ObjectReader
            self.__dict__.update(gameobject_asset.__dict__)
            self.__dict__.update(kwargs)
            sf.objects[kwargs['path_id']] = self
            preload.append({
                'm_FileID': 0,
                'm_PathID': kwargs['path_id']
            })
            sf.mark_changed()

        def save(self):
            return self.data
        
    class EmptyFileIdentifier(object):
        def __init__(self, **kwargs):
            self.__class__ = FileIdentifier
            self.__dict__.update(kwargs)

    class EmptySerializedType(object):
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            self.__class__ = SerializedType 
        
    def generate_16_byte_uid():
        return uuid.uuid1().urn[-16:].encode("ascii")

    def get_type_id(class_id):
        type_id = -1

        for i, sftype in enumerate(sf.types):
            if sftype.class_id == class_id:
                type_id = i

        if type_id == -1:
            type_id = len(sf.types)
            nodes = Tpk.get_typetree_nodes(class_id, (2020, 3, 30, 1))

            buffer = []
            offset = 0
            known_strings = {}

            def store_string(string):
                nonlocal offset

                if string == "SInt32":
                    string = "int"
                elif string == "UInt32":
                    string = "unsigned int"

                string_offset = known_strings.get(string)
                
                if string_offset is None:
                    known_strings[string] = string_offset = offset
                    string_raw = string.encode("utf8") + b"\x00"
                    offset += len(string_raw)
                    buffer.append(string_raw)
                return string_offset

            for node in nodes:
                node.m_TypeStrOffset = store_string(node.m_Type)
                node.m_NameStrOffset = store_string(node.m_Name)

            str_data = b"".join(buffer)

            sf.types.append(
                EmptySerializedType(
                    class_id=class_id,
                    is_stripped_type=False,
                    script_type_index=-1,
                    nodes=nodes,
                    old_type_hash=generate_16_byte_uid(),
                    string_data=str_data,
                    type_dependencies=()
                )
            )
        return type_id

    def generate_path_id():
        path_id = 2
        while True:
            yield path_id
            path_id += 1

    path_id_generator = generate_path_id()

    def get_name_path(bpy_obj):
        if bpy_obj:
            return get_name_path(bpy_obj.parent) + f'/{bpy_obj.name}'
        return ''
    
    def add_gameobject(bpy_obj, _gameobject_path_id, transform_path_id):
        gameobject = EmptyObject(
            type_id=get_type_id(1),
            type=ClassIDType(1),
            serialized_type = sf.types[get_type_id(1)],
            class_id=1,
            data=b'',
            path_id=next(path_id_generator)
        )

        transform = EmptyObject(
            type_id=get_type_id(4),
            type=ClassIDType(4),
            serialized_type = sf.types[get_type_id(4)],
            class_id=4,
            data=b'',
            path_id=next(path_id_generator)
        )

        tree_map[gameobject.path_id] = {
            'm_Component': [
                {
                    'component': {
                        'm_FileID': 0, 
                        'm_PathID': transform.path_id
                    }
                }
            ],
            'm_Layer': 0,
            'm_Name': bpy_obj.name,
            'm_Tag': 0,
            'm_IsActive': True
        }

        tree_map[transform.path_id] = {
            'm_GameObject': {
                'm_FileID': 0,
                'm_PathID': gameobject.path_id
            },
            'm_LocalRotation': dict(zip([*'wxyz'], bpy_obj.rotation_quaternion)),
            'm_LocalPosition': dict(zip([*'xyz'], invert_mirror_mapping(bpy_obj.location))),
            'm_LocalScale': dict(zip([*'xyz'], [1,1,1])),
            'm_Children': [],
            'm_Father': {
                'm_FileID': 0,
                'm_PathID': transform_path_id
            }
        }

        return [gameobject.path_id, transform.path_id]

    def add_mesh(bpy_obj, gameobject_path_id, transform_path_id):

        mesh = EmptyObject(
            type_id=get_type_id(43),
            type=ClassIDType(43),
            serialized_type = sf.types[get_type_id(43)],
            class_id=43,
            data=b'',
            path_id=next(path_id_generator)
        )
        mesh_renderer = EmptyObject(
            type_id=get_type_id(23),
            type=ClassIDType(23),
            serialized_type = sf.types[get_type_id(23)],
            class_id=23,
            data=b'',
            path_id=next(path_id_generator)
        )
        mesh_filter = EmptyObject(
            type_id=get_type_id(33),
            type=ClassIDType(33),
            serialized_type = sf.types[get_type_id(33)],
            class_id=33,
            data=b'',
            path_id=next(path_id_generator)
        )

        byte_mask = (1 << 8) - 1
        to_bytes = lambda x: list(struct.pack('<f', x))

        mesh_data = bpy_obj.data

        positions = []
        normals = []
        uvs = []
        index_buffer = []
        index_counter = 0

        for poly in mesh_data.polygons:
            for j in range(3):
                i = poly.loop_start + 2 - j
                if poly.loop_total > 3:
                    raise Exception('Mesh must be triangulated')
                
                loop = mesh_data.loops[i]
                uv_loop = mesh_data.uv_layers[0].data[i]
                vert = mesh_data.vertices[loop.vertex_index]
                
                positions.append(invert_mirror_mapping(vert.co))
                normals.append(invert_mirror_mapping(poly.normal))
                uvs.append(uv_loop.uv)

                index_buffer += [index_counter & byte_mask, index_counter >> 8]
                index_counter += 1

        data_size: list[int] = []
        for vert in zip(positions, normals, uvs):
            data_size.extend(itertools.chain(*[to_bytes(float) for float in itertools.chain(*vert)]))

        tree_map[mesh.path_id] = {
            'm_Name': bpy_obj.name,
            'm_SubMeshes': [
                {
                    'firstByte': 0,
                    'indexCount': int(len(index_buffer) / 2),
                    'topology': 0,
                    'baseVertex': 0,
                    'firstVertex': 0,
                    'vertexCount': int(len(data_size) / 32),
                    'localAABB': {
                        'm_Center': dict(zip([*'xyz'], [0, 0, 0])),
                        'm_Extent': dict(zip([*'xyz'], [10,10,10]))
                    }
                }
            ],
            'm_Shapes': {
                'vertices': [],
                'shapes': [],
                'channels': [],
                'fullWeights': []
            },
            'm_BindPose': [],
            'm_BoneNameHashes': [],
            'm_RootBoneNameHash': 0,
            'm_BonesAABB': [],
            'm_VariableBoneCountWeights': {
                'm_Data': []
            },
            'm_MeshCompression': 0,
            'm_IsReadable': True,
            'm_KeepVertices': True,
            'm_KeepIndices': True,
            'm_IndexFormat': 0,
            'm_IndexBuffer': index_buffer,
            'm_VertexData': {
                'm_VertexCount': int(len(data_size) / 32),
                'm_Channels': [
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 3},
                    {'stream': 0, 'offset': 12, 'format': 0, 'dimension': 3},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0},
                    {'stream': 0, 'offset': 24, 'format': 0, 'dimension': 2},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0}
                ],
                'm_DataSize': bytes(data_size)
            },
            'm_CompressedMesh': {
                'm_Vertices': {
                    'm_NumItems': 0,
                    'm_Range': 0,
                    'm_Start': 0,
                    'm_Data': [],
                    'm_BitSize': 0
                },
                'm_UV': {
                    'm_NumItems': 0,
                    'm_Range': 0,
                    'm_Start': 0,
                    'm_Data': [],
                    'm_BitSize': 0
                },
                'm_Normals': {
                    'm_NumItems': 0,
                    'm_Range': 0,
                    'm_Start': 0,
                    'm_Data': [],
                    'm_BitSize': 0
                },
                'm_Tangents': {
                    'm_NumItems': 0,
                    'm_Range': 0,
                    'm_Start': 0,
                    'm_Data': [],
                    'm_BitSize': 0
                },
                'm_Weights': {
                    'm_NumItems': 0,
                    'm_Data': [],
                    'm_BitSize': 0
                },
                'm_NormalSigns': {
                    'm_NumItems': 0,
                    'm_Data': [],
                    'm_BitSize': 0
                },
                'm_TangentSigns': {
                    'm_NumItems': 0,
                    'm_Data': [],
                    'm_BitSize': 0
                },
                'm_FloatColors': {
                    'm_NumItems': 0,
                    'm_Range': 0,
                    'm_Start': 0,
                    'm_Data': [],
                    'm_BitSize': 0
                },
                'm_BoneIndices': {
                    'm_NumItems': 0,
                    'm_Data': [],
                    'm_BitSize': 0
                },
                'm_Triangles': {
                    'm_NumItems': 0,
                    'm_Data': [],
                    'm_BitSize': 0
                },
                'm_UVInfo': 0
            },
            'm_LocalAABB': {
                'm_Center': dict(zip([*'xyz'], [0, 0, 0])),
                'm_Extent': dict(zip([*'xyz'], [10, 10, 10]))
            },
            'm_MeshUsageFlags': 0,
            'm_BakedConvexCollisionMesh': [],
            'm_BakedTriangleCollisionMesh': [],
            'm_MeshMetrics[0]': 1,
            'm_MeshMetrics[1]': 1,
            'm_StreamData': {
                'offset': 0,
                'size': 0,
                'path': ''
            }
        }

        tree_map[mesh_filter.path_id] = {
            'm_GameObject': {
                'm_FileID': 0,
                'm_PathID': gameobject_path_id
            },
            'm_Mesh': {
                'm_FileID': 0,
                'm_PathID': mesh.path_id
            }
        }

        tree_map[mesh_renderer.path_id] = {
            'm_GameObject': {
                'm_FileID': 0,
                'm_PathID': gameobject_path_id
            },
            'm_Enabled': True,
            'm_CastShadows': 1,
            'm_ReceiveShadows': 1,
            'm_DynamicOccludee': 1,
            'm_MotionVectors': 1,
            'm_LightProbeUsage': 1,
            'm_ReflectionProbeUsage': 1,
            'm_RayTracingMode': 2,
            'm_RayTraceProcedural': 0,
            'm_RenderingLayerMask': 1,
            'm_RendererPriority': 0,
            'm_LightmapIndex': 65535,
            'm_LightmapIndexDynamic': 65535,
            'm_LightmapTilingOffset': dict(zip([*'xyzw'], [0,0,0,0])),
            'm_LightmapTilingOffsetDynamic': dict(zip([*'xyzw'], [0,0,0,0])),
            'm_Materials': [
                {
                    'm_FileID': 1,
                    'm_PathID': (40 if bpy_obj.name != 'Shadow' else 36)
                }
            ],
            'm_StaticBatchInfo': {
                'firstSubMesh': 0,
                'subMeshCount': 0
            },
            'm_StaticBatchRoot': {
                'm_FileID': 0,
                'm_PathID': 0
            },
            'm_ProbeAnchor': {
                'm_FileID': 0,
                'm_PathID': 0
            },
            'm_LightProbeVolumeOverride': {
                'm_FileID': 0,
                'm_PathID': 0
            },
            'm_SortingLayerID': 0,
            'm_SortingLayer': 0,
            'm_SortingOrder': 0,
            'm_AdditionalVertexStreams': {
                'm_FileID': 0,
                'm_PathID': 0
            },
            'm_EnlightenVertexStream': {
                'm_FileID': 0,
                'm_PathID': 0
            }
        }

        tree_map[gameobject_path_id]['m_Component'].append({
            'component': {
                'm_FileID': 0,
                'm_PathID': mesh_filter.path_id
            }
        })
        tree_map[gameobject_path_id]['m_Component'].append({
            'component': {
                'm_FileID': 0,
                'm_PathID': mesh_renderer.path_id
            }
        })

        return [gameobject_path_id, transform_path_id]


    def descend_tree(bpy_obj, gameobject_path_id=0, transform_path_id=0):

        preloadIndex = len(preload)

        [new_gameobject_path_id, new_transform_path_id
         ] = add_gameobject(bpy_obj, gameobject_path_id, transform_path_id)

        if bpy_obj.type == 'MESH':

            add_mesh(bpy_obj, new_gameobject_path_id, new_transform_path_id)

        for child in bpy_obj.children:
            descend_tree(child, new_gameobject_path_id, new_transform_path_id)

        if transform_path_id != 0:
            parent_transform = sf.objects[transform_path_id]
            tree_map[parent_transform.path_id]['m_Children'].append({
                'm_FileID': 0,
                'm_PathID': new_transform_path_id
            })
        else:
            container.append((
                f'{bpy_obj.name}',
                {
                    'preloadIndex': 0,
                    'preloadSize': len(preload),
                    'asset': {
                        'm_FileID': 0,
                        'm_PathID': new_gameobject_path_id
                    }
                }
            ))
            container.append((
                f'{bpy_obj.name}/Transform',
                {
                    'preloadIndex': 0,
                    'preloadSize': len(preload),
                    'asset': {
                        'm_FileID': 0,
                        'm_PathID': new_transform_path_id
                    }
                }
            ))

    root_bpy_obj = [obj for obj in bpy.data.objects if obj.parent == None][0]

    descend_tree(root_bpy_obj)

    for [path_id, tree] in tree_map.items():
        sf.objects[path_id].save_typetree(tree)

    tree = asset_bundle_asset.read_typetree()
    tree['m_PreloadTable'] = preload
    tree['m_Container'] = container
    asset_bundle_asset.save_typetree(tree)

    external_files = [
        'resources.assets',
        'sharedassets0.assets',
        'sharedassets1.assets',
        'sharedassets2.assets',
        'sharedassets3.assets',
        'sharedassets4.assets',
        'sharedassets5.assets',
        'sharedassets6.assets',
        'sharedassets7.assets',
        'sharedassets8.assets',
        'globalgamemanagers.assets',
        'unity_builtin_extra',
        'unity default resources'
    ]

    sf.externals = []
    
    for external_file in external_files:
        sf.externals.append(EmptyFileIdentifier(
            guid = bytes(bytearray(16)),
            type = 0,
            path = external_file,
            temp_empty = ''
        ))

    sf.mark_changed()

    with open(saved_bundle_fp, 'wb') as f:
        f.write(env.file.save())

    return {'FINISHED'}
    
    import itertools, struct, uuid, UnityPy
    from UnityPy import Environment
    from UnityPy.enums import ClassIDType 
    from UnityPy.files import ObjectReader, SerializedFile
    from UnityPy.files.SerializedFile import SerializedType, FileIdentifier
    from UnityPy.helpers import Tpk

    base_bundle_fp: str = os.path.join(os.path.dirname(__file__), 'base_bundle')
    saved_bundle_fp: str = filepath

    env: Environment = UnityPy.load(base_bundle_fp)
    sf: SerializedFile = list(env.file.files.values())[0]
    
    sf._container = {}
    sf.container_ = {}

    sf.mark_changed()

    asset_bundle_asset = [asset for asset in sf.objects.values() if asset.type.name == 'AssetBundle'][0]
    gameobject_asset = [asset for asset in sf.objects.values() if asset.type.name == 'GameObject'][0]

    path_id_keys = [key for key in sf.objects.keys() if key != 1]

    for key in path_id_keys:
        del sf.objects[key]

    preload = []
    container = []

    tree_map = {}
    
    class EmptyObject(object):
        def __init__(self, **kwargs):
            self.__class__ = ObjectReader
            self.__dict__.update(gameobject_asset.__dict__)
            self.__dict__.update(kwargs)
            sf.objects[kwargs['path_id']] = self
            preload.append({
                'm_FileID': 0,
                'm_PathID': kwargs['path_id']
            })
            sf.mark_changed()

        def save(self):
            return self.data
        
    class EmptyFileIdentifier(object):
        def __init__(self, **kwargs):
            self.__class__ = FileIdentifier
            self.__dict__.update(kwargs)

    class EmptySerializedType(object):
        def __init__(self, **kwargs):
            self.__dict__.update(kwargs)
            self.__class__ = SerializedType 
        
    def generate_16_byte_uid():
        return uuid.uuid1().urn[-16:].encode("ascii")

    def get_type_id(class_id):
        type_id = -1

        for i, sftype in enumerate(sf.types):
            if sftype.class_id == class_id:
                type_id = i

        if type_id == -1:
            type_id = len(sf.types)
            nodes = Tpk.get_typetree_nodes(class_id, (2020, 3, 30, 1))

            buffer = []
            offset = 0
            known_strings = {}

            def store_string(string):
                nonlocal offset

                if string == "SInt32":
                    string = "int"
                elif string == "UInt32":
                    string = "unsigned int"

                string_offset = known_strings.get(string)
                
                if string_offset is None:
                    known_strings[string] = string_offset = offset
                    string_raw = string.encode("utf8") + b"\x00"
                    offset += len(string_raw)
                    buffer.append(string_raw)
                return string_offset

            for node in nodes:
                node.m_TypeStrOffset = store_string(node.m_Type)
                node.m_NameStrOffset = store_string(node.m_Name)

            str_data = b"".join(buffer)

            sf.types.append(
                EmptySerializedType(
                    class_id=class_id,
                    is_stripped_type=False,
                    script_type_index=-1,
                    nodes=nodes,
                    old_type_hash=generate_16_byte_uid(),
                    string_data=str_data,
                    type_dependencies=()
                )
            )
        return type_id

    def generate_path_id():
        path_id = 2
        while True:
            yield path_id
            path_id += 1

    path_id_generator = generate_path_id()

    def get_name_path(bpy_obj):
        if bpy_obj:
            return get_name_path(bpy_obj.parent) + f'/{bpy_obj.name}'
        return ''
    
    def add_gameobject(bpy_obj, _gameobject_path_id, transform_path_id):
        gameobject = EmptyObject(
            type_id=get_type_id(1),
            type=ClassIDType(1),
            serialized_type = sf.types[get_type_id(1)],
            class_id=1,
            data=b'',
            path_id=next(path_id_generator)
        )

        transform = EmptyObject(
            type_id=get_type_id(4),
            type=ClassIDType(4),
            serialized_type = sf.types[get_type_id(4)],
            class_id=4,
            data=b'',
            path_id=next(path_id_generator)
        )

        tree_map[gameobject.path_id] = {
            'm_Component': [
                {
                    'component': {
                        'm_FileID': 0, 
                        'm_PathID': transform.path_id
                    }
                }
            ],
            'm_Layer': 0,
            'm_Name': bpy_obj.name,
            'm_Tag': 0,
            'm_IsActive': True
        }

        tree_map[transform.path_id] = {
            'm_GameObject': {
                'm_FileID': 0,
                'm_PathID': gameobject.path_id
            },
            'm_LocalRotation': dict(zip([*'wxyz'], bpy_obj.rotation_quaternion)),
            'm_LocalPosition': dict(zip([*'xyz'], bpy_obj.location)),
            'm_LocalScale': dict(zip([*'xyz'], [1,1,1])),
            'm_Children': [],
            'm_Father': {
                'm_FileID': 0,
                'm_PathID': transform_path_id
            }
        }

        return [gameobject.path_id, transform.path_id]

    def add_mesh(bpy_obj, gameobject_path_id, transform_path_id):

        mesh = EmptyObject(
            type_id=get_type_id(43),
            type=ClassIDType(43),
            serialized_type = sf.types[get_type_id(43)],
            class_id=43,
            data=b'',
            path_id=next(path_id_generator)
        )
        mesh_renderer = EmptyObject(
            type_id=get_type_id(23),
            type=ClassIDType(23),
            serialized_type = sf.types[get_type_id(23)],
            class_id=23,
            data=b'',
            path_id=next(path_id_generator)
        )
        mesh_filter = EmptyObject(
            type_id=get_type_id(33),
            type=ClassIDType(33),
            serialized_type = sf.types[get_type_id(33)],
            class_id=33,
            data=b'',
            path_id=next(path_id_generator)
        )

        byte_mask = (1 << 8) - 1
        to_bytes = lambda x: list(struct.pack('<f', x))

        mesh_data = bpy_obj.data

        positions = []
        normals = []
        uvs = []
        index_buffer = []
        index_counter = 0

        for poly in mesh_data.polygons:
            for i in range(poly.loop_start, poly.loop_start + 3):
                if poly.loop_total > 3:
                    raise Exception('Mesh must be triangulated')
                
                loop = mesh_data.loops[i]
                uv_loop = mesh_data.uv_layers[0].data[i]
                vert = mesh_data.vertices[loop.vertex_index]
                
                positions.append(vert.co)
                normals.append(poly.normal)
                uvs.append(uv_loop.uv)

                index_buffer += [index_counter & byte_mask, index_counter >> 8]
                index_counter += 1

        data_size: list[int] = []
        for vert in zip(positions, normals, uvs):
            data_size.extend(itertools.chain(*[to_bytes(float) for float in itertools.chain(*vert)]))

        tree_map[mesh.path_id] = {
            'm_Name': bpy_obj.name,
            'm_SubMeshes': [
                {
                    'firstByte': 0,
                    'indexCount': int(len(index_buffer) / 2),
                    'topology': 0,
                    'baseVertex': 0,
                    'firstVertex': 0,
                    'vertexCount': int(len(data_size) / 32),
                    'localAABB': {
                        'm_Center': dict(zip([*'xyz'], [0, 0, 0])),
                        'm_Extent': dict(zip([*'xyz'], [10,10,10]))
                    }
                }
            ],
            'm_Shapes': {
                'vertices': [],
                'shapes': [],
                'channels': [],
                'fullWeights': []
            },
            'm_BindPose': [],
            'm_BoneNameHashes': [],
            'm_RootBoneNameHash': 0,
            'm_BonesAABB': [],
            'm_VariableBoneCountWeights': {
                'm_Data': []
            },
            'm_MeshCompression': 0,
            'm_IsReadable': True,
            'm_KeepVertices': True,
            'm_KeepIndices': True,
            'm_IndexFormat': 0,
            'm_IndexBuffer': index_buffer,
            'm_VertexData': {
                'm_VertexCount': int(len(data_size) / 32),
                'm_Channels': [
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 3},
                    {'stream': 0, 'offset': 12, 'format': 0, 'dimension': 3},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0},
                    {'stream': 0, 'offset': 24, 'format': 0, 'dimension': 2},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0},
                    {'stream': 0, 'offset': 0, 'format': 0, 'dimension': 0}
                ],
                'm_DataSize': bytes(data_size)
            },
            'm_CompressedMesh': {
                'm_Vertices': {
                    'm_NumItems': 0,
                    'm_Range': 0,
                    'm_Start': 0,
                    'm_Data': [],
                    'm_BitSize': 0
                },
                'm_UV': {
                    'm_NumItems': 0,
                    'm_Range': 0,
                    'm_Start': 0,
                    'm_Data': [],
                    'm_BitSize': 0
                },
                'm_Normals': {
                    'm_NumItems': 0,
                    'm_Range': 0,
                    'm_Start': 0,
                    'm_Data': [],
                    'm_BitSize': 0
                },
                'm_Tangents': {
                    'm_NumItems': 0,
                    'm_Range': 0,
                    'm_Start': 0,
                    'm_Data': [],
                    'm_BitSize': 0
                },
                'm_Weights': {
                    'm_NumItems': 0,
                    'm_Data': [],
                    'm_BitSize': 0
                },
                'm_NormalSigns': {
                    'm_NumItems': 0,
                    'm_Data': [],
                    'm_BitSize': 0
                },
                'm_TangentSigns': {
                    'm_NumItems': 0,
                    'm_Data': [],
                    'm_BitSize': 0
                },
                'm_FloatColors': {
                    'm_NumItems': 0,
                    'm_Range': 0,
                    'm_Start': 0,
                    'm_Data': [],
                    'm_BitSize': 0
                },
                'm_BoneIndices': {
                    'm_NumItems': 0,
                    'm_Data': [],
                    'm_BitSize': 0
                },
                'm_Triangles': {
                    'm_NumItems': 0,
                    'm_Data': [],
                    'm_BitSize': 0
                },
                'm_UVInfo': 0
            },
            'm_LocalAABB': {
                'm_Center': dict(zip([*'xyz'], [0, 0, 0])),
                'm_Extent': dict(zip([*'xyz'], [10, 10, 10]))
            },
            'm_MeshUsageFlags': 0,
            'm_BakedConvexCollisionMesh': [],
            'm_BakedTriangleCollisionMesh': [],
            'm_MeshMetrics[0]': 1,
            'm_MeshMetrics[1]': 1,
            'm_StreamData': {
                'offset': 0,
                'size': 0,
                'path': ''
            }
        }

        tree_map[mesh_filter.path_id] = {
            'm_GameObject': {
                'm_FileID': 0,
                'm_PathID': gameobject_path_id
            },
            'm_Mesh': {
                'm_FileID': 0,
                'm_PathID': mesh.path_id
            }
        }

        tree_map[mesh_renderer.path_id] = {
            'm_GameObject': {
                'm_FileID': 0,
                'm_PathID': gameobject_path_id
            },
            'm_Enabled': True,
            'm_CastShadows': 1,
            'm_ReceiveShadows': 1,
            'm_DynamicOccludee': 1,
            'm_MotionVectors': 1,
            'm_LightProbeUsage': 1,
            'm_ReflectionProbeUsage': 1,
            'm_RayTracingMode': 2,
            'm_RayTraceProcedural': 0,
            'm_RenderingLayerMask': 1,
            'm_RendererPriority': 0,
            'm_LightmapIndex': 65535,
            'm_LightmapIndexDynamic': 65535,
            'm_LightmapTilingOffset': dict(zip([*'xyzw'], [0,0,0,0])),
            'm_LightmapTilingOffsetDynamic': dict(zip([*'xyzw'], [0,0,0,0])),
            'm_Materials': [
                {
                    'm_FileID': 1,
                    'm_PathID': (40 if bpy_obj.name != 'Shadow' else 36)
                }
            ],
            'm_StaticBatchInfo': {
                'firstSubMesh': 0,
                'subMeshCount': 0
            },
            'm_StaticBatchRoot': {
                'm_FileID': 0,
                'm_PathID': 0
            },
            'm_ProbeAnchor': {
                'm_FileID': 0,
                'm_PathID': 0
            },
            'm_LightProbeVolumeOverride': {
                'm_FileID': 0,
                'm_PathID': 0
            },
            'm_SortingLayerID': 0,
            'm_SortingLayer': 0,
            'm_SortingOrder': 0,
            'm_AdditionalVertexStreams': {
                'm_FileID': 0,
                'm_PathID': 0
            },
            'm_EnlightenVertexStream': {
                'm_FileID': 0,
                'm_PathID': 0
            }
        }

        tree_map[gameobject_path_id]['m_Component'].append({
            'component': {
                'm_FileID': 0,
                'm_PathID': mesh_filter.path_id
            }
        })
        tree_map[gameobject_path_id]['m_Component'].append({
            'component': {
                'm_FileID': 0,
                'm_PathID': mesh_renderer.path_id
            }
        })

        return [gameobject_path_id, transform_path_id]


    def descend_tree(bpy_obj, gameobject_path_id=0, transform_path_id=0):

        preloadIndex = len(preload)

        [new_gameobject_path_id, new_transform_path_id
         ] = add_gameobject(bpy_obj, gameobject_path_id, transform_path_id)

        if bpy_obj.type == 'MESH':

            add_mesh(bpy_obj, new_gameobject_path_id, new_transform_path_id)

        for child in bpy_obj.children:
            descend_tree(child, new_gameobject_path_id, new_transform_path_id)

        if transform_path_id != 0:
            parent_transform = sf.objects[transform_path_id]
            tree_map[parent_transform.path_id]['m_Children'].append({
                'm_FileID': 0,
                'm_PathID': new_transform_path_id
            })
        else:
            container.append((
                f'{bpy_obj.name}',
                {
                    'preloadIndex': 0,
                    'preloadSize': len(preload),
                    'asset': {
                        'm_FileID': 0,
                        'm_PathID': new_gameobject_path_id
                    }
                }
            ))
            container.append((
                f'{bpy_obj.name}/Transform',
                {
                    'preloadIndex': 0,
                    'preloadSize': len(preload),
                    'asset': {
                        'm_FileID': 0,
                        'm_PathID': new_transform_path_id
                    }
                }
            ))

    root_bpy_obj = [obj for obj in bpy.data.objects if obj.parent == None][0]

    descend_tree(root_bpy_obj)

    for [path_id, tree] in tree_map.items():
        sf.objects[path_id].save_typetree(tree)

    tree = asset_bundle_asset.read_typetree()
    tree['m_PreloadTable'] = preload
    tree['m_Container'] = container
    asset_bundle_asset.save_typetree(tree)

    external_files = [
        'resources.assets',
        'sharedassets0.assets',
        'sharedassets1.assets',
        'sharedassets2.assets',
        'sharedassets3.assets',
        'sharedassets4.assets',
        'sharedassets5.assets',
        'sharedassets6.assets',
        'sharedassets7.assets',
        'sharedassets8.assets',
        'globalgamemanagers.assets',
        'unity_builtin_extra',
        'unity default resources'
    ]

    sf.externals = []
    
    for external_file in external_files:
        sf.externals.append(EmptyFileIdentifier(
            guid = bytes(bytearray(16)),
            type = 0,
            path = external_file,
            temp_empty = ''
        ))

    sf.mark_changed()

    with open(saved_bundle_fp, 'wb') as f:
        f.write(env.file.save())

    return {'FINISHED'}

if __name__ == '__main__':
    register()
    export(bpy.context, "C:\Program Files (x86)\Steam\steamapps\common\TinyCombatArenaDev\AssetBundles\AV8B2TEST")