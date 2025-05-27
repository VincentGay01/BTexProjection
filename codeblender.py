import bpy
import json
import mathutils
import math
import os
import re
import numpy 

# Nettoyer la scène au début
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)

# Chemins
mesh_path = "D:/project/AppTexToMesh/gltf/Chemi-AU-O005.gltf"
json_path = "D:/project/verifCam/intrinsic/camera1.json"
image_path = "D:/project/AppTexToMesh/photo/shoe1.png"
output_image_path = "D:/project/AppTexToMesh/res/bake_Texture.png"

def extract_position_from_name(name):
    """Extraire la position à partir du nom"""
    position = {"x": 0.0, "y": 0.0, "z": 0.0}
    
    pattern = r"Pos: \(([0-9.]+), ([0-9.]+), ([0-9.]+)\)"
    matches = re.search(pattern, name)
    
    if matches and len(matches.groups()) == 3:
        position["x"] = float(matches.group(1))
        position["y"] = float(matches.group(2))
        position["z"] = float(matches.group(3))
    
    return position

def convert_pose_to_blender_matrix(pose):
    matrix = mathutils.Matrix([
        [pose[0][0], pose[0][1], pose[0][2], pose[0][3]],
        [pose[1][0], pose[1][1], pose[1][2], pose[1][3]],
        [pose[2][0], pose[2][1], pose[2][2], pose[2][3]],
        [pose[3][0], pose[3][1], pose[3][2], pose[3][3]]
    ])
 
    conversion = mathutils.Matrix([
        [1.0, 0.0, 0.0, 0.0],
        [0.0, -1.0, 0.0, 0.0],
        [0.0, 0.0, -1.0, 0.0],
        [0.0, 0.0, 0.0, -1.0]
    ])
    
    matrix = matrix @ conversion
    rotation_x = mathutils.Matrix.Rotation(math.radians(180.0), 4, 'X')
    matrix = matrix @ rotation_x
    
    matrix_inverted = matrix.inverted()
    print(f"Matrice caméra: {matrix_inverted}")
    return matrix_inverted

def create_camera_parameters(cam_params, near_plane=0.001, far_plane=1000.0):
    """Configurer les paramètres de caméra Blender"""
    image_width = int(2 * cam_params["principal_point_x"])
    image_height = int(2 * cam_params["principal_point_y"])
    aspect_ratio = image_width / image_height
    
    return {
        "focal_length_x": cam_params["focal_length_x"],
        "focal_length_y": cam_params["focal_length_y"], 
        "principal_point_x": cam_params["principal_point_x"],
        "principal_point_y": cam_params["principal_point_y"],
        "image_width": image_width,
        "image_height": image_height,
        "aspect_ratio": aspect_ratio,
        "near_plane": near_plane,
        "far_plane": far_plane
    }

# Charger les données JSON
with open(json_path, 'r') as f:
    data = json.load(f)

camera_data = data[0]
camera_name = camera_data["name"]
position = extract_position_from_name(camera_name)
print(f"Position extraite du nom: ({position['x']}, {position['y']}, {position['z']})")

# Créer la caméra
cam_data = bpy.data.cameras.new(name=camera_name)
cam_object = bpy.data.objects.new(name=camera_name, object_data=cam_data)

# Ajouter à la scène
scene = bpy.context.scene
scene.collection.objects.link(cam_object)

# Configurer les paramètres de caméra
cam_params = camera_data["camera_params"]
camera_parameters = create_camera_parameters(cam_params)

scene.render.resolution_x = camera_parameters["image_width"]
scene.render.resolution_y = camera_parameters["image_height"]
scene.render.pixel_aspect_x = 1.0
scene.render.pixel_aspect_y = 1.0

sensor_width = cam_data.sensor_width
focal_length_mm = (camera_parameters["focal_length_x"] * sensor_width) / camera_parameters["image_width"]
cam_data.lens = focal_length_mm

cam_data.shift_x = (camera_parameters["principal_point_x"] / camera_parameters["image_width"]) - 0.5
cam_data.shift_y = ((camera_parameters["principal_point_y"] / camera_parameters["image_height"]) - 0.5)

cam_data.clip_start = camera_parameters["near_plane"]
cam_data.clip_end = camera_parameters["far_plane"]

# Appliquer la matrice de transformation
blender_matrix = convert_pose_to_blender_matrix(camera_data["pose"])
rotation_matrix_local = mathutils.Matrix.Rotation(math.radians(180), 4,'X')
cam_object.matrix_world = blender_matrix @ rotation_matrix_local

matrix_position = blender_matrix.translation
print(f"Position de la caméra: ({matrix_position.x}, {matrix_position.y}, {matrix_position.z})")

scene.camera = cam_object

# Importer le mesh
bpy.ops.import_scene.gltf(filepath=mesh_path)
obj = bpy.context.selected_objects[0]
bpy.context.view_layer.objects.active = obj

# Quaternion de rotation de -90° autour de X
q = mathutils.Quaternion((1.0, 0.0, 0.0), math.radians(-90))

# Appliquer au lieu de rotation_euler
obj.rotation_mode = 'QUATERNION'
obj.rotation_quaternion = q

print(f"Mesh importé: {obj.name}")
print(f"Nombre de vertices: {len(obj.data.vertices)}")

# Vérifier les UV
if not obj.data.uv_layers:
    print("Création des coordonnées UV...")
    bpy.ops.object.editmode_toggle()
    bpy.ops.uv.smart_project()
    bpy.ops.object.editmode_toggle()
else:
    print("Coordonnées UV existantes trouvées")

# CORRECTION PRINCIPALE: Créer le matériau avec projection depuis la caméra spécifique
mat = bpy.data.materials.new("ProjectedMat")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
nodes.clear()

# Créer les nodes pour une projection de caméra correcte
coord = nodes.new('ShaderNodeTexCoord')
cam_data_node = nodes.new('ShaderNodeCameraData')  




mapping = nodes.new('ShaderNodeMapping')
img_node = nodes.new('ShaderNodeTexImage')
emission = nodes.new('ShaderNodeEmission')
out = nodes.new('ShaderNodeOutputMaterial')

# Positionner les nodes
cam_data_node.location = (-400, 0)
mapping.location = (400, 0)
img_node.location = (600, 0)
emission.location = (800, 0)
out.location = (1000, 0)

# Charger l'image
try:
    img_node.image = bpy.data.images.load(image_path)
    print(f"Image chargée: {image_path}")
    print(f"Dimensions image: {img_node.image.size[0]}x{img_node.image.size[1]}")
except:
    print(f"ERREUR: Impossible de charger l'image {image_path}")

# Configuration du mapping pour ajustements finaux
mapping.inputs['Scale'].default_value = (1.4, 2.1, 1.0)
mapping.inputs['Location'].default_value = (0.5, 0.5, 0.0)

# Configuration de l'image node
img_node.extension = 'CLIP'
img_node.projection = 'FLAT'

# CONNEXIONS CORRIGÉES pour projection depuis la caméra
# 1. Position mondiale vers coordonnées caméra
links.new(cam_data_node.outputs['View Vector'], mapping.inputs['Vector'])
links.new(mapping.outputs['Vector'], img_node.inputs['Vector'])
links.new(img_node.outputs['Color'], emission.inputs['Color'])
links.new(emission.outputs['Emission'], out.inputs['Surface'])

# Assigner le matériau
if obj.data.materials:
    obj.data.materials[0] = mat
else:
    obj.data.materials.append(mat)

# IMPORTANT: Définir la caméra de référence pour les coordonnées
# Ceci force Blender à utiliser votre caméra pour les transformations
bpy.context.scene.camera = cam_object

# Créer l'image pour le baking
bake_width = 1024
bake_height = 1024
baked_img = bpy.data.images.new("BakedProjection", width=bake_width, height=bake_height)
baked_img.generated_color = (1.0, 0.0, 1.0, 1.0)

# Créer un deuxième UV map pour le baking si nécessaire
if len(obj.data.uv_layers) < 2:
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.uv_texture_add()
    bpy.ops.uv.smart_project()
    bpy.ops.object.editmode_toggle()

# Créer un node pour l'image de bake
baked_node = nodes.new('ShaderNodeTexImage')
baked_node.image = baked_img
baked_node.location = (1200, -200)
nodes.active = baked_node

# Configuration du moteur de rendu
bpy.context.scene.render.engine = 'CYCLES'
bpy.context.scene.cycles.device = 'CPU'
bpy.context.scene.cycles.samples = 1

# S'assurer que l'objet est sélectionné et actif
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)
bpy.context.view_layer.objects.active = obj

# Configuration spécifique pour le baking
bpy.context.scene.cycles.bake_type = 'EMIT'
bpy.context.scene.render.bake.use_pass_direct = False
bpy.context.scene.render.bake.use_pass_indirect = False
bpy.context.scene.render.bake.use_pass_color = True
bpy.context.scene.render.bake.margin = 0

print("=== DIAGNOSTIC ===")
print(f"Caméra active: {scene.camera.name if scene.camera else 'Aucune'}")
print(f"Objet actif: {bpy.context.view_layer.objects.active.name if bpy.context.view_layer.objects.active else 'Aucun'}")
print(f"Node actif: {nodes.active.name if nodes.active else 'Aucun'}")
print(f"Nombre de matériaux sur l'objet: {len(obj.data.materials)}")
print(f"Image dans le node actif: {nodes.active.image.name if nodes.active and nodes.active.image else 'Aucune'}")

# TEST: Rendu simple pour vérifier la projection
print("Test de rendu pour vérifier la projection...")
scene.render.filepath = "D:/project/AppTexToMesh/res/test_render.png"
bpy.ops.render.render(write_still=True)

print("Démarrage du baking...")

try:
    # Lancer le baking
    bpy.ops.object.bake(type='EMIT')
    print("Baking terminé avec succès!")
    
    # Vérifier si l'image contient des données
    pixels = list(baked_img.pixels)
    non_zero_pixels = sum(1 for p in pixels if p > 0.01)
    print(f"Pixels non-noirs dans l'image bakée: {non_zero_pixels}/{len(pixels)}")
    
    # Sauvegarder l'image
    baked_img.filepath_raw = output_image_path
    baked_img.file_format = 'PNG'
    baked_img.save()
    
    print(f"Image sauvegardée: {output_image_path}")
    
except Exception as e:
    print(f"ERREUR pendant le baking: {str(e)}")
    import traceback
    traceback.print_exc()

print("Script terminé.")