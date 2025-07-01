import moderngl
import numpy as np
import os
from engine.geometry.primitives import create_cube
import textwrap

class Mesh:
    def __init__(self, ctx, vertices, indices, shader):
        self.ctx = ctx
        self.vbo = ctx.buffer(vertices.tobytes())
        self.ibo = ctx.buffer(indices.tobytes())
        self.vao = ctx.vertex_array(
            shader,
            [(self.vbo, '3f', 'in_position')],
            self.ibo
        )


class Renderer:
    def __init__(self, ctx: moderngl.Context):
        self.ctx = ctx

        # Load shaders
        shader_path = os.path.join(os.path.dirname(__file__), '..', 'shaders')
        with open(os.path.join(shader_path, 'cube.vert')) as f:
            vertex_shader = f.read()
        with open(os.path.join(shader_path, 'cube.frag')) as f:
            fragment_shader = f.read()

        self.prog = self.ctx.program(
            vertex_shader=vertex_shader,
            fragment_shader=fragment_shader
        )
        self.mvp = self.prog['mvp']

        vertices, indices = create_cube()
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.ibo = self.ctx.buffer(indices.tobytes())
        self.vao = self.ctx.vertex_array(
            self.prog,
            [(self.vbo, '3f', 'in_position')],
            self.ibo
        )

    def render(self, mvp_matrix):
        self.mvp.write(mvp_matrix.tobytes())
        self.vao.render()