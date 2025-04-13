import math
import random

import pygame

from ..utils.elements import ElementSingleton
from .particles import Particle

def extract_color(img, color, add_surf=None):
    img = img.copy()
    img.set_colorkey(color)
    mask = pygame.mask.from_surface(img)
    if mask.count() == img.get_width() * img.get_height():
        return None
    surf = mask.to_surface(setcolor=(0, 0, 0, 0), unsetcolor=color)
    if add_surf:
        base_surf = pygame.Surface(img.get_size())
        base_surf.fill(color)
        add_surf = (add_surf[0].convert(), add_surf[1])
        add_surf[0].set_colorkey(add_surf[1])
        base_surf.blit(add_surf[0], (0, 0))
        base_surf.blit(surf, (0, 0))
        base_surf.set_colorkey((0, 0, 0))
        return base_surf
    else:
        return surf
    
class FoliageAssets(ElementSingleton):
    def __init__(self):
        super().__init__()
        self.foliage = {}
        self.global_speed = 0.5
        self.renders = 0
        
    def __getitem__(self, key):
        return self.foliage[key]
    
    def render_functions(self):
        leaf_colors = [[84, 92, 126], [197, 105, 129], [163, 162, 154]]
        
        def foliage_render(tile, offset=(0, 0), group='default'):
            if tile.tile_id in self.e['FoliageAssets'].foliage[tile.group]:
                tile.e['FoliageAssets'].renders += 1
                foliage = self.e['FoliageAssets'].foliage[tile.group][tile.tile_id]
                tile.e['Renderer'].renderf(foliage.render, (tile.raw_pos[0] + tile.offset[0] - offset[0], tile.raw_pos[1] + tile.offset[1] - offset[1]), m_clock=tile.e['Window'].time * tile.e['FoliageAssets'].global_speed, z=tile.layer, group=group, seed=sum(tile.raw_pos))

                if random.random() < tile.e['Window'].dt * 0.5:
                    leaf_point = foliage.find_leaf_point()
                    wpos = (leaf_point[0] + tile.raw_pos[0], leaf_point[1] + tile.raw_pos[1])
                    colors = {(255, 255, 255): random.choice(leaf_colors)}
                    if not tile.map.physics_gridtile(wpos):
                        leaf = Particle(wpos, 'leaf', velocity=[-15, 15], decay_rate=0.1, advance=random.random() * 0.5, behavior='grass', z=10, colors=colors)
                        tile.e['EntityGroups'].add(leaf, 'particles')

        funcs = {f_id: foliage_render for f_id in self.foliage}
        
        return funcs
        
    def load(self):
        for ss_id in self.e['Assets'].spritesheets:
            if 'foliage_colors' in self.e['Assets'].spritesheets[ss_id]['config']:
                self.foliage[ss_id] = {}
                colors = self.e['Assets'].spritesheets[ss_id]['config']['foliage_colors']
                for tile_id in self.e['Assets'].spritesheets[ss_id]['assets']:
                    motion_scale = self.e['Assets'].spritesheets[ss_id]['config'][tile_id]['motion_scale'] if 'motion_scale' in self.e['Assets'].spritesheets[ss_id]['config'][tile_id] else 1
                    self.foliage[ss_id][tile_id] = AnimatedFoliage(self.e['Assets'].spritesheets[ss_id]['assets'][tile_id], colors, motion_scale=motion_scale)

class AnimatedFoliage:
    def __init__(self, image, color_chain, motion_scale=1):
        self.motion_scale = motion_scale
        self.base_image = image.copy()
        self.color_chain = color_chain
        self.layers = []

        for i, color in enumerate(color_chain[::-1]):
            if not len(self.layers):
                next_layer = extract_color(self.base_image, color)
                if next_layer:
                    self.layers.append(next_layer)
            else:
                next_layer = extract_color(self.base_image, color, add_surf=(self.layers[-1], color_chain[::-1][i - 1]))
                if next_layer:
                    self.layers.append(next_layer)

        self.layers = self.layers[::-1]

    def find_leaf_point(self):
        while True:
            point = (int(random.random() * self.layers[0].get_width()), int(random.random() * self.layers[0].get_height()))
            color = self.layers[0].get_at(point)
            if list(color)[:3] != [0, 0, 0]:
                return point

    def render(self, surf, pos, m_clock=0, seed=14):
        surf.blit(pygame.transform.rotate(self.layers[0], math.sin(m_clock * 0.8 + (2.7 * seed)) * 1.2), (pos[0] + math.sin(m_clock * 1.7 + (2.7 * seed)) * 1.5 * self.motion_scale, pos[1] + math.sin(m_clock + (2.2 * seed)) * self.motion_scale))
        surf.blit(self.base_image, pos)
        for i, layer in enumerate(self.layers):
            if i != 0:
                layer_img = pygame.transform.rotate(layer, math.sin(m_clock * 1.1) * 4.5)
                offset = ((layer_img.get_width() - layer.get_width()) // 2, (layer_img.get_height() - layer.get_height()) // 2)
                surf.blit(layer_img, (pos[0] + math.sin(m_clock * (1.25 * i) + (2.7 * seed)) * 1.5 * self.motion_scale - offset[0], pos[1] + math.sin(m_clock * (1.25 * i) + (2.2 * seed)) * self.motion_scale - offset[1]))
            else:
                surf.blit(layer, pos)
