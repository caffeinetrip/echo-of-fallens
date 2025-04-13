import time

import pygame

from ..utils.elements import ElementSingleton
from ..mgl.mgl import MGL

class Window(ElementSingleton):
    def __init__(self, dimensions=(640, 480), caption='pygpen window', flags=0, fps_cap=60, dt_cap=1, opengl=False, frag_path=None):
        super().__init__()
        self.opengl = opengl
        self.frag_path = frag_path
        self.dimensions = dimensions
        self.flags = flags
        if self.opengl:
            self.flags = self.flags | pygame.DOUBLEBUF | pygame.OPENGL
        self.fps_cap = fps_cap
        self.dt_cap = dt_cap
        self.background_color = (152, 252, 152)
        self.time = time.time()
        self.start_time = time.time()
        self.runtime_ = self.time - self.start_time
        self.frames = 0
        self.frame_log = []
        
        pygame.init()
        pygame.display.set_caption(caption)
        self.screen = pygame.display.set_mode(self.dimensions, self.flags)
        self.clock = pygame.time.Clock()
        
        self.last_frame = time.time()
        self.dt = 0.1
        self.tremor = 0
        self.fight = False
        
        self.transition = 0.0  
        self.transition_speed = 0.7
        self.transitioning = False
        
        self.e_transition = 1.0  
        self.e_transition_speed = 0.75
        self.e_transitioning = False
        
        self.open = True
        self.noise_gain = 1
                
        self.render_object = None
        if self.opengl:
            MGL()
            if not self.frag_path:
                self.render_object = self.e['MGL'].default_ro()
            else:
                self.render_object = self.e['MGL'].render_object(frag_path)

    @property
    def fps(self):
        return len(self.frame_log) / sum(self.frame_log)
    
    def start_transition(self):
        if self.open:
            self.transition = 0.0
        else:
            self.transition = 1.0
            
        self.transitioning = True

    def update_transition(self):
        if self.transitioning:
   
            self.transition += self.dt * self.transition_speed * self.open
            if self.open:
                if self.transition >= 1.0:
                    self.transition = 1.0
                    self.transitioning = False
            else:
                if self.transition <= 0.0:
                    self.transition = 0.0
                    self.transitioning = False
    
    def e_start_transition(self):
        if self.open:
            self.e_transition = 0.0
        else:
            self.e_transition = 1.0
            
        self.e_transitioning = True

    def e_update_transition(self):
        if self.e_transitioning:
   
            self.e_transition += self.dt * self.e_transition_speed * self.open
            if self.open:
                if self.e_transition >= 1.0:
                    self.e_transition = 1.0
                    self.e_transitioning = False
            else:
                if self.e_transition <= 0.0:
                    self.e_transition = 0.0
                    self.e_transitioning = False
    
    def cycle(self, uniforms={}):
        if self.render_object:
            if self.render_object.default and ('surface' not in uniforms):
                uniforms['surface'] = self.screen
            uniforms['time'] = self.dt
            uniforms['tremor'] = self.tremor
            uniforms['fight'] = self.fight
            uniforms['transition'] = self.transition
            uniforms['e_transition'] = self.e_transition
            uniforms['noise_gain'] = self.noise_gain
            self.render_object.render(uniforms=uniforms)
        self.update_transition()
        self.e_update_transition()
        pygame.display.flip()
        self.clock.tick(self.fps_cap)
        self.dt = min(time.time() - self.last_frame, self.dt_cap)
        self.frame_log.append(self.dt)
        self.frame_log = self.frame_log[-60:]
        self.last_frame = time.time()
        self.screen.fill(self.background_color)
        if self.render_object:
            self.e['MGL'].ctx.clear(*[self.background_color[i] / 255 for i in range(3)], 1.0)
        self.e['Input'].update()
        self.time = time.time()
        self.frames += 1
        self.runtime_ = self.time - self.start_time
        
        