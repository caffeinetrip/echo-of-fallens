import pygame
import random
import math
from scripts.pygpen.vfx.sparks import Spark

class BattleVFX:
    def __init__(self, engine):
        self.e = engine
        self.sparks = []
        self.last_cleanup_time = 0
        
    def cleanup_old_sparks(self, current_time, force=False):
        if force or current_time - self.last_cleanup_time > 5.0:
            self.sparks = [s for s in self.sparks if hasattr(s, 'creation_time') and 
                          current_time - s.creation_time <= s.max_lifetime]
            self.last_cleanup_time = current_time
    
    def update_sparks(self, delta_time=0.016):
        current_time = pygame.time.get_ticks() / 1000

        for spark in self.sparks:
            if not hasattr(spark, 'creation_time'):
                spark.creation_time = current_time
                spark.max_lifetime = getattr(spark, 'max_lifetime', 2.0)

        self.sparks = [s for s in self.sparks if not s.update(delta_time) and 
                      current_time - s.creation_time <= s.max_lifetime]
        
        if random.random() < 0.03:
            self.generate_ambient_spark()
    
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
        
        self.sparks.append(Spark(
            pos=(x, y),
            angle=angle,
            size=(random.uniform(0.01, 0.015), random.uniform(0.01, 0.015)),
            speed=random.uniform(80, 180),
            decay=random.uniform(1, 1.9),
            color=spark_color,
            z=5
        ))
        
        if hasattr(self.e['Window'], 'fight'):
            self.e['Window'].fight = True
    
    def create_attack_effect(self, source_pos, target_pos, color, damage, is_player_attack=True):
        dx = target_pos[0] - source_pos[0]
        dy = target_pos[1] - source_pos[1]
        target_angle = math.atan2(dy, dx)
        
        num_sparks = min(10, 5 + damage // 2)
        for j in range(num_sparks):
            offset_angle = target_angle + random.uniform(-0.4, 0.4)
            offset_distance = random.uniform(5, 20)
            spark_pos = (
                source_pos[0] + math.cos(offset_angle) * offset_distance,
                source_pos[1] + math.sin(offset_angle) * offset_distance
            )
            
            self.sparks.append(Spark(
                pos=spark_pos,
                angle=target_angle + random.uniform(-0.2, 0.2),
                size=(random.uniform(2, 4), random.uniform(0.7, 1.5)),
                speed=random.uniform(150, 250),
                decay=random.uniform(0.4, 0.8),
                color=color,
                z=10
            ))
        
        for i in range(5):
            explosion_angle = random.uniform(0, math.pi * 2)
            self.sparks.append(Spark(
                pos=target_pos,
                angle=explosion_angle,
                size=(random.uniform(2, 5), random.uniform(0.7, 1.5)),
                speed=random.uniform(80, 180),
                decay=random.uniform(0.3, 0.5),
                color=color,
                z=10
            ))
    
    def get_attack_color(self, attack_type):
        if attack_type == "water":
            return (50, 100, 255)
        elif attack_type == "earth":
            return (50, 200, 50)
        elif attack_type == "fire":
            return (255, 50, 50)
        elif attack_type == "dark":
            return (150, 0, 255)
        else:
            return (255, 100, 50)
    
    def render(self):
        for spark in self.sparks:
            spark.renderz(group='ui')
    
    def clear_all_sparks(self):
        self.sparks = []