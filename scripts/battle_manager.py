import pygame
import random
import math, time
import scripts.pygpen as pp
from scripts.pygpen.vfx.sparks import Spark

class BattleManager(pp.ElementSingleton):
    def __init__(self, custom_id=None):
        super().__init__(custom_id)
        self.is_battling = False
        self.current_enemy = None
        self.turn = 'player'
        self.selected_card_index = 0
        self.battle_message = ""
        self.message_timer = 0
        self.tremor_value = 0
        self.tremor_decay = 1
        self.sparks = []
        self.game_over = False
        self.game_over_timer = 0
        self.last_cleanup_time = 0
        self.player_die = False
        self.e_player_health = None
        self.end_game = False
        
    def start_battle(self, enemy):
        self.is_battling = True
        self.current_enemy = enemy
        self.turn = 'player'
        self.battle_message = "Battle started! Select a card."
        self.message_timer = 5
        self.selected_card_index = 0
        self.set_tremor(0.5)
        self.game_over = False
        self.game_over_timer = 0
        
    def end_battle(self):
        self.is_battling = False
        self.battle_message = ""
        
        if hasattr(self.e['Game'].player, 'moves'):
            self.e['Game'].player.moves = [0, 0, 0, 0]
            if self.current_enemy.type == 'main_boss' and not self.player_die:
                self.end_game = True
                
        if self.current_enemy and self.current_enemy.hp <= 0:
            enemy_type = self.current_enemy.type
            pygame.time.set_timer(pygame.USEREVENT, 2000)

            self.e['Sounds'].play('death', volume=0.05)
            self.e['Game'].on_battle_end(enemy_type)
        
        if self.player_die and self.e['Game'].player.hp <=10:
            pygame.time.set_timer(pygame.USEREVENT, 25000)
            self.e['Game'].on_battle_end('author')
        
        for spark in self.sparks:
            if not hasattr(spark, 'max_lifetime'):
                spark.max_lifetime = 2.0 
        
    def set_tremor(self, value):
        self.tremor_value = value
        self.e["Window"].tremor = value
        
        if self.game_over and value > 0:
            self.tremor_decay = 3.0  
        
    def update(self):
        if hasattr(self.e['Game'], 'dialogue_manager') and self.e['Game'].dialogue_manager.active:
            return
            
        current_time = pygame.time.get_ticks() / 1000
        
        if current_time - self.last_cleanup_time > 5.0: 
            if not self.is_battling and not self.game_over:
                self.sparks = [] 
            self.last_cleanup_time = current_time
            
        if self.tremor_value > 0:
            self.tremor_value = max(0, self.tremor_value - self.tremor_decay * 0.016)
            self.e["Window"].tremor = self.tremor_value
        
        if self.game_over:
            self.game_over_timer -= 0.016
            if self.game_over_timer <= 0:
                self.game_over = False
                self.set_tremor(0)
                self.sparks = []
                return
        
        if not self.is_battling:
            return
            
        if self.message_timer > 0:
            self.message_timer -= 0.016
            
        elif self.turn == 'player':
            self.handle_player_turn()
        elif self.turn == 'enemy':
            self.handle_enemy_turn()
            
        self.check_battle_end()
        
        current_time = pygame.time.get_ticks() / 1000
        for i in range(len(self.sparks)-1, -1, -1):
            spark = self.sparks[i]
            
            if not hasattr(spark, 'creation_time'):
                spark.creation_time = current_time
                spark.max_lifetime = 2.0 
                
            if spark.update(0.016) or (current_time - spark.creation_time > spark.max_lifetime):
                del self.sparks[i]
                
        if random.random() < 0.03 and self.is_battling:
            screen_width = 320
            screen_height = 240
            
            side = random.randint(0, 3)
            
            if side == 0: 
                x = random.uniform(0, screen_width)
                y = -5
                angle = random.uniform(math.pi/4, math.pi*3/4)
            elif side == 1: 
                x = screen_width + 5
                y = random.uniform(0, screen_height)
                angle = random.uniform(math.pi*3/4, math.pi*5/4)
            elif side == 2:  
                x = random.uniform(0, screen_width)
                y = screen_height + 5
                angle = random.uniform(math.pi*5/4, math.pi*7/4)
            else: 
                x = -5
                y = random.uniform(0, screen_height)
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
        
    def handle_player_turn(self):
        deck = self.e['Game'].deck
        
        if len(deck.cards) == 0:
            self.battle_message = "No spells available!"
            self.turn = 'enemy'
            return
            
        if self.e['Input'].pressed('left'):
            self.selected_card_index = max(0, self.selected_card_index - 1)
            self.e['Sounds'].play('action', volume=0.2)
            
        if self.e['Input'].pressed('right'):
            self.selected_card_index = min(len(deck.cards) - 1, self.selected_card_index + 1)
            self.e['Sounds'].play('action', volume=0.2)
            
        if self.e['Input'].pressed('action'):
            if self.selected_card_index < len(deck.cards):
                selected_card = deck.cards[self.selected_card_index]
                amplifier = 1
                if len(deck.cards) == 3:
                    amplifier = 5
                damage = selected_card.spell.dmg * amplifier
                self.message_timer = 5
                self.current_enemy.tkd(damage)
                
                self.e['Sounds'].play('damage', volume=0.5)
                
                tremor_intensity = min(1, 0.2 + (damage / 20))
                self.set_tremor(tremor_intensity)
                
                enemy_pos = self.current_enemy.center
                
                spark_color = (255, 100, 50) 
                if hasattr(selected_card, 'type'):
                    card_type = selected_card.type.lower()
                else:
                    card_type = selected_card.spell.type.lower()
                    
                if card_type == "water":
                    spark_color = (50, 100, 255)
                elif card_type == "earth":
                    spark_color = (50, 200, 50)
                elif card_type == "fire":
                    spark_color = (255, 50, 50)
                
                player_pos = self.e['Game'].player.rect.center if hasattr(self.e['Game'].player, 'rect') else (150, 150)
                dx = enemy_pos[0] - player_pos[0]
                dy = enemy_pos[1] - player_pos[1]
                target_angle = math.atan2(dy, dx)
                
                num_sparks = min(10, 5 + damage // 2)
                for j in range(num_sparks):
                    offset_angle = target_angle + random.uniform(-0.4, 0.4)
                    offset_distance = random.uniform(5, 20)
                    spark_pos = (
                        player_pos[0] + math.cos(offset_angle) * offset_distance,
                        player_pos[1] + math.sin(offset_angle) * offset_distance
                    )
                    
                    self.sparks.append(Spark(
                        pos=spark_pos,
                        angle=target_angle + random.uniform(-0.2, 0.2),
                        size=(random.uniform(2, 4), random.uniform(0.7, 1.5)),
                        speed=random.uniform(150, 250),
                        decay=random.uniform(0.4, 0.8),
                        color=spark_color,
                        z=10
                    ))
                

                for i in range(5):
                    explosion_angle = random.uniform(0, math.pi * 2)
                    self.sparks.append(Spark(
                        pos=enemy_pos,
                        angle=explosion_angle,
                        size=(random.uniform(2, 5), random.uniform(0.7, 1.5)),
                        speed=random.uniform(80, 180),
                        decay=random.uniform(0.3, 0.5),
                        color=spark_color,
                        z=10
                    ))
                
                card_type = selected_card.type if hasattr(selected_card, 'type') else selected_card.spell.type
                self.battle_message = f"Player used {card_type}! Dealt {damage} damage."
                self.turn = 'enemy'
    
    def handle_enemy_turn(self):
        enemy = self.current_enemy
        player = self.e['Game'].player
        damage = enemy.use_card()
        if enemy.type == 'main_boss' and len(self.e['Game'].deck.cards) == 3 and self.e_player_health == None:
            self.e_player_health = player.hp
        if self.e_player_health != None:
            damage = int((self.e_player_health//4)+5)
        
        if hasattr(player, 'tkd'):
            player.tkd(damage)
        else:
            player.take_damage(damage)
            self.e['Sounds'].play('damage', volume=0.5)
        
        tremor_intensity = min(1.5, 0.3 + (damage / 15))
        self.set_tremor(tremor_intensity)
        
        player_pos = player.center if hasattr(player, 'center') else player.rect.center if hasattr(player, 'rect') else (150, 150)
        
        attack_type = enemy.cards[0].type if hasattr(enemy.cards[0], 'type') else enemy.cards[0].spell.type
        spark_color = (200, 100, 100)
        if attack_type == "water":
            spark_color = (50, 100, 255)
        elif attack_type == "earth":
            spark_color = (50, 200, 50)
        elif attack_type == "fire":
            spark_color = (255, 50, 50)
        elif attack_type == "dark":
            spark_color = (150, 0, 255)
            
        enemy_pos = enemy.rect.center if hasattr(enemy, 'rect') else enemy.center if hasattr(enemy, 'center') else (200, 100)
        dx = player_pos[0] - enemy_pos[0]
        dy = player_pos[1] - enemy_pos[1]
        target_angle = math.atan2(dy, dx)

        num_sparks = min(10, 5 + damage // 2)
        for j in range(num_sparks):
            offset_angle = target_angle + random.uniform(-0.4, 0.4)
            offset_distance = random.uniform(5, 20)
            spark_pos = (
                enemy_pos[0] + math.cos(offset_angle) * offset_distance,
                enemy_pos[1] + math.sin(offset_angle) * offset_distance
            )
            
            self.sparks.append(Spark(
                pos=spark_pos,
                angle=target_angle + random.uniform(-0.2, 0.2),
                size=(random.uniform(2, 4), random.uniform(0.7, 1.5)),
                speed=random.uniform(150, 250),
                decay=random.uniform(0.4, 0.8),
                color=spark_color,
                z=10
            ))
        
        for i in range(5):
            explosion_angle = random.uniform(0, math.pi * 2)
            self.sparks.append(Spark(
                pos=player_pos,
                angle=explosion_angle,
                size=(random.uniform(2, 5), random.uniform(0.7, 1.5)),
                speed=random.uniform(80, 180),
                decay=random.uniform(0.3, 0.5),
                color=spark_color,
                z=10
            ))
        
        self.battle_message = f"Enemy attacks! Player takes {damage} damage."
        self.message_timer = 5
        self.turn = 'player'
    
    def check_battle_end(self):
        if self.current_enemy and self.current_enemy.hp <= 0:
            if hasattr(self.e['Window'], 'fight'):
                self.e['Window'].fight = False
                
            self.battle_message = "Victory! Enemy defeated."
            self.message_timer = 15
            current_room = self.e['Game'].room_manager.current_room_id
            self.e['Game'].room_manager.rooms[current_room].enemy = None
            
            self.set_tremor(0.6)
            
            enemy_pos = self.current_enemy.rect.center if hasattr(self.current_enemy, 'rect') else (
                self.current_enemy.center if hasattr(self.current_enemy, 'center') else (200, 100)
            )

            self.e['Sounds'].play('death', volume=0.05)
            
            for i in range(5):
                explosion_angle = random.uniform(0, math.pi * 2)
                
                for j in range(5):
                    angle_offset = explosion_angle + (j * (2 * math.pi / 5))
                    for k in range(3):
                        dist = random.uniform(5, 25) * (k + 1)
                        spark_pos = (
                            enemy_pos[0] + math.cos(angle_offset) * dist,
                            enemy_pos[1] + math.sin(angle_offset) * dist
                        )
                        
                        self.sparks.append(Spark(
                            pos=spark_pos,
                            angle=angle_offset,
                            size=(random.uniform(2, 5), random.uniform(0.7, 1.5)),
                            speed=random.uniform(100, 200),
                            decay=random.uniform(0.3, 0.5),
                            color=(255, 150, 50),
                            z=10
                        ))
            
            for i in range(10):
                explosion_angle = random.uniform(0, math.pi * 2)
                self.sparks.append(Spark(
                    pos=enemy_pos,
                    angle=explosion_angle,
                    size=(random.uniform(3, 6), random.uniform(1, 2)),
                    speed=random.uniform(60, 120),
                    decay=random.uniform(0.2, 0.4),
                    color=(255, 200, 50),
                    z=10
                ))
            
            self.sparks = []
            self.game_over_timer = 0.4
            self.e['Window'].e_start_transition()
            self.end_battle()
            
        if self.e['Game'].player.hp <= 0:
            if hasattr(self.e['Window'], 'fight'):
                self.e['Window'].fight = False
                
            self.battle_message = "Defeat! Player lost."
            self.message_timer = 5
           
            self.set_tremor(0.7)
            
            self.e['Sounds'].play('death', volume=0.05)
            
            player_pos = self.e['Game'].player.rect.center if hasattr(self.e['Game'].player, 'rect') else (150, 150)
            
            for i in range(5):
                explosion_angle = random.uniform(0, math.pi * 2)
                
                for j in range(5):
                    angle_offset = explosion_angle + (j * (2 * math.pi / 5))
                    for k in range(3):
                        dist = random.uniform(5, 25) * (k + 1)
                        spark_pos = (
                            player_pos[0] + math.cos(angle_offset) * dist,
                            player_pos[1] + math.sin(angle_offset) * dist
                        )
                        
                        self.sparks.append(Spark(
                            pos=spark_pos,
                            angle=angle_offset,
                            size=(random.uniform(1, 3), random.uniform(0.5, 1)),
                            speed=random.uniform(100, 200),
                            decay=random.uniform(0.4, 0.6),
                            color=(200, 200, 255),
                            z=10
                        ))

            for i in range(10):
                explosion_angle = random.uniform(0, math.pi * 2)
                self.sparks.append(Spark(
                    pos=player_pos,
                    angle=explosion_angle,
                    size=(random.uniform(1, 3), random.uniform(0.5, 1)),
                    speed=random.uniform(60, 120),
                    decay=random.uniform(0.4, 0.6),
                    color=(255, 255, 255),
                    z=10
                ))
            
            self.sparks = []
            self.game_over = True
            self.game_over_timer = 0.4
            self.player_die = True

            self.end_battle()
    
    # RENDER UI
    def render(self):
        if not self.is_battling and not self.game_over and len(self.sparks) == 0:
            return
        
        if self.game_over:
            if self.player_die and self.e['Game'].player.hp < 40:
                self.e['Window'].e_start_transition()
                if hasattr(self.e['EntityGroups'], 'groups'):
                    self.e['EntityGroups'].groups = {}
                self.e['Game'].reset()
            elif self.current_enemy and self.current_enemy.type == 'main_boss':
                self.end_game = True
            
            self.e['Window'].e_start_transition()
            self.game_over = False
                
        if self.is_battling:
            screen_width = 320
            screen_height = 240
            
            left_rect = pygame.Surface((25, screen_height), pygame.SRCALPHA)
            right_rect = pygame.Surface((25, screen_height), pygame.SRCALPHA)
            top_rect = pygame.Surface((screen_width, 25), pygame.SRCALPHA)
            bottom_rect = pygame.Surface((screen_width, 25), pygame.SRCALPHA)
            
            corner_radius = 12
            rect_color = (0, 0, 0, 180)
            
            pygame.draw.rect(left_rect, rect_color, (0, 0, 25, screen_height), border_radius=corner_radius)
            pygame.draw.rect(right_rect, rect_color, (0, 0, 25, screen_height), border_radius=corner_radius)
            pygame.draw.rect(top_rect, rect_color, (0, 0, screen_width, 25), border_radius=corner_radius)
            pygame.draw.rect(bottom_rect, rect_color, (0, 0, screen_width, 25), border_radius=corner_radius)
            
            self.e['Renderer'].blit(left_rect, (0, 0), group='ui')
            self.e['Renderer'].blit(right_rect, (screen_width - 25, 0), group='ui')
            self.e['Renderer'].blit(top_rect, (0, 0), group='ui')
            self.e['Renderer'].blit(bottom_rect, (0, screen_height - 25), group='ui')
            
        deck = self.e['Game'].deck
        
        if self.battle_message and (self.message_timer > 0 or self.game_over):
            self.e['Text']['small_font'].renderzb(self.battle_message, (160, 20), 
                                            line_width=0, color=(255, 255, 255),
                                            bgcolor=(40, 35, 40), group='ui')
                                            
        if self.is_battling:
            turn_text = f"Turn: {self.turn.capitalize()}"
            self.e['Text']['small_font'].renderzb(turn_text, (20, 30), line_width=0,
                                              color=(255, 255, 255), bgcolor=(40, 35, 40),
                                              group='ui')
            
            turn_text = f"Enemy: {self.current_enemy.hp}/{self.current_enemy.max_hp}"
            self.e['Text']['small_font'].renderzb(turn_text, (20, 65), line_width=0,
                                              color=(200, 152, 152), bgcolor=(40, 35, 40),
                                              group='ui')

            turn_text = f"You: {self.e['Game'].player.hp}/{self.e['Game'].player.max_hp}"
            self.e['Text']['small_font'].renderzb(turn_text, (20, 50), line_width=0,
                                              color=(200, 152, 152), bgcolor=(40, 35, 40),
                                              group='ui')
                  
            if self.turn == 'player' and len(deck.cards) > 0:
                for i, card in enumerate(deck.cards):
                    highlight = (i == self.selected_card_index)
                    color = (255, 255, 100) if highlight else (200, 200, 200)
                    card_type = card.type if hasattr(card, 'type') else card.spell.type
                    self.e['Text']['small_font'].renderzb(f"{card_type}", (130 + i * 40, 185), 
                                                    line_width=0, color=color, 
                                                    bgcolor=(40, 35, 40), group='ui')
        
        for spark in self.sparks:
            spark.renderz(group='ui')