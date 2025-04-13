import math, time
import pygame
import scripts.pygpen as pp
from scripts.cards import Card

class Enemy(pp.Element):
    def __init__(self, type, cards_db, hp):
        super().__init__(type)
        self.type = type
        self.hp = hp
        self.max_hp = hp
        self.cards = cards_db
        self.player_offset = 0
        self.center = [0, 0]
        self.defeated = False
        self.rect = pygame.Rect(0, 0, 32, 32)
        self.prompt_animation_speed = 2
        self.prompt_max_alpha = 100
        self.prompt_min_alpha = 30
        self.prompt_visible = True
        self.prompt_alpha = 0
        self.fade_start_time = time.time()
        self.fade_duration = 0.15
        self.prompt_x_offset = 20
        self.prompt_y_offset = 15
        self.dialogue_appear_done = False
    
    @property
    def img(self):
        return self.e['Assets'].images['enemy'][self.type]
    
    def use_card(self):
        return self.cards[0].spell.dmg
    
    def tkd(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            self.defeated = True
    
    def render(self):
        if self.defeated:
            return
        
        y_offset = math.sin(2 * self.e['Window'].time)/2 + self.player_offset
        current_time = time.time()
        
        dialogue = self.e['DialogueManager'].active
        if self.e['DialogueManager'].post_battle_mode:
            dialogue = False
            
        if not self.e['Game'].battle_manager.is_battling and not dialogue and self.e['Game'].player.action == 'idle':
            if self.player_offset < 7:
                self.player_offset += 0.08
            
            if self.type == 'main_boss':
                if not self.prompt_visible:
                    self.prompt_visible = True
                    self.fade_start_time = current_time
                    self.dialogue_appear_done = False
                
                text = self.e.elems['singletons']['Text']
                
                fade_progress = min(1.0, (current_time - self.fade_start_time) / self.fade_duration)
                if fade_progress < 0.5:
                    smoothed = 2 * fade_progress * fade_progress
                else:
                    smoothed = 1 - pow(-2 * fade_progress + 2, 2) / 2
                
                base_alpha = self.prompt_min_alpha + (self.prompt_max_alpha - self.prompt_min_alpha) * smoothed
                breathing_factor = 0.8 + 0.2 * math.sin(current_time * self.prompt_animation_speed)
                
                alpha_value = int(base_alpha * breathing_factor)
                alpha_value = max(0, min(255, alpha_value))
                
                self.prompt_alpha = alpha_value
                current_y_offset = int(self.prompt_y_offset * (1 - smoothed))
                
                prompt_text = "Press E to talk"
                prompt_size = text['small_font'].prep_text(prompt_text).size
                prompt_x = (340 - prompt_size[0]) // 2 + 5
                prompt_y = 145 + current_y_offset
                
                if fade_progress >= 1.0:
                    self.dialogue_appear_done = True
                
                text['small_font'].renderzb(
                    prompt_text, (prompt_x, prompt_y), line_width=0,
                    color=(150, 150, 150, alpha_value), bgcolor=(0,0,0,0),
                    group='ui'
                ) 
                
        elif self.e['Game'].player.action != 'idle':
            if self.player_offset > 0:
                self.player_offset -= 0.08
            
            if self.type == 'main_boss' and self.prompt_visible:
                self.prompt_visible = False
                self.fade_start_time = current_time
                self.dialogue_appear_done = False
            
            if self.type == 'main_boss' and self.prompt_alpha > 0:
                text = self.e.elems['singletons']['Text']
                
                fade_progress = min(1.0, (current_time - self.fade_start_time) / self.fade_duration)
                if fade_progress < 0.5:
                    smoothed = 2 * fade_progress * fade_progress
                else:
                    smoothed = 1 - pow(-2 * fade_progress + 2, 2) / 2
                
                alpha_value = int(self.prompt_max_alpha * (1.0 - smoothed))
                alpha_value = max(0, min(255, alpha_value))
                self.prompt_alpha = alpha_value
                current_y_offset = int(self.prompt_y_offset * smoothed)
                
                if alpha_value > 0:
                    prompt_text = "Press E to talk"
                    prompt_size = text['small_font'].prep_text(prompt_text).size
                    prompt_x = (340 - prompt_size[0]) // 2 + 5
                    prompt_y = 145 + current_y_offset
                    
                    text['small_font'].renderzb(
                        prompt_text, (prompt_x, prompt_y), line_width=0,
                        color=(150, 150, 150, alpha_value), bgcolor=(0,0,0,0),
                        group='ui'
                    )
        
        self.e['Renderer'].blit(self.img, (140, 80+y_offset), group='default')
        self.center = [170, 80+y_offset]
        self.rect.x = 140
        self.rect.y = 80+y_offset
        self.rect.width = self.img.get_width()
        self.rect.height = self.img.get_height()

main_boss = Enemy('main_boss', [Card('dark', 5), Card('dark', 5), Card('dark', 5)], 400)
mom_ghost = Enemy('mom_ghost', [Card('water', 1)], 40)
father_ghost = Enemy('father_ghost', [Card('water', 1)], 40)
