# BTexProjection
a python code for blender ,using camera intrinsic , pose matrix , mesh(.gltf) and an image of the mesh to bake the image on the mesh with the right parameter 



json for the intrinsic and camera pose  matrix must look like that : 
[{
    "name": "Camera 1 - Pos: (0.486, 0.158, 0.208)",
    "pose": [
      [
        0.41210145434442225,
        -0.052346168009846636,
        -0.9096330414084004,
        -0.003084626480626029
      ],
      [
        0.18927432020411677,
        -0.9716514198984573,
        0.14166421538476562,
        0.031764885533649104
      ],
      [
        -0.8912618150905385,
        -0.23055020473640161,
        -0.3905111778906232,
        0.5507717849217422
      ],
      [
        0.0,
        0.0,
        0.0,
        1.0
      ]
    ],
    "camera_params": {
      "focal_length_x": 3828.92,
      "focal_length_y": 3828.92,
      "principal_point_x": 1352.0,
      "principal_point_y": 900.0
    },
    "timestamp": ""
  }]


  
