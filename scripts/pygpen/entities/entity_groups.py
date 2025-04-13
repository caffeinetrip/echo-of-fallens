import pygame

from ..utils.elements import ElementSingleton
from ..data_structures.entity_quads import EQuads

class EntityGroups(ElementSingleton):
    def __init__(self, quad_size=64, quad_groups=[]):
        super().__init__()
        self.groups = {}
        self.locked = False
        self.add_queue = []
        
        self.quad_groups = set(quad_groups)
        self.equads = EQuads(quad_size=quad_size)
        
    def set_quad_groups(self, quad_groups=[]):
        self.quad_groups = set(quad_groups)
        
    def add(self, entity, group):
        if self.locked:
            self.add_queue.append((entity, group))
        else:
            # two insert cases depending on whether the group is spatially partitioned
            if group in self.quad_groups:
                self.equads.insert(entity, egroup=group)
            else:
                if group not in self.groups:
                    self.groups[group] = []
                self.groups[group].append(entity)
    
    def update(self, group=None, unlock=True, quad_rect=pygame.Rect(0, 0, 100, 100)):
        dt = self.e['Window'].dt
        
        # update active entities based on quads (only applies when doing a general update)
        if len(self.quad_groups) and not group:
            self.equads.update_active(quad_rect)
            # update local group listing based on spatial partitioning
            self.groups.update(self.equads.active_entities)
            
        self.locked = True
        if group:
            if group in self.groups:
                for entity in self.groups[group].copy():
                    kill = entity.update(dt)
                    if kill:
                        self.groups[group].remove(entity)
                        # delete from quads if applicable
                        if group in self.quad_groups:
                            self.equads.delete(entity)
        else:
            for group in self.groups:
                self.update(group, unlock=False)
        if unlock:
            self.locked = False
            if len(self.add_queue):
                for addition in self.add_queue:
                    self.add(*addition)
                self.add_queue = []
    
    def render(self, surf, group=None, offset=(0, 0)):
        if group:
            if group in self.groups:
                for entity in self.groups[group]:
                    entity.render(surf, offset=offset)
        else:
            for group in self.groups:
                self.render(surf, group=group, offset=offset)
    
    def renderz(self, group=None, render_group='default', offset=(0, 0)):
        if group:
            if group in self.groups:
                for entity in self.groups[group]:
                    entity.renderz(group=render_group, offset=offset)
        else:
            for group in self.groups:
                self.renderz(group=group, render_group=render_group, offset=offset)