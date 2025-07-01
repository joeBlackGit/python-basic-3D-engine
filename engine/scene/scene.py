import numpy as np

class Object3D:
    def __init__(self, mesh, shader, position=(0, 0, 0), rotation=(0, 0, 0), scale=(1, 1, 1)):
        self.mesh = mesh
        self.shader = shader  # A moderngl.Program
        self.position = np.array(position, dtype='f4')
        self.rotation = np.array(rotation, dtype='f4')  # Euler angles in degrees
        self.scale = np.array(scale, dtype='f4')

    def get_model_matrix(self):
        rx, ry, rz = np.radians(self.rotation)
        sx, sy, sz = self.scale
        px, py, pz = self.position

        cos, sin = np.cos, np.sin

        # Compose rotation matrices
        Rx = np.array([
            [1, 0, 0, 0],
            [0, cos(rx), -sin(rx), 0],
            [0, sin(rx),  cos(rx), 0],
            [0, 0, 0, 1]
        ], dtype='f4')

        Ry = np.array([
            [ cos(ry), 0, sin(ry), 0],
            [ 0, 1, 0, 0],
            [-sin(ry), 0, cos(ry), 0],
            [ 0, 0, 0, 1]
        ], dtype='f4')

        Rz = np.array([
            [cos(rz), -sin(rz), 0, 0],
            [sin(rz),  cos(rz), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ], dtype='f4')

        S = np.diag([sx, sy, sz, 1])
        T = np.identity(4, dtype='f4')
        T[:3, 3] = [px, py, pz]

        return T @ Rz @ Ry @ Rx @ S


class Scene:
    def __init__(self):
        self.objects = []

    def add(self, obj):
        self.objects.append(obj)

    def render_all(self, renderer, camera, outline=False):
        view = camera.get_view_matrix()
        proj = camera.get_proj_matrix()
        for obj in self.objects:
            model = obj.get_model_matrix()
            mvp = (proj @ view @ model).T  # Transposed for OpenGL
            renderer.render(obj, mvp, outline=outline)
