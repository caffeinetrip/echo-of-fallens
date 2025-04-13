import pygame

from ..utils.game_math import box_points

class SQuads:
    def __init__(self, quad_size=64):
        self.quad_size = quad_size
        self.reset()
        
    def reset(self):
        self.quads = {}
        self.known_locs = {}
        
    def grid_locs(self, rect):
        topleft = (int(rect.left // self.quad_size), int(rect.top // self.quad_size))
        bottomright = (int(rect.right // self.quad_size), int(rect.bottom // self.quad_size))
        grid_rect = pygame.Rect(*topleft, bottomright[0] - topleft[0] + 1, bottomright[1] - topleft[1] + 1)
        quad_locs = box_points(grid_rect)
        return quad_locs
        
    def insert(self, obj, rect):
        quad_locs = self.grid_locs(rect)
        
        if id(obj) not in self.known_locs:
            self.known_locs[id(obj)] = []
            
        for quad in quad_locs:
            if quad not in self.quads:
                self.quads[quad] = []
            self.quads[quad].append(obj)
            self.known_locs[id(obj)].append(quad)
    
    def delete(self, obj):
        if id(obj) in self.known_locs:
            for quad in self.known_locs[id(obj)]:
                self.quads[quad].remove(obj)
            del self.known_locs[id(obj)]
            
    def query(self, rect):
        # doesn't use grid_locs in order to save on performance (since grid_locs() iterates twice)
        objects = set()
        for y in range(int(rect.top // self.quad_size), int(rect.bottom // self.quad_size + 1)):
            for x in range(int(rect.left // self.quad_size), int(rect.right // self.quad_size + 1)):
                loc = (x, y)
                if loc in self.quads:
                    for obj in self.quads[loc]:
                        objects.add(obj)
        return objects