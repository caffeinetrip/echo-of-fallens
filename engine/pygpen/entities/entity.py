import pygame

from ..utils.elements import Element
from ..utils.game_math import normalize

OFFSET_N4 = [(1, 0), (0, 1), (-1, 0), (0, -1)]

class Entity(Element):
    def __init__(self, type, pos, z=0):
        super().__init__()
        self.type = type
        self.pos = list(pos)
        self.z = z
        self.config = self.e['EntityDB'][self.type].config
        self.assets = self.e['EntityDB'][self.type].assets
        self.animations = self.e['EntityDB'][self.type].animations
        self.action = self.config['default']
        self.source = 'animations' if self.action in self.animations else 'images'
        self.animation = None if self.source != 'animations' else self.animations[self.action].copy()
        self.size = self.config['size']
        
        # rendering options
        self.opacity = 255
        self.scale = [1, 1]
        self.rotation = 0
        self.flip = [False, False]
        self.visible = True
        
        # tracks if optimized rendering can be used
        self.tweaked = False

        self.outline = None
        
    @property
    def center(self):
        return self.rect.center
        
    @property
    def rect(self):
        return pygame.Rect(*self.pos, *self.size)
        
    @property
    def local_offset(self):
        img_offset = self.config[self.source][self.action]['offset']
        entity_offset = self.config['offset']
        return (img_offset[0] + entity_offset[0], img_offset[1] + entity_offset[1])
    
    @property
    def raw_img(self):
        if self.source == 'animations':
            return self.animation.img
        return self.assets[self.action]
    
    @property
    def img(self):
        raw_img = self.raw_img
        img = raw_img
        base_dimensions = img.get_size()
        if self.scale != [1, 1]:
            img = pygame.transform.scale(img, (int(self.scale[0] * base_dimensions[0]), int(self.scale[1] * base_dimensions[1])))
            self.tweaked = True
        if any(self.flip):
            img = pygame.transform.flip(img, self.flip[0], self.flip[1])
        if self.rotation:
            img = pygame.transform.rotate(img, self.rotation)
            self.tweaked = True
        if self.opacity != 255:
            if img == raw_img:
                img = img.copy()
            img.set_alpha(self.opacity)
        return img
    
    def set_action(self, action, force=False):
        if not force and (self.action == action):
            return
        self.action = action
        self.source = 'animations' if self.action in self.animations else 'images'
        if self.source == 'animations':
            self.animation = self.animations[self.action].copy()
    
    def topleft(self, offset=(0, 0)):
        img_size = self.img.get_size()
        if (not self.tweaked) or self.config['centered']:
            center_offset = (img_size[0] // 2, img_size[1] // 2) if self.config['centered'] else (0, 0)
            return (self.pos[0] - offset[0] + self.local_offset[0] - center_offset[0], self.pos[1] - offset[1] + self.local_offset[1] - center_offset[1])
        else:
            raw_img_size = self.raw_img.get_size()
            size_diff = (img_size[0] - raw_img_size[0], img_size[1] - raw_img_size[1])
            dynamic_offset = [-size_diff[0] // 2, -size_diff[1] // 2]
            return (self.pos[0] - offset[0] + self.local_offset[0] + dynamic_offset[0], self.pos[1] - offset[1] + self.local_offset[1] + dynamic_offset[1])
    
    def update(self, dt):
        if self.source == 'animations':
            self.animation.update(dt)
    
    def render(self, surf, offset=(0, 0)):
        if self.visible:
            surf.blit(self.img, self.topleft(offset))
    
    def renderz(self, offset=(0, 0), group='game'):
        if self.visible:
            self.e['Renderer'].blit(self.img, self.topleft(offset), z=self.z, group=group)

    def renderz(self, offset=(0, 0), group='game'):
        if self.visible:
            base_pos = self.topleft(offset)
            if self.outline:
                silhouette = pygame.mask.from_surface(self.img).to_surface(setcolor=self.outline, unsetcolor=(0, 0, 0, 0))
                silhouette.set_alpha(self.opacity)
                for offset in OFFSET_N4:
                    self.e['Renderer'].blit(silhouette, (base_pos[0] + offset[0], base_pos[1] + offset[1]), z=self.z - 0.000001, group=group)
            self.e['Renderer'].blit(self.img, base_pos, z=self.z, group=group)

class PhysicsEntity(Entity):
    def __init__(self, type, pos, z=0):
        super().__init__(type, pos, z=z)
        self.last_pos = (0, 0)
        self.velocity = [0, 0]
        self.acceleration = [0, 0]
        self.velocity_caps = [99999, 99999]
        self.velocity_normalization = [0, 0]
        self.next_movement = [0, 0]
        self.last_movement = (0, 0)
        self.bounce = 0
        self.autoflip = 0
        self.last_collisions = []
        self.collide_directions = {'up': False, 'down': False, 'right': False, 'left': False}
        self.dropthrough = 0
        self.off_colide = False
        self.setup()
        
    @property
    def bounce2d(self):
        if type(self.bounce) not in {list, tuple}:
            return (self.bounce, self.bounce)
        return tuple(self.bounce)
        
    def setup(self):
        pass
        
    def physics_processor(self, movement, tiles):
        rect = self.rect
        for tile in tiles:
            if rect.colliderect(tile.rect) and not self.off_colide:
                if tile.physics_type == 'solid':
                    if movement[0] > 0:
                        rect.right = tile.rect.left
                        self.velocity[0] *= -self.bounce2d[0]
                        self.collide_directions['right'] = True
                    if movement[0] < 0:
                        rect.left = tile.rect.right
                        self.velocity[0] *= -self.bounce2d[0]
                        self.collide_directions['left'] = True
                    if movement[1] > 0:
                        rect.bottom = tile.rect.top
                        self.velocity[1] *= -self.bounce2d[1]
                        self.collide_directions['down'] = True
                    if movement[1] < 0:
                        rect.top = tile.rect.bottom
                        self.velocity[1] *= -self.bounce2d[1]
                        self.collide_directions['up'] = True
                elif tile.physics_type == 'rampr':
                    if (movement[1] > 0) or (movement[0] > 0):
                        check_x = (rect.right - tile.rect.left) / tile.rect.width
                        if 0 <= check_x <= 1:
                            if rect.bottom > (1 - check_x) * tile.rect.height + tile.rect.top:
                                rect.bottom = (1 - check_x) * tile.rect.height + tile.rect.top
                                self.velocity[1] *= -self.bounce2d[1]
                                self.collide_directions['down'] = True
                elif tile.physics_type == 'rampl':
                    if (movement[1] > 0) or (movement[0] < 0):
                        check_x = (rect.left - tile.rect.left) / tile.rect.width
                        if 0 <= check_x <= 1:
                            if rect.bottom > check_x * tile.rect.height + tile.rect.top:
                                rect.bottom = check_x * tile.rect.height + tile.rect.top
                                self.velocity[1] *= -self.bounce2d[1]
                                self.collide_directions['down'] = True
                elif tile.physics_type == 'dropthrough':
                    if not self.dropthrough:
                        if (movement[1] > 0):
                            if (rect.bottom > tile.rect.top) and (rect.bottom - movement[1] <= tile.rect.top + 1):
                                rect.bottom = tile.rect.top
                                self.velocity[1] *= -self.bounce2d[1]
                                self.collide_directions['down'] = True
                    
                if rect.x != self.rect.x:
                    self.pos[0] = rect.x
                if rect.y != self.rect.y:
                    self.pos[1] = rect.y
                rect = self.rect
                self.last_collisions.append(tile)
                
    def custom_update(self):
        pass
                
    def physics_update(self, tilemap):
        dt = self.e['Window'].dt
        self.custom_update()
        if self.next_movement[0] * -self.autoflip > 0:
            self.flip[0] = True
        if self.next_movement[0] * self.autoflip > 0:
            self.flip[0] = False
        self.next_movement[0] += self.velocity[0] * dt
        self.next_movement[1] += self.velocity[1] * dt
        self.physics_move(self.next_movement, tilemap)
        self.last_movement = (self.next_movement[0] / dt, self.next_movement[1] / dt)
        self.velocity[0] += self.acceleration[0] * dt
        self.velocity[1] += self.acceleration[1] * dt
        self.velocity[0] = normalize(self.velocity[0], self.velocity_normalization[0] * dt)
        self.velocity[1] = normalize(self.velocity[1], self.velocity_normalization[1] * dt)
        self.velocity[0] = max(-self.velocity_caps[0], min(self.velocity_caps[0], self.velocity[0]))
        self.velocity[1] = max(-self.velocity_caps[1], min(self.velocity_caps[1], self.velocity[1]))
        self.next_movement = [0, 0]
        self.dropthrough = max(0, self.dropthrough - dt)
        
    def apply_force(self, vec):
        self.next_movement[0] += vec[0] * self.e['Window'].dt
        self.next_movement[1] += vec[1] * self.e['Window'].dt
    
    def physics_move(self, movement, tilemap):
        self.last_collisions = []
        self.last_pos = tuple(self.pos)
        self.collide_directions = {'up': False, 'down': False, 'right': False, 'left': False}
        self.pos[1] += movement[1]
        tiles = tilemap.nearby_grid_physics(self.center)
        self.physics_processor((0, movement[1]), tiles)
        self.pos[0] += movement[0]
        tiles = tilemap.nearby_grid_physics(self.center)
        self.physics_processor((movement[0], 0), tiles)