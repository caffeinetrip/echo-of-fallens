import pygame

from ..utils.elements import ElementSingleton

class Renderer(ElementSingleton):
    def __init__(self, groups=['default']):
        super().__init__()
        self.groups = groups
        self.render_queue = {}
        self.i = 0
        self.render_count = 0
        self.reset()
        
    def set_groups(self, groups):
        self.groups = groups
        self.reset()
    
    def reset(self):
        for group in self.groups:
            self.render_queue[group] = []
    
    def blit(self, surf, pos, z=0, group='default'):
        self.render_queue[group].append((z, self.i, surf, pos))
        self.i += 1
    
    # works with anything that takes the surface as the first argument
    def renderf(self, func, *args, **kwargs):
        z = kwargs['z'] if 'z' in kwargs else 0
        group = kwargs['group'] if 'group' in kwargs else 'default'
        if 'z' in kwargs:
            del kwargs['z']
        if 'group' in kwargs:
            del kwargs['group']
        self.render_queue[group].append((z, self.i, func, args, kwargs))
        self.i += 1

    def cycle(self, dest_surfs):
        self.render_count = 0
        for group in dest_surfs:
            if group in self.render_queue:
                self.render_queue[group].sort(key=lambda x: x.priority if hasattr(x, 'priority') else 0)
                self.render_count += len(self.render_queue[group])
                for blit in self.render_queue[group]:
                    if len(blit) > 4:
                        blit[2](dest_surfs[group], *blit[3], **blit[4])
                    else:
                        if blit[0] != 107:
                            dest_surfs[group].blit(blit[2], blit[3])
                        else:
                            dest_surfs[group].blit(blit[2], blit[3], special_flags=pygame.BLEND_RGBA_ADD)
        self.reset()
        return dest_surfs
