import os

import pygame

from ..utils.io import read_tjson, write_tjson
from ..utils.gfx import clip
from .asset_utils import load_img_directory

def load_spritesheet_config(path):
    if os.path.isfile(path):
        config = read_tjson(path, loose=True)
    else:
        config = {}
    write_tjson(path, config)
    return config

def parse_spritesheet(surf, split_color=(0, 255, 255)):
    row_start = None
    loc = [0, 0]
    tiles = {}
    for y in range(surf.get_height() - 1):
        c1 = surf.get_at((1, y))
        c2 = surf.get_at((1, y + 1))
        c3 = surf.get_at((0, y + 1))
        if (c1 == split_color) and (c2 != split_color) and (c3 == split_color):
            row_start = y
        if (c1 != split_color) and (c2 == split_color) and (c3 == split_color) and row_start != None:
            row_bounds_y = (row_start, y)
            col_start = None
            for x in range(surf.get_width() - 1):
                c1 = surf.get_at((x, row_bounds_y[0] + 1))
                c2 = surf.get_at((x + 1, row_bounds_y[0] + 1))
                if (c1 == split_color) and (c2 != split_color):
                    col_start = x
                if (c1 != split_color) and (c2 == split_color) and col_start != None:
                    col_bounds_x = (col_start, x)
                    if col_start == 0:
                        tile_bounds_y = row_bounds_y
                    else:
                        y2 = row_start
                        while True:
                            c1 = surf.get_at((col_start + 1, y2))
                            c2 = surf.get_at((col_start + 1, y2 + 1))
                            if (c1 != split_color) and (c2 == split_color):
                                break
                            y2 += 1
                        tile_bounds_y = (row_start, y2)
                    rect = pygame.Rect(col_bounds_x[0] + 1, tile_bounds_y[0] + 1, col_bounds_x[1] - col_bounds_x[0], tile_bounds_y[1] - tile_bounds_y[0])
                    tiles[tuple(loc)] = clip(surf, rect)
                    loc[0] += 1
                    col_start = None
            loc[1] += 1
            loc[0] = 0
            row_start = None
    return tiles

def load_spritesheets(path, split_color=(0, 255, 255), colorkey=(0, 0, 0)):
    spritesheets = load_img_directory(path, colorkey=colorkey)
    for spritesheet in spritesheets:
        spritesheets[spritesheet] = {
            'assets': parse_spritesheet(spritesheets[spritesheet], split_color=split_color),
            'config': load_spritesheet_config(path + '/' + spritesheet + '.json'),
        }
        for tile in spritesheets[spritesheet]['assets']:
            if tile not in spritesheets[spritesheet]['config']:
                spritesheets[spritesheet]['config'][tile] = {'offset': (0, 0)}
            if 'offset' not in spritesheets[spritesheet]['config'][tile]:
                spritesheets[spritesheet]['config'][tile]['offset'] = (0, 0)
    return spritesheets