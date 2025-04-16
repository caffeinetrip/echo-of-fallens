import pygame, random, math
from engine.pygpen.vfx.sparks import Spark

class BattleVFX:
    def __init__(self, engine):
        self.e = engine
        self.sparks = []
        self.last_cleanup_time = 0
        
    def cleanup_old_sparks(self, current_time, force=False):
        if force or current_time - self.last_cleanup_time > 5.0:
            self._remove_expired_sparks(current_time)
            self.last_cleanup_time = current_time
    
    def _remove_expired_sparks(self, current_time):
        self.sparks = [s for s in self.sparks if hasattr(s, 'creation_time') and 
                      current_time - s.creation_time <= s.max_lifetime]
    
    def update_sparks(self, delta_time=0.016):
        current_time = pygame.time.get_ticks() / 1000

        self._initialize_spark_timers(current_time)
        self._update_active_sparks(current_time, delta_time)
        
        if random.random() < 0.03:
            self.generate_ambient_spark()
    
    def _initialize_spark_timers(self, current_time):
        for spark in self.sparks:
            if not hasattr(spark, 'creation_time'):
                spark.creation_time = current_time
                spark.max_lifetime = getattr(spark, 'max_lifetime', 2.0)
    
    def _update_active_sparks(self, current_time, delta_time):
        self.sparks = [s for s in self.sparks if not s.update(delta_time) and 
                      current_time - s.creation_time <= s.max_lifetime]
    
    def generate_ambient_spark(self):
        screen_width, screen_height = 320, 240
        
        side = random.randint(0, 3)
        
        if side == 0:  # Top
            x, y = random.uniform(0, screen_width), -5
            angle = random.uniform(math.pi/4, math.pi*3/4)
        elif side == 1:  # Right
            x, y = screen_width + 5, random.uniform(0, screen_height)
            angle = random.uniform(math.pi*3/4, math.pi*5/4)
        elif side == 2:  # Bottom
            x, y = random.uniform(0, screen_width), screen_height + 5
            angle = random.uniform(math.pi*5/4, math.pi*7/4)
        else:  # Left
            x, y = -5, random.uniform(0, screen_height)
            angle = random.uniform(math.pi*7/4, math.pi*9/4) % (math.pi*2)
        
        spark_color = (
            random.randint(200, 255),
            random.randint(200, 255),
            random.randint(200, 255)
        )
        
        self._create_spark(
            (x, y), 
            angle, 
            (random.uniform(0.01, 0.015), random.uniform(0.01, 0.015)),
            random.uniform(80, 180),
            random.uniform(1, 1.9),
            spark_color,
            5
        )
        
        if hasattr(self.e['Window'], 'fight'):
            self.e['Window'].fight = True
    
    def create_attack_effect(self, source_pos, target_pos, color, damage, is_player_attack=True):
        dx = target_pos[0] - source_pos[0]
        dy = target_pos[1] - source_pos[1]
        target_angle = math.atan2(dy, dx)
        
        self._create_source_sparks(source_pos, target_angle, color, damage)
        self._create_target_explosion(target_pos, color)
    
    def _create_source_sparks(self, source_pos, target_angle, color, damage):
        num_sparks = min(10, 5 + damage // 2)
        for _ in range(num_sparks):
            offset_angle = target_angle + random.uniform(-0.4, 0.4)
            offset_distance = random.uniform(5, 20)
            spark_pos = (
                source_pos[0] + math.cos(offset_angle) * offset_distance,
                source_pos[1] + math.sin(offset_angle) * offset_distance
            )
            
            self._create_spark(
                spark_pos,
                target_angle + random.uniform(-0.2, 0.2),
                (random.uniform(2, 4), random.uniform(0.7, 1.5)),
                random.uniform(150, 250),
                random.uniform(0.4, 0.8),
                color,
                10
            )
    
    def _create_target_explosion(self, target_pos, color):
        for _ in range(5):
            explosion_angle = random.uniform(0, math.pi * 2)
            self._create_spark(
                target_pos,
                explosion_angle,
                (random.uniform(2, 5), random.uniform(0.7, 1.5)),
                random.uniform(80, 180),
                random.uniform(0.3, 0.5),
                color,
                10
            )
    
    def _create_spark(self, pos, angle, size, speed, decay, color, z):
        self.sparks.append(Spark(
            pos=pos,
            angle=angle,
            size=size,
            speed=speed,
            decay=decay,
            color=color,
            z=z
        ))
    
    def get_attack_color(self, attack_type):
        colors = {
            "water": (50, 100, 255),
            "earth": (50, 200, 50),
            "fire": (255, 50, 50),
            "dark": (150, 0, 255)
        }
        return colors.get(attack_type, (255, 100, 50))
    
    def render(self):
        for spark in self.sparks:
            spark.renderz(group='ui')
    
    def clear_all_sparks(self):
        self.sparks = []