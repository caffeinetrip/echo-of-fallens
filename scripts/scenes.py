import pygame
import math
import time
import scripts.pygpen as pp

class PrologueScene:
    def __init__(self, game):
        self.game = game
        self.text = "He was from a family of miners. One day his family didn't return from the mine. And while waiting for his parents he accidentally fell..."
        self.title_text = "Made for Ludum Dare 57\nby soma"
        self.current_text = ""
        self.current_title = ""
        self.text_index = 0
        self.title_index = 0
        self.last_char_time = 0
        self.last_title_char_time = 0
        self.char_delay = 0.05
        self.title_char_delay = 0.08
        self.completed = False
        self.waiting_for_input = False
        self.wait_start_time = 0
        self.fade_alpha = 255
        self.title_fade_alpha = 0
        self.title_fade_start = 0
        self.title_fade_duration = 1.5
        self.title_y_offset = 20
        self.title_visible = False
        self.prologue_img = None
        self.img_alpha = 0
        self.img_fade_speed = 1.5
        self.narrator_sound_timer = 0
        
        try:
            self.prologue_img = self.game.e['Assets'].images.get('prologue', None)
            if not self.prologue_img:
                self.prologue_img = pygame.image.load('data/images/prologue.png').convert_alpha()
        except:
            print("Could not load prologue image")
            
    def update(self):
        current_time = time.time()
        
        if self.game.e.elems['singletons']['Input'].pressed('action'):
            self.completed = True
            self.game.scene = 'game'
            self.game.e.elems['singletons']['Window'].start_transition()
            self.game.e['Sounds'].play('action', volume=0.4)
            self.game.e['Sounds'].play_music('default', volume=0.4)
            return
            
        if not self.completed:
            if self.img_alpha < 255:
                self.img_alpha = min(255, self.img_alpha + self.img_fade_speed)
                
            if self.text_index < len(self.text):
                if current_time - self.last_char_time > self.char_delay:
                    self.current_text += self.text[self.text_index]
                    self.text_index += 1
                    self.last_char_time = current_time
                    if self.text_index <= len(self.text)-1 and self.text[self.text_index] != ' ':
                        self.game.e['Sounds'].play('author_talk', volume=0.1)

            else:
                if not self.title_visible:
                    self.title_visible = True
                    self.title_fade_start = current_time
                    
                if not self.waiting_for_input:
                    self.waiting_for_input = True
                    self.wait_start_time = current_time
                    
                if self.title_index < len(self.title_text):
                    if current_time - self.last_title_char_time > self.title_char_delay:
                        self.current_title += self.title_text[self.title_index]
                        self.title_index += 1
                        self.last_title_char_time = current_time
                        
                if current_time - self.wait_start_time > 1.0:
                    if self.game.e.elems['singletons']['Input'].pressed('action'):
                        self.completed = True
                        self.game.scene = 'game'
                        self.game.e.elems['singletons']['Window'].start_transition()
                        
                        self.game.e['Sounds'].play_music('default', volume=0.4)
                        
            if self.title_visible:
                progress = min(1.0, (current_time - self.title_fade_start) / self.title_fade_duration)
                if progress < 0.5:
                    smoothed = 2 * progress * progress
                else:
                    smoothed = 1 - pow(-2 * progress + 2, 2) / 2
                    
                self.title_fade_alpha = int(255 * smoothed)
                self.title_y_offset = int(20 * (1 - smoothed))
                
    def render(self):
        self.game.display.fill((10, 10, 10))
   
        if self.prologue_img:
            img_copy = self.prologue_img.copy()
         
            if self.img_alpha < 255:
                img_copy.set_alpha(self.img_alpha)
 
            img_x = (340 - self.prologue_img.get_width()) // 2
            img_y = 30
            self.game.e['Renderer'].blit(img_copy, (img_x, img_y), group='default')
        
        text_prep = self.game.e['Text']['small_font'].prep_text(self.current_text, 300)
        text_width = text_prep.size[0]
        text_x = (340 - text_width) // 2
        text_y = 175 if self.prologue_img else 80
        
        self.game.e['Text']['small_font'].renderzb(
            self.current_text, (text_x, text_y), line_width=300,
            color=(255, 255, 255), bgcolor=(0,0,0,0),
            group='ui'
        )
        
        if self.title_visible and self.current_title:
            title_lines = self.current_title.split('\n')
            for i, line in enumerate(title_lines):
                title_prep = self.game.e['Text']['small_font'].prep_text(line)
                title_x = (340 - title_prep.size[0]) // 2
                title_y = 230 + i * 15 - self.title_y_offset
                
                self.game.e['Text']['small_font'].renderzb(
                    line, (title_x, title_y), line_width=0,
                    color=(200, 200, 200, self.title_fade_alpha), bgcolor=(0,0,0,0),
                    group='ui'
                )
    
        if self.text_index >= len(self.text) and time.time() - self.wait_start_time > 1.0:
            if math.sin(time.time() * 4) > 0:
                prompt_text = "Press E to continue"
                prompt_size = self.game.e['Text']['small_font'].prep_text(prompt_text).size
                prompt_x = (340 - prompt_size[0]) // 2
                prompt_y = 200 if self.prologue_img else 140
                
                self.game.e['Text']['small_font'].renderzb(
                    prompt_text, (prompt_x, prompt_y), line_width=0,
                    color=(152,152,152), bgcolor=(0,0,0,0),
                    group='ui'
                )
                
                
class GameOverScene:
    def __init__(self, game, win=False):
        self.game = game
        self.win = win
        self.text = "Game Over" if not win else "You Win!"
        self.display_time = time.time()
        self.fade_alpha = 0
        self.fade_in_speed = 2
        self.restart_prompt_visible = False

        if win:
            self.game.e['Sounds'].play_music('end_game', volume=0.5)
        else:
            self.game.e['Sounds'].play('death', volume=0.6)
        
    def update(self):
        current_time = time.time()
        time_elapsed = current_time - self.display_time
        if time_elapsed < 2.0:
            self.fade_alpha = min(255, self.fade_alpha + self.fade_in_speed)

        if time_elapsed > 2.0 and self.game.e['Input'].pressed('action'):
            self.game.e['Sounds'].play('action', volume=0.4)
            self.game.reset()
            self.game.scene = 'game'
            self.game.e['Window'].start_transition()
            
    def render(self):
        self.game.display.fill((0, 0, 0))
        text_color = (255, 220, 100) if self.win else (255, 100, 100)
        text_prep = self.game.e['Text']['small_font'].prep_text(self.text)
        text_x = (340 - text_prep.size[0]) // 2
        
        self.game.e['Text']['small_font'].renderzb(
            self.text, (text_x, 80), line_width=0,
            color=(text_color[0], text_color[1], text_color[2], self.fade_alpha),
            bgcolor=(0,0,0,0),
            group='ui'
        )

        if time.time() - self.display_time > 2.0:
            if math.sin(time.time() * 4) > 0:
                prompt_text = "Press E to restart"
                prompt_size = self.game.e['Text']['small_font'].prep_text(prompt_text).size
                prompt_x = (340 - prompt_size[0]) // 2
                prompt_y = 140
                
                self.game.e['Text']['small_font'].renderzb(
                    prompt_text, (prompt_x, prompt_y), line_width=0,
                    color=(152, 152, 152, self.fade_alpha),
                    bgcolor=(0,0,0,0),
                    group='ui'
                )