import pygame

from ..utils.elements import ElementSingleton
from ..utils.gfx import clip
from ..assets.asset_utils import load_img_directory

class UIBoxer(ElementSingleton):
    def __init__(self, path=None):
        super().__init__()

        self.path = path
        self.src_boxes = {}
        self.load()
        self.boxes = {}
        self.box_cache = {}
            
    def load(self, path=None):
        if path:
            self.path = path
        if self.path:
            self.src_boxes = load_img_directory(self.path)
        for box in self.src_boxes:
            self.parse_box(box)

    def parse_box(self, box_name):
        box_img = self.src_boxes[box_name]
        box_img.set_colorkey(None)
        corner_size = int(box_name.split('_')[-1])
        edge_size = (box_img.get_width() - corner_size * 2, corner_size)

        box_parts = {
            'tl_corner': clip(box_img, pygame.Rect(0, 0, corner_size, corner_size)),
            'tr_corner': clip(box_img, pygame.Rect(box_img.get_width() - corner_size, 0, corner_size, corner_size)),
            'br_corner': clip(box_img, pygame.Rect(box_img.get_width() - corner_size, box_img.get_height() - corner_size, corner_size, corner_size)),
            'bl_corner': clip(box_img, pygame.Rect(0, box_img.get_height() - corner_size, corner_size, corner_size)),
            'top_edge': clip(box_img, pygame.Rect(corner_size, 0, *edge_size)),
            'left_edge': clip(box_img, pygame.Rect(0, corner_size, *edge_size[::-1])),
            'bottom_edge': clip(box_img, pygame.Rect(corner_size, box_img.get_height() - edge_size[1], *edge_size)),
            'right_edge': clip(box_img, pygame.Rect(box_img.get_width() - edge_size[1], corner_size, *edge_size[::-1])),
            'color': box_img.get_at((box_img.get_width() // 2, box_img.get_height() // 2)),
            'min_size': corner_size * 2,
            'corner_size': corner_size,
            'edge_size': edge_size[0],
        }

        self.boxes['_'.join(box_name.split('_')[:-1])] = box_parts

    def ui_box(self, box_id, size, cache=True):
        cache_id = (box_id, tuple(size))
        if cache_id not in self.box_cache:
            bd = self.boxes[box_id]

            size = (max(bd['min_size'], size[0]), max(self.boxes[box_id]['min_size'], size[1]))

            box_surf = pygame.Surface(size)
            box_surf.fill(bd['color'])

            box_surf.blit(bd['tl_corner'], (0, 0))
            box_surf.blit(bd['tr_corner'], (size[0] - bd['corner_size'], 0))
            box_surf.blit(bd['bl_corner'], (0, size[1] - bd['corner_size']))
            box_surf.blit(bd['br_corner'], (size[0] - bd['corner_size'], size[1] - bd['corner_size']))

            horizontal_remainder = (size[0] - bd['min_size']) % bd['edge_size']
            vertical_remainder = (size[1] - bd['min_size']) % bd['edge_size']
            horizontal_count = (size[0] - bd['min_size']) // bd['edge_size']
            vertical_count = (size[1] - bd['min_size']) // bd['edge_size']

            top_crop = clip(bd['top_edge'], pygame.Rect(0, 0, horizontal_remainder, bd['corner_size']))
            bottom_crop = clip(bd['bottom_edge'], pygame.Rect(0, 0, horizontal_remainder, bd['corner_size']))
            left_crop = clip(bd['left_edge'], pygame.Rect(0, 0, bd['corner_size'], vertical_remainder))
            right_crop = clip(bd['right_edge'], pygame.Rect(0, 0, bd['corner_size'], vertical_remainder))

            box_surf.blit(top_crop, (size[0] - bd['corner_size'] - horizontal_remainder, 0))
            box_surf.blit(bottom_crop, (size[0] - bd['corner_size'] - horizontal_remainder, size[1] - bd['corner_size']))
            box_surf.blit(left_crop, (0, size[1] - bd['corner_size'] - vertical_remainder))
            box_surf.blit(right_crop, (size[0] - bd['corner_size'], size[1] - bd['corner_size'] - vertical_remainder))

            for i in range(horizontal_count):
                box_surf.blit(bd['top_edge'], (bd['corner_size'] + i * bd['edge_size'], 0))
                box_surf.blit(bd['bottom_edge'], (bd['corner_size'] + i * bd['edge_size'], size[1] - bd['corner_size']))
            for i in range(vertical_count):
                box_surf.blit(bd['left_edge'], (0, bd['corner_size'] + i * bd['edge_size']))
                box_surf.blit(bd['right_edge'], (size[0] - bd['corner_size'], bd['corner_size'] + i * bd['edge_size']))

            box_surf.set_colorkey((0, 0, 0))

            if cache:
                self.box_cache[cache_id] = box_surf

        else:
            box_surf = self.box_cache[cache_id]

        return box_surf
