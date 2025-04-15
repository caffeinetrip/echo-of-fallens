import pygame
import math
import time
import json
import os
import scripts.pygpen as pp

class DialogueManager(pp.ElementSingleton):
    def __init__(self, custom_id=None):
        super().__init__(custom_id)
        self._init_dialogue_state()
        self._init_animation_state()
        self.load_dialogues()
    
    def _init_dialogue_state(self):
        self.active = False
        self.current_dialogue = []
        self.dialogue_index = 0
        self.current_text = ""
        self.text_index = 0
        self.last_char_time = 0
        self.char_delay = 0.03
        self.post_battle_mode = False
        self.fade_alpha = 255
        self.fade_speed = 0.5
        self.display_time = 0
        self.glow_effect = 0
        self.dialogues = {}
        self.post_battle_dialogues = {}
        self.speaker = ""
    
    def _init_animation_state(self):
        self.prompt_animation_speed = 1.5
        self.prompt_max_alpha = 100
        self.prompt_min_alpha = 30
        
        self.dialogue_appear_duration = 0.5
        self.dialogue_appear_start = 0
        self.dialogue_appear_alpha = 0
        self.dialogue_box_y_offset = 0
        self.dialogue_appear_done = False
    
    def load_dialogues(self):
        try:
            with open('data/dialogues.json', 'r') as f:
                dialogue_data = json.load(f)
                self.dialogues = dialogue_data.get('dialogues', {})
                self.post_battle_dialogues = dialogue_data.get('post_battle_dialogues', {})
        except:
            self._create_default_dialogues()
    
    def _create_default_dialogues(self):
        os.makedirs('data', exist_ok=True)
        
        with open('data/dialogues.json', 'w') as f:
            json.dump({
                'dialogues': self.dialogues,
                'post_battle_dialogues': self.post_battle_dialogues
            }, f, indent=4)
    
    def start_dialogue(self, enemy_type):
        self.active = True
        self.post_battle_mode = False
        self.current_dialogue = self.dialogues.get(enemy_type, ["No dialogue available"])
        self.dialogue_index = 0
        self.current_text = ""
        self.text_index = 0
        self.display_time = time.time()
        self.speaker = enemy_type
        
        self._start_dialogue_animation()
        
    def start_post_battle_dialogue(self, enemy_type):
        self.active = True
        self.post_battle_mode = True
        self.fade_alpha = 255
        self.current_dialogue = self.post_battle_dialogues.get(enemy_type, [""])
        self.dialogue_index = 0
        self.current_text = ""
        self.text_index = 0
        self.display_time = time.time()
        self.speaker = enemy_type
        
        self._start_dialogue_animation()
        
    def show_center_text(self, message="Go back to the ugly smile!"):
        self.active = True
        self.post_battle_mode = True
        self.fade_alpha = 255
        self.current_dialogue = [message]
        self.dialogue_index = 0
        self.current_text = ""
        self.text_index = 0
        self.display_time = time.time()
        self.speaker = "system"
        
        self._start_dialogue_animation()
    
    def _start_dialogue_animation(self):
        self.dialogue_appear_start = time.time()
        self.dialogue_appear_alpha = 0
        self.dialogue_box_y_offset = 20
        self.dialogue_appear_done = False
    
    def update(self):
        if not self.active:
            return
            
        current_time = time.time()
        
        self._update_animation_state(current_time)
        
        if self.post_battle_mode:
            self._update_post_battle_dialogue(current_time)
        else:
            self._update_normal_dialogue(current_time)
    
    def _update_animation_state(self, current_time):
        if self.dialogue_index > 0:
            self.dialogue_appear_done = True
            self.dialogue_appear_alpha = 255
            self.dialogue_box_y_offset = 0
        
        if not self.dialogue_appear_done:
            self._update_dialogue_appear_animation(current_time)
    
    def _update_dialogue_appear_animation(self, current_time):
        progress = min(1.0, (current_time - self.dialogue_appear_start) / self.dialogue_appear_duration)
        if progress < 0.5:
            smoothed = 2 * progress * progress
        else:
            smoothed = 1 - pow(-2 * progress + 2, 2) / 2
            
        self.dialogue_appear_alpha = int(255 * smoothed)
        self.dialogue_box_y_offset = int(20 * (1 - smoothed))
        
        if progress >= 1.0:
            self.dialogue_appear_done = True
            self.dialogue_appear_alpha = 255
            self.dialogue_box_y_offset = 0
    
    def _update_post_battle_dialogue(self, current_time):
        if current_time - self.display_time > 0.1:
            self.fade_alpha = max(0, self.fade_alpha - self.fade_speed)
            if self.fade_alpha <= 0:
                self.active = False
                return
        
        if self.text_index < len(self.current_dialogue[self.dialogue_index]):
            self._reveal_text_character(current_time)
    
    def _update_normal_dialogue(self, current_time):
        input_manager = self.e.elems['singletons']['Input']
        
        if self.dialogue_index < len(self.current_dialogue):
            current_dialogue_text = self.current_dialogue[self.dialogue_index]
            
            if input_manager.pressed('action'):
                self._handle_action_press(current_dialogue_text)
            
            if self.text_index < len(current_dialogue_text) and not input_manager.pressed('action'):
                self._reveal_text_character(current_time)
    
    def _handle_action_press(self, dialogue_text):
        self.e['Sounds'].play('action', volume=0.15)
        
        if self.text_index < len(dialogue_text):
            self._complete_text_reveal(dialogue_text)
        else:
            self._advance_to_next_dialogue()
    
    def _complete_text_reveal(self, dialogue_text):
        self.current_text = dialogue_text
        self.text_index = len(dialogue_text)
    
    def _advance_to_next_dialogue(self):
        self.dialogue_index += 1
        if self.dialogue_index < len(self.current_dialogue):
            self.current_text = ""
            self.text_index = 0
            
            self._start_dialogue_animation()
        else:
            self._end_dialogue()
    
    def _end_dialogue(self):
        self.active = False
        current_room = self.e['Game'].room_manager.rooms[self.e['Game'].room_manager.current_room_id]
        if current_room.enemy and not self.e['Game'].battle_manager.is_battling:
            self.e['Game'].battle_manager.start_battle(current_room.enemy)
            self.e.elems['singletons']['Window'].e_start_transition()
    
    def _reveal_text_character(self, current_time):
        if current_time - self.last_char_time > self.char_delay:
            dialogue_text = self.current_dialogue[self.dialogue_index]
            self.current_text += dialogue_text[self.text_index]
            self.text_index += 1
            self.last_char_time = current_time
            
            self._play_dialogue_sound()
    
    def _play_dialogue_sound(self):
        if (self.text_index <= len(self.current_dialogue[self.dialogue_index])-1 and 
            self.current_dialogue[self.dialogue_index][self.text_index] != ' '):
            if self.speaker == 'main_boss':
                self.e['Sounds'].play('main_boss_talk', volume=0.15)
            elif self.speaker in ['mom_ghost', 'father_ghost']:
                self.e['Sounds'].play('ghost_talk', volume=0.15)
            elif self.speaker == 'author':
                self.e['Sounds'].play('author_talk', volume=0.15)
    
    def render(self):
        if not self.active:
            return
            
        if self.post_battle_mode:
            self._render_post_battle_dialogue()
        else:
            self._render_normal_dialogue()
    
    def _render_post_battle_dialogue(self):
        text = self.e.elems['singletons']['Text']
        effective_alpha = min(self.fade_alpha, self.dialogue_appear_alpha)
        
        text_size = text['small_font'].prep_text(self.current_text).size
        text_x = (340 - text_size[0]) // 2
        text_y = 195 + self.dialogue_box_y_offset
        
        text['small_font'].renderzb(
            self.current_text, (text_x, text_y), line_width=0,
            color=(255, 255, 255, effective_alpha), bgcolor=(0,0,0,0),
            group='ui'
        )
    
    def _render_normal_dialogue(self):
        text = self.e.elems['singletons']['Text']
        effective_alpha = self.dialogue_appear_alpha
        
        text_prep = text['small_font'].prep_text(self.current_text, 250)
        text_x = (340 - text_prep.size[0]) // 2
        text_y = 145 + self.dialogue_box_y_offset
        
        text['small_font'].renderzb(
            self.current_text, (text_x, text_y), line_width=250,
            color=(255, 255, 255, effective_alpha), bgcolor=(0,0,0,0),
            group='ui'
        )
        
        if self._should_show_continue_prompt():
            self._render_continue_prompt(text, text_prep, text_y)
    
    def _should_show_continue_prompt(self):
        return (self.text_index >= len(self.current_dialogue[self.dialogue_index]) and 
                self.dialogue_appear_done)
    
    def _render_continue_prompt(self, text, text_prep, text_y):
        alpha_range = self.prompt_max_alpha - self.prompt_min_alpha
        alpha_offset = self.prompt_min_alpha
        alpha_value = int(alpha_offset + alpha_range * (0.5 + 0.5 * math.sin(time.time() * self.prompt_animation_speed)))
        
        prompt_text = "Press E to continue"
        prompt_size = text['small_font'].prep_text(prompt_text).size
        prompt_x = (340 - prompt_size[0]) // 2
        prompt_y = text_y + text_prep.size[1] + 40
        
        text['small_font'].renderzb(
            prompt_text, (prompt_x, prompt_y), line_width=0,
            color=(150, 150, 150, alpha_value), bgcolor=(0,0,0,0),
            group='ui'
        )