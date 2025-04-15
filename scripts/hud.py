import pygame
import math
import time
import scripts.pygpen as pp

class SpellSlot(pp.Element):
    def __init__(self, position, index):
        super().__init__(f'spell_slot_{index}')
        self.position = position
        self.index = index
        self.spell = None
        self.is_selected = False

    def render(self):
        slot_pos = (self.position[0], self.position[1])
        # Використовуємо 'cards' замість 'spells' для зворотної сумісності
        self.e['Renderer'].blit(self.e['Assets'].images['cards']['slot'], slot_pos, group='ui')
        if self.spell:
            card_pos = (self.position[0]+1, self.position[1]+1)
            # Отримуємо зображення заклинання
            spell_img = self._get_spell_image()
            self.e['Renderer'].blit(
                pygame.transform.scale(
                    pygame.transform.flip(spell_img, False, True), 
                    (14,14)
                ), 
                card_pos, 
                group='ui'
            )
    
    def _get_spell_image(self):
        # Отримуємо зображення з правильного місця в assets
        if hasattr(self.spell, 'img'):
            return self.spell.img
        
        # Якщо spell.img не є доступним, спробуємо отримати зображення з Assets
        try:
            return self.e['Assets'].images['cards'][self.spell.type]
        except:
            # Запасний варіант: повертаємо пусте зображення
            return pygame.Surface((14, 14), pygame.SRCALPHA)

    def set_spell(self, spell):
        self.spell = spell

    def clear(self):
        self.spell = None
        self.is_selected = False

class HUD(pp.ElementSingleton):
    def __init__(self, custom_id=None):
        super().__init__(custom_id)
        self.slots = []
        self.create_slots()
        
        self._init_buff_state()
        self._init_battle_state()
        
    def _init_buff_state(self):
        self.buff_appear_duration = 1.0
        self.buff_appear_start = 0
        self.buff_appear_alpha = 0
        self.buff_y_offset = 40
        self.buff_appear_done = False
        self.showing_buff = False
        self.buff_spells = []
    
    def _init_battle_state(self):
        self.battle_message = ""
        self.message_timer = 0
        self.selected_spell_index = 0
        
    def create_slots(self):
        slot_size = 16
        margin = 2
        start_x = 255
        for i in range(3):
            position = (start_x + i * (slot_size + margin), 190)
            slot = SpellSlot(position, i)
            self.slots.append(slot)

    def update(self, spells):
        deck = self.e['Game'].spell_deck
        self._update_slots(deck)
        self._update_buff_display(spells)
        self._update_message_timer()
                
    def _update_slots(self, deck):
        for i, slot in enumerate(self.slots):
            if i < len(deck.spells):
                slot.set_spell(deck.spells[i])
            else:
                slot.clear()
    
    def _update_buff_display(self, spells):
        if len(spells) == 3 and not self.showing_buff:
            self._start_buff_animation(spells)
        elif len(spells) < 3:
            self.showing_buff = False
            self.buff_spells = []
        
        if self.showing_buff and not self.buff_appear_done:
            self._update_buff_animation()
    
    def _start_buff_animation(self, spells):
        self.buff_appear_start = time.time()
        self.buff_appear_alpha = 0
        self.buff_y_offset = 40
        self.buff_appear_done = False
        self.showing_buff = True
        self.buff_spells = spells.copy()
    
    def _update_buff_animation(self):
        current_time = time.time()
        progress = min(1.0, (current_time - self.buff_appear_start) / self.buff_appear_duration)
        
        if progress < 0.5:
            smoothed = 2 * progress * progress
        else:
            smoothed = 1 - pow(-2 * progress + 2, 2) / 2
        
        self.buff_appear_alpha = int(255 * smoothed)
        self.buff_y_offset = int(40 * (1 - smoothed))
        
        if progress >= 1.0:
            self.buff_appear_done = True
            self.buff_appear_alpha = 255
            self.buff_y_offset = 0
    
    def _update_message_timer(self):
        if self.message_timer > 0:
            self.message_timer -= 0.016

    def render(self):
        for slot in self.slots:
            slot.render()
        
        if self.showing_buff:
            self._render_buff_indicators()
    
    def _render_buff_indicators(self):
        buff_text = "+500%"
            
        self.e['Text']['small_font'].renderzb(
            buff_text, 
            (244, 210 + self.buff_y_offset), 
            line_width=0,
            color=self.get_color(0), 
            bgcolor=(0, 0, 0, 0),
            group='ui'
        )
            
        self.e['Text']['small_font'].renderzb(
            buff_text, 
            (269, 210 + self.buff_y_offset), 
            line_width=0,
            color=self.get_color(1), 
            bgcolor=(0, 0, 0, 0),
            group='ui'
        )
            
        self.e['Text']['small_font'].renderzb(
            buff_text, 
            (294, 210 + self.buff_y_offset), 
            line_width=0,
            color=self.get_color(2), 
            bgcolor=(0, 0, 0, 0),
            group='ui'
        )
            
    def render_battle_ui(self, is_battling, enemy, player, turn):
        if not is_battling:
            return
            
        self._render_battle_frame()
        self.render_battle_message()
        self.render_battle_stats(enemy, player, turn)
        self.render_player_spells(turn)
    
    def _render_battle_frame(self):
        screen_width, screen_height = 320, 240
        
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
    
    def render_battle_message(self):
        if self.battle_message and self.message_timer > 0:
            self.e['Text']['small_font'].renderzb(
                self.battle_message, (160, 20),
                line_width=0, color=(255, 255, 255),
                bgcolor=(40, 35, 40), group='ui'
            )
    
    def render_battle_stats(self, enemy, player, turn):
        turn_text = f"Turn: {turn.capitalize()}"
        self.e['Text']['small_font'].renderzb(
            turn_text, (20, 30), line_width=0,
            color=(255, 255, 255), bgcolor=(40, 35, 40),
            group='ui'
        )
        
        enemy_text = f"Enemy: {enemy.hp}/{enemy.max_hp}"
        self.e['Text']['small_font'].renderzb(
            enemy_text, (20, 65), line_width=0,
            color=(200, 152, 152), bgcolor=(40, 35, 40),
            group='ui'
        )

        player_text = f"You: {player.hp}/{player.max_hp}"
        self.e['Text']['small_font'].renderzb(
            player_text, (20, 50), line_width=0,
            color=(200, 152, 152), bgcolor=(40, 35, 40),
            group='ui'
        )
    
    def render_player_spells(self, turn):
        deck = self.e['Game'].spell_deck
        
        if turn == 'player' and len(deck.spells) > 0:
            for i, spell in enumerate(deck.spells):
                highlight = (i == self.selected_spell_index)
                color = (255, 255, 100) if highlight else (200, 200, 200)
                spell_type = spell.type if hasattr(spell, 'type') else spell.spell.type
                self.e['Text']['small_font'].renderzb(
                    f"{spell_type}", (130 + i * 40, 185),
                    line_width=0, color=color,
                    bgcolor=(40, 35, 40), group='ui'
                )
        
    def get_color(self, card_id):
        if card_id >= len(self.buff_spells):
            return (255, 255, 255)
            
        if self.buff_spells[card_id].type == 'fire':
            return (255, 131, 1)
        elif self.buff_spells[card_id].type == 'water':
            return (69, 198, 210)
        else:
            return (128, 50, 0)
            
    def get_selected_spell(self):
        for slot in self.slots:
            if slot.is_selected and slot.spell:
                return slot.spell, slot.index
        return None, -1
        
    def set_battle_message(self, message, timer=5):
        self.battle_message = message
        self.message_timer = timer
        
    def set_selected_spell_index(self, index):
        self.selected_spell_index = index