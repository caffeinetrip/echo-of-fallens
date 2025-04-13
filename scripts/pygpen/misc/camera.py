import pygame

from ..utils.gfx import smooth_approach
from ..utils.elements import Element

class Camera(Element):
    def __init__(self, size, pos=(0, 0), slowness=1, tilemap_lock=None):
        super().__init__()
        self.size = size
        self.slowness = slowness
        self.pos = list(pos)
        self.int_pos = (int(self.pos[0]), int(self.pos[1]))
        self.target_entity = None
        self.target_pos = None
        self.tilemap_lock = tilemap_lock
        self.rect = pygame.Rect(self.pos[0] - 20, self.pos[1] - 20, self.size[0] + 40, self.size[1] + 40)
    
    @property
    def target(self):
        if self.target_entity:
            return (self.target_entity.center[0] - self.size[0] // 2, self.target_entity.center[1] - self.size[1] // 2)
        elif self.target_pos:
            return (self.target_pos[0] - self.size[0] // 2, self.target_pos[0] - self.size[1] // 2)
        
    @property
    def center(self):
        return (self.pos[0] + self.size[0] / 2, self.pos[1] + self.size[1] / 2)
    
    def set_target(self, target):
        if hasattr(target, 'center'):
            self.target_entity = target
            self.target_pos = None
        elif target:
            self.target_pos = tuple(target)
            self.target_entity = None
        else:
            self.target_pos = None
            self.target_entity = None
            
    def __iter__(self):
        for v in self.int_pos:
            yield v
        
    def __getitem__(self, item):
        return self.int_pos[item]
    
    def move(self, movement):
        self.pos[0] += movement[0]
        self.pos[1] += movement[1]
    
    def update(self):
        dt = self.e['Window'].dt
        self.rect = pygame.Rect(self.pos[0] - 30, self.pos[1] - 30, self.size[0] + 60, self.size[1] + 60)
        target = self.target
        if target:
            self.pos[0] = smooth_approach(self.pos[0], target[0], slowness=self.slowness)
            self.pos[1] = smooth_approach(self.pos[1], target[1], slowness=self.slowness)
            if self.tilemap_lock:
                self.pos[0] = max(0, min(self.tilemap_lock.dimensions[0] * self.tilemap_lock.tile_size[0] - self.size[0], self.pos[0]))
                self.pos[1] = max(0, min(self.tilemap_lock.dimensions[1] * self.tilemap_lock.tile_size[1] - self.size[1], self.pos[1]))
        self.int_pos = (int(self.pos[0]), int(self.pos[1]))
    
    