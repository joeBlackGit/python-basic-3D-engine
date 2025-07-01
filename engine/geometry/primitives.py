import numpy as np

def create_cube():
    vertices = np.array([
        # x, y, z
        -1, -1, -1,
         1, -1, -1,
         1,  1, -1,
        -1,  1, -1,
        -1, -1,  1,
         1, -1,  1,
         1,  1,  1,
        -1,  1,  1,
    ], dtype='f4')

    indices = np.array([
        0, 1, 2, 2, 3, 0,  # back face
        4, 5, 6, 6, 7, 4,  # front face
        0, 1, 5, 5, 4, 0,  # bottom
        3, 2, 6, 6, 7, 3,  # top
        1, 2, 6, 6, 5, 1,  # right
        0, 3, 7, 7, 4, 0   # left
    ], dtype='i4')

    return vertices, indices