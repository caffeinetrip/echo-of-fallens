import math
import time
import pygame
import scripts.pygpen as pp

class PrologueScene(pp.ElementSingleton):
    def __init__(self, custom_id=None):
        super().__init__(custom_id)
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
        
        self._load_prologue_image()
    
    def _load_prologue_image(self):
        self.prologue_img = self.e['Assets'].images.get('prologue', None)
        if not self.prologue_img:
            self.prologue_img = pygame.image.load('data/images/prologue.png').convert_alpha()

    def update(self):
        current_time = time.time()
        
        if self.e['Input'].pressed('action'):
            self._handle_action_input()
            return
            
        if not self.completed:
            self._update_prologue_intro(current_time)
    
    def _handle_action_input(self):
        self.completed = True
        self.e['GameStateSystem'].scene = 'game'
        self.e['Window'].start_transition()
        self.e['Sounds'].play('action', volume=0.4)
        self.e['Sounds'].play_music('default', volume=0.4)
    
    def _update_prologue_intro(self, current_time):
        self._update_image_fade()
        
        if self.text_index < len(self.text):
            self._update_text_reveal(current_time)
        else:
            self._update_title_reveal(current_time)
    
    def _update_image_fade(self):
        if self.img_alpha < 255:
            self.img_alpha = min(255, self.img_alpha + self.img_fade_speed)
    
    def _update_text_reveal(self, current_time):
        if current_time - self.last_char_time > self.char_delay:
            self.current_text += self.text[self.text_index]
            self.text_index += 1
            self.last_char_time = current_time
            
            if self.text_index <= len(self.text)-1 and self.text[self.text_index] != ' ':
                self.e['Sounds'].play('author_talk', volume=0.1)
    
    def _update_title_reveal(self, current_time):
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
            if self.e['Input'].pressed('action'):
                self.completed = True
                self.scene = 'game'
                self.e['Window'].start_transition()
                self.e['Sounds'].play_music('default', volume=0.4)
                
        if self.title_visible:
            self._update_title_fade_effect(current_time)
    
    def _update_title_fade_effect(self, current_time):
        progress = min(1.0, (current_time - self.title_fade_start) / self.title_fade_duration)
        if progress < 0.5:
            smoothed = 2 * progress * progress
        else:
            smoothed = 1 - pow(-2 * progress + 2, 2) / 2
            
        self.title_fade_alpha = int(255 * smoothed)
        self.title_y_offset = int(20 * (1 - smoothed))
    
    def render(self):
        self.e['Game'].display.fill((10, 10, 10))
        self._render_prologue_image()
        self._render_prologue_text()
        self._render_title()
        self._render_continue_prompt()
    
    def _render_prologue_image(self):
        if self.prologue_img:
            img_copy = self.prologue_img.copy()
         
            if self.img_alpha < 255:
                img_copy.set_alpha(self.img_alpha)
 
            img_x = (340 - self.prologue_img.get_width()) // 2
            img_y = 30
            self.e['Renderer'].blit(img_copy, (img_x, img_y), group='default')
    
    def _render_prologue_text(self):
        text_prep = self.e['Text']['small_font'].prep_text(self.current_text, 300)
        text_width = text_prep.size[0]
        text_x = (340 - text_width) // 2
        text_y = 175 if self.prologue_img else 80
        
        self.e['Text']['small_font'].renderzb(
            self.current_text, (text_x, text_y), line_width=300,
            color=(255, 255, 255), bgcolor=(0,0,0,0),
            group='ui'
        )
    
    def _render_title(self):
        if self.title_visible and self.current_title:
            title_lines = self.current_title.split('\n')
            for i, line in enumerate(title_lines):
                title_prep = self.e['Text']['small_font'].prep_text(line)
                title_x = (340 - title_prep.size[0]) // 2
                title_y = 230 + i * 15 - self.title_y_offset
                
                self.e['Text']['small_font'].renderzb(
                    line, (title_x, title_y), line_width=0,
                    color=(200, 200, 200, self.title_fade_alpha), bgcolor=(0,0,0,0),
                    group='ui'
                )
    
    def _render_continue_prompt(self):
        if self.text_index >= len(self.text) and time.time() - self.wait_start_time > 1.0:
            if math.sin(time.time() * 4) > 0:
                prompt_text = "Press E to continue"
                prompt_size = self.e['Text']['small_font'].prep_text(prompt_text).size
                prompt_x = (340 - prompt_size[0]) // 2
                prompt_y = 200 if self.prologue_img else 140
                
                self.e['Text']['small_font'].renderzb(
                    prompt_text, (prompt_x, prompt_y), line_width=0,
                    color=(152,152,152), bgcolor=(0,0,0,0),
                    group='ui'
                )