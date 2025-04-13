import time

import numpy as np
import moderngl
import pygame

from ..utils.elements import ElementSingleton

cs = '''
#version 430

layout(local_size_x = 1, local_size_y = 1, local_size_z = 1) in;

layout(std430, binding = 0) buffer Input {
    float data[];
};

layout(std430, binding = 1) buffer Output {
    float data_out[];
};

uniform float spread = 0.5;
uniform float springiness = 0.02;
uniform float dampening = 0.05;

void main() {
    uint index = gl_WorkGroupID.x;
    float pos = data[index];
    float vel = data[index + gl_NumWorkGroups.x];
    if (pos < 9000000.0) {
        float l_pos = data[index - 1];
        if (l_pos >= 9000000.0) {
            l_pos = 0;
        }
        float r_pos = data[index + 1];
        if (r_pos >= 9000000.0) {
            r_pos = 0;
        }
        float shift = ((l_pos - pos) + (r_pos - pos)) * spread;
        data_out[index + gl_NumWorkGroups.x] = vel + (shift * spread - springiness * pos - vel * dampening);
        data_out[index] = data[index] + (vel + shift);
        // stabilization case
        if ((abs(data_out[index]) < 0.05) && (abs(data_out[index + gl_NumWorkGroups.x]) < 0.05)) {
            data_out[index] = 0;
            data_out[index + gl_NumWorkGroups.x] = 0;
        }
    } else {
        data_out[index] = pos;
        data_out[index + gl_NumWorkGroups.x] = vel;
    }
}
'''

class WaterManager(ElementSingleton):
    def __init__(self, spread=0.5, springiness=0.015, dampening=0.065, hz=60):
        super().__init__()
        self.hz = hz
        self.cs_prog = self.e['MGL'].ctx.compute_shader(cs) if self.e['Window'].opengl else None
        self.spread = spread
        self.springiness = springiness
        self.dampening = dampening
        self.update_timer = time.time()
        self.clear()

    def render_functions(self, tile_group, spacing=2):
        def water_render(tile, offset=(0, 0), group='default'):
            if not hasattr(tile, '_water'):
                if hasattr(tile, 'water_size'):
                    tile.rect.width = tile.water_size[0]
                    tile.rect.height = tile.water_size[1]
                else:
                    tile.rect.width = tile.img.get_width()
                    tile.rect.height = tile.img.get_height()
                foam_color = tile.img.get_at((0, 0))
                water_color = tile.img.get_at((1, 1))
                tile._water = Water(tile.rect, spacing=spacing, colors=(water_color, foam_color))
            tile.e['WaterManager'].queue(tile._water)
            tile.e['Renderer'].renderf(tile._water.render, (offset[0], offset[1]), group=group, z=tile.layer)
        funcs = {tile_group: water_render}
        return funcs            
    
    def clear(self):
        self.compute_buffer = []

    def impact(self, start_p, end_p, force, width=1, fast=True):
        collisions = []
        for water in self.compute_buffer:
            if water.impact2p(start_p, end_p, force, width=width, fast=fast):
                collisions.append(water)
        return collisions

    def queue(self, water):
        if self.cs_prog:
            self.compute_buffer.append(water)
    
    def compute(self, waters=[], restricted=False):
        if self.cs_prog:
            updates = 1
            if restricted:
                updates = 0
                while (self.update_timer + (1 / self.hz)) < self.e['Window'].time:
                    self.update_timer += (1 / self.hz)
                    updates += 1
            # will attempt to keep up with 60hz in its own time
            waters = self.compute_buffer + waters
            if len(waters):
                for i in range(updates):
                    self.cs_prog['spread'] = self.spread
                    self.cs_prog['springiness'] = self.springiness
                    self.cs_prog['dampening'] = self.dampening
                    buffer_stack = tuple([water.points for water in waters] + [water.velocities for water in waters])
                    in_buff = np.concatenate(buffer_stack)
                    buffer_hwidth = int(len(in_buff) / 2)
                    in_buff = self.e['MGL'].ctx.buffer(data=in_buff)
                    out_buff = self.e['MGL'].ctx.buffer(data=np.zeros(buffer_hwidth * 2, dtype=np.float32))
                    in_buff.bind_to_storage_buffer(0)
                    out_buff.bind_to_storage_buffer(1)
                    self.cs_prog.run(buffer_hwidth)
                    out_buff = np.frombuffer(out_buff.read(), dtype=np.float32)
                    x = 0
                    for water in waters:
                        water.points = out_buff[x:x + len(water.points)].copy()
                        water.velocities = out_buff[x + buffer_hwidth:x + len(water.points) + buffer_hwidth].copy()
                        x += len(water.points)
            self.clear()

class Water:
    def __init__(self, rect, spacing=4, colors=((0, 0, 255), (255, 255, 255))):
        self.spacing = spacing
        self.colors = colors
        self.rect = rect
        self.pos = (rect.x, rect.y)
        self.size = (rect.width, rect.height)
        self.pwidth = max(0, self.size[0] // spacing - 1)
        self.points = np.zeros(self.pwidth + 2, dtype=np.float32)
        self.points[0] = 9999999
        self.points[-1] = 9999999
        self.velocities = self.points.copy()
        
    def surface_level(self, world_pos):
        if (world_pos >= self.pos[0]) and (world_pos <= self.pos[0] + self.size[0]):
            index = max(0, min(self.pwidth - 1, int((world_pos - self.pos[0]) / self.spacing))) + 1
            return self.points[index] + self.pos[1]
        return self.pos[1]

    # faster adjusted surface level for collisions
    def qsurface_level(self, world_pos):
        index = max(0, min(self.pwidth - 1, int((world_pos - self.pos[0]) / self.spacing))) + 1
        return self.points[index] + self.pos[1]
    
    def impact(self, world_pos, amount, width=1):
        if (world_pos >= self.pos[0]) and (world_pos <= self.pos[0] + self.size[0]):
            index = max(0, min(self.pwidth - 1, int((world_pos - self.pos[0]) / self.spacing))) + 1
            for i in range(width * 2 - 1):
                p = i - (width - 1)
                force = (1 - abs(p) / width) * amount
                self.velocities[max(1, min(self.pwidth, index + p))] += force

    def impact2p(self, p1, p2, amount, width=1, fast=False):
        if (self.pos[0] <= p2[0] <= self.pos[0] + self.size[0]):
            sl = self.pos[1] if fast else self.qsurface_level(p2[0])
            if (p2[1] > sl > p1[1]):
                self.impact(p2[0], amount, width=width)
                return True
            elif (p2[1] < sl < p1[1]):
                self.impact(p2[0], -amount, width=width)
                return True
        return False
    
    def render(self, surf, offset=(0, 0)):
        surface_points = [(0, 0)] + [((i + 1) * self.spacing, self.points[i + 1]) for i in range(self.pwidth)] + [(self.size[0], 0)]
        surface_points[0] = (0, self.points[1])
        surface_points[-1] = (self.size[0], self.points[-2])
        render_points = [(p[0] + self.pos[0] - offset[0], p[1] + self.pos[1] - offset[1]) for p in surface_points]
        render_points_box = [(self.pos[0] - offset[0], self.pos[1] - offset[1] + self.size[1])] + render_points + [(self.pos[0] - offset[0] + self.size[0], self.pos[1] - offset[1] + self.size[1])]
        pygame.draw.polygon(surf, self.colors[0], render_points_box)
        pygame.draw.lines(surf, self.colors[1], False, render_points, 1)