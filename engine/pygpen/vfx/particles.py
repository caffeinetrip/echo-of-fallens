from ..utils.elements import Element
from ..utils.gfx import palette_swap
from ..utils.game_math import normalize

PARTICLE_FUNCS = {'behave': {}, 'init': {}}
ANIMATION_CACHE = {}

def particle_init(argument):
    def decorator(func):
        PARTICLE_FUNCS['init'][argument] = func
        return func
    return decorator

def particle_behavior(argument):
    def decorator(func):
        PARTICLE_FUNCS['behave'][argument] = func
        return func
    return decorator

@particle_init('idle')
def idle_init(self):
    pass

@particle_behavior('idle')
def idle_behave(self, dt):
    pass

@particle_init('physics_example')
def physics_ex_init(self):
    self.acceleration[1] = 600
    self.velocity_caps[1] = 300
    self.velocity_normalization[0] = 50
    
@particle_behavior('physics_example')
def physics_ex_behave(self, dt):
    pass

class Particle(Element):
    def __init__(self, pos, particle_type, velocity=(0, 0), decay_rate=1.0, advance=0.0, behavior='idle', colors=None, z=0, physics_source=None):
        super().__init__()
        self.type = particle_type
        self.behavior = behavior
        self.pos = list(pos)
        self.velocity = list(velocity)
        self.acceleration = [0, 0]
        self.velocity_caps = [99999, 99999]
        self.velocity_normalization = [0, 0]
        self.next_movement = [0, 0]
        self.bounce = 0.5
        self.decay_rate = decay_rate
        self.advance = advance
        self.physics_source = physics_source
        self.z = z
        self.animation = self.e['EntityDB'][self.type].animations[self.type].copy()
        self.animation.config['loop'] = False
        self.colors = colors
        if colors:
            colors_id = (self.type, tuple((tuple(k), tuple(v)) for k, v in colors.items()))
            if colors_id in ANIMATION_CACHE:
                self.animation = ANIMATION_CACHE[colors_id].copy()
            else:
                self.animation = self.animation.hard_copy()
                self.animation.palette_swap(colors)
                ANIMATION_CACHE[colors_id] = self.animation
        self.animation.update(advance)
        PARTICLE_FUNCS['init'][behavior](self)
    
    def update(self, dt=None):
        if not dt:
            dt = self.e['Window'].dt
        self.animation.update(dt * self.decay_rate)
        
        PARTICLE_FUNCS['behave'][self.behavior](self, dt)
        
        self.next_movement[0] += self.velocity[0] * dt
        self.next_movement[1] += self.velocity[1] * dt
        
        # handle movement and tile physics
        self.pos[0] += self.next_movement[0]
        if self.physics_source:
            collision = self.physics_source.physics_gridtile(self.pos)
            if collision and (collision.physics_type == 'solid'):
                self.velocity[0] *= -self.bounce
                if self.next_movement[0] > 0:
                    self.pos[0] = collision.rect.left
                if self.next_movement[0] < 0:
                    self.pos[0] = collision.rect.right
        self.pos[1] += self.next_movement[1]
        if self.physics_source:
            collision = self.physics_source.physics_gridtile(self.pos)
            if collision and (collision.physics_type == 'solid'):
                self.velocity[1] *= -self.bounce
                if self.next_movement[1] > 0:
                    self.pos[1] = collision.rect.top
                if self.next_movement[1] < 0:
                    self.pos[1] = collision.rect.bottom
        
        self.velocity[0] += self.acceleration[0] * dt
        self.velocity[1] += self.acceleration[1] * dt
        self.velocity[0] = normalize(self.velocity[0], self.velocity_normalization[0] * dt)
        self.velocity[1] = normalize(self.velocity[1], self.velocity_normalization[1] * dt)
        self.velocity[0] = max(-self.velocity_caps[0], min(self.velocity_caps[0], self.velocity[0]))
        self.velocity[1] = max(-self.velocity_caps[1], min(self.velocity_caps[1], self.velocity[1]))
        self.next_movement = [0, 0]
        return self.animation.finished
    
    def render(self, surf, offset=(0, 0)):
        img = self.animation.img
        surf.blit(img, (self.pos[0] - offset[0] - img.get_width() // 2, self.pos[1] - offset[1] - img.get_height() // 2))
    
    def renderz(self, group='default', offset=(0, 0)):
        img = self.animation.img
        self.e['Renderer'].blit(img, (self.pos[0] - offset[0] - img.get_width() // 2, self.pos[1] - offset[1] - img.get_height() // 2), z=self.z, group=group)