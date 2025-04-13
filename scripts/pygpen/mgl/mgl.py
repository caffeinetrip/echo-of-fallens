from array import array

import moderngl
import pygame

from .render_object import RenderObject
from ..utils.elements import ElementSingleton
from ..utils.io import read_f

default_vert_shader = '''
#version 330

in vec2 vert;
in vec2 texcoord;
out vec2 uv;

void main() {
  uv = texcoord;
  gl_Position = vec4(vert, 0.0, 1.0);
}
'''

default_frag_shader = '''
#version 330

uniform sampler2D surface;

out vec4 f_color;
in vec2 uv;

void main() {
  f_color = vec4(texture(surface, uv).rgb, 1.0);
}
'''

class MGL(ElementSingleton):
    def __init__(self):
        super().__init__()
        self.ctx = moderngl.create_context(require=330)
        self.quad_buffer = self.ctx.buffer(data=array('f', [
            # position (x, y) , texture coordinates (x, y)
            -1.0, 1.0, 0.0, 0.0,
            -1.0, -1.0, 0.0, 1.0,
            1.0, 1.0, 1.0, 0.0,
            1.0, -1.0, 1.0, 1.0,
        ]))
        
        self.quad_buffer_notex = self.ctx.buffer(data=array('f', [
            # position (x, y)
            -1.0, 1.0,
            -1.0, -1.0,
            1.0, 1.0,
            1.0, -1.0,
        ]))
        
        self.default_vert = default_vert_shader
        self.default_frag = default_frag_shader
        
    def default_ro(self):
        return RenderObject(self.default_frag, default_ro=True)
        
    def render_object(self, frag_path, vert_shader=None, vao_args=['2f 2f', 'vert', 'texcoord'], buffer=None):
        frag_shader = read_f(frag_path)
        if vert_shader:
            vert_shader = read_f(vert_shader)
        return RenderObject(frag_shader, vert_shader=vert_shader, vao_args=vao_args, buffer=buffer)
            
    def pg2tx(self, surf):
        channels = 4
        new_tex = self.ctx.texture(surf.get_size(), channels)
        new_tex.filter = (moderngl.NEAREST, moderngl.NEAREST)
        new_tex.swizzle = 'BGRA'
        new_tex.write(surf.get_view('1'))
        return new_tex
    
    def pg2tx_update(self, tex, surf):
        tex.write(surf.get_view('1'))
        return tex