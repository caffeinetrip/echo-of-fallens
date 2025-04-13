from ..utils.gfx import palette_swap

class Animation:
    def __init__(self, images, config=None, hard_copy=False):
        if not config:
            config = {}
        if 'speed' not in config:
            config['speed'] = 1
        if 'loop' not in config:
            config['loop'] = True
        if 'paused' not in config:
            config['paused'] = False
        if 'frames' not in config:
            config['frames'] = [0.1 for i in range(len(images))]
        self.config = config
        
        self.images = images
        if hard_copy:
            self.images = [img.copy() for img in self.images]
            
        self.frame = 0
        self.frame_time = 0
        self.paused = config['paused']
        self.finished = False
        
    def palette_swap(self, colors):
        for i in range(len(self.images)):
            self.images[i] = palette_swap(self.images[i], colors)
    
    def copy(self):
        return Animation(self.images, config=self.config)
    
    def hard_copy(self):
        return Animation(self.images, config=self.config, hard_copy=True)
    
    @property
    def img(self):
        return self.images[max(min(len(self.images) - 1, self.frame), 0)]
    
    @property
    def frames(self):
        return len(self.images)

    def pause(self):
        self.paused = True
    
    def unpause(self):
        self.paused = False

    def update(self, dt):
        if not self.paused:
            self.frame_time += dt * self.config['speed']
            while self.frame_time >= self.config['frames'][max(min(len(self.images) - 1, self.frame), 0)]:
                # ignore update if end is reached and looping is disabled
                if (self.frame >= len(self.images) - 1) and (not self.config['loop']):
                    self.finished = True
                    return
            
                frame_dur = self.config['frames'][max(min(len(self.images) - 1, self.frame), 0)]
                self.frame_time -= frame_dur
                self.frame = (self.frame + 1) % len(self.images)
                
        