import math, time, pygame
from .. import pygpen as pp

class PrologueScene(pp.ElementSingleton):

    PROLOGUE_TEXT = "He was from a family of miners. One day his family didn't return from the mine. And while waiting for his parents he accidentally fell..."
    TITLE_TEXT = "Made for Ludum Dare 57\nby soma"
    CONTINUE_PROMPT = "Press E to continue"
    
    def __init__(self, custom_id=None):
        super().__init__(custom_id)
        self.char_delay = 0.05
        self.title_char_delay = 0.08
        self.img_fade_speed = 1.5

        self.current_text = ""
        self.current_title = ""
        self.text_index = self.title_index = 0
        self.last_char_time = self.last_title_char_time = self.wait_start_time = time.time()
        self.title_fade_start = 0
        self.title_fade_alpha = 0
        self.title_y_offset = 20
        self.img_alpha = 0
        self.completed = self.waiting_for_input = self.title_visible = False

        self.prologue_img = self.e['Assets'].images.get('prologue')
        if not self.prologue_img:
            self.prologue_img = pygame.image.load('data/images/prologue.png').convert_alpha()
    
    def update(self):
        current_time = time.time()
        
        if self.e['Input'].pressed('action'):
            self.completed = True
            self.e['GameStateSystem'].scene = 'game'
            self.e['Window'].start_transition()
            self.e['Sounds'].play('action', volume=0.4)
            self.e['Sounds'].play_music('default', volume=0.4)
            return
            
        if not self.completed:
            if self.img_alpha < 255:
                self.img_alpha = min(255, self.img_alpha + self.img_fade_speed)
            
            if self.text_index < len(self.PROLOGUE_TEXT):
                self._update_text_typing(current_time)
            else:
                self._update_title_reveal(current_time)
    
    def _update_text_typing(self, current_time):
        if current_time - self.last_char_time > self.char_delay:
            next_char = self.PROLOGUE_TEXT[self.text_index]
            self.current_text += next_char
            self.text_index += 1
            self.last_char_time = current_time
            
            if self.text_index <= len(self.PROLOGUE_TEXT) - 1 and next_char != ' ':
                self.e['Sounds'].play('author_talk', volume=0.1)
    
    def _update_title_reveal(self, current_time):
        if not self.title_visible:
            self.title_visible = True
            self.title_fade_start = current_time
        if not self.waiting_for_input:
            self.waiting_for_input = True
            self.wait_start_time = current_time
        
        # update title typing
        if self.title_index < len(self.TITLE_TEXT):
            if current_time - self.last_title_char_time > self.title_char_delay:
                self.current_title += self.TITLE_TEXT[self.title_index]
                self.title_index += 1
                self.last_title_char_time = current_time
        
        # update title fade effect
        if self.title_visible:
            progress = min(1.0, (current_time - self.title_fade_start) / 1.5)  # title_fade_duration = 1.5
            smoothed = 2 * progress * progress if progress < 0.5 else 1 - pow(-2 * progress + 2, 2) / 2
            self.title_fade_alpha = int(255 * smoothed)
            self.title_y_offset = int(20 * (1 - smoothed))
    
    def render(self):
        self.e['Game'].display.fill((10, 10, 10))
        current_time = time.time()
        
        # render image
        if self.prologue_img:
            img_copy = self.prologue_img.copy()
            if self.img_alpha < 255:
                img_copy.set_alpha(self.img_alpha)
            img_x = (340 - self.prologue_img.get_width()) // 2
            self.e['Renderer'].blit(img_copy, (img_x, 30), group='default')
        
        # render main text
        text_prep = self.e['Text']['small_font'].prep_text(self.current_text, 300)
        text_x = (340 - text_prep.size[0]) // 2
        text_y = 175 if self.prologue_img else 80
        self.e['Text']['small_font'].renderzb(
            self.current_text, (text_x, text_y), line_width=300,
            color=(255, 255, 255), bgcolor=(0, 0, 0, 0), group='ui'
        )
        
        # render title
        if self.title_visible and self.current_title:
            for i, line in enumerate(self.current_title.split('\n')):
                title_prep = self.e['Text']['small_font'].prep_text(line)
                title_x = (340 - title_prep.size[0]) // 2
                title_y = 230 + i * 15 - self.title_y_offset
                self.e['Text']['small_font'].renderzb(
                    line, (title_x, title_y), line_width=0,
                    color=(200, 200, 200, self.title_fade_alpha), bgcolor=(0, 0, 0, 0), group='ui'
                )
        
        # render continue prompt
        if (self.text_index >= len(self.PROLOGUE_TEXT) and 
                current_time - self.wait_start_time > 1.0 and
                math.sin(current_time * 4) > 0):
            prompt_size = self.e['Text']['small_font'].prep_text(self.CONTINUE_PROMPT).size
            prompt_x = (340 - prompt_size[0]) // 2
            prompt_y = 200 if self.prologue_img else 140
            self.e['Text']['small_font'].renderzb(
                self.CONTINUE_PROMPT, (prompt_x, prompt_y), line_width=0,
                color=(152, 152, 152), bgcolor=(0, 0, 0, 0), group='ui'
            )