import pygame
import math
import time
import scripts.pygpen as pp

class CardSlot(pp.Element):
    def __init__(self, position, index):
        super().__init__(f'card_slot_{index}')
        self.position = position
        self.index = index
        self.card = None
        self.is_selected = False

    def render(self):
        slot_pos = (self.position[0], self.position[1])
        self.e['Renderer'].blit(self.e['Assets'].images['cards']['slot'], slot_pos, group='ui')
        if self.card:
            card_pos = (self.position[0]+1, self.position[1]+1)
            self.e['Renderer'].blit(pygame.transform.scale(pygame.transform.flip(self.card.img, False, True), (14,14)), card_pos, group='ui')

    def set_card(self, card):
        self.card = card

    def clear(self):
        self.card = None
        self.is_selected = False

class HUD(pp.ElementSingleton):
    def __init__(self, custom_id=None):
        super().__init__(custom_id)
        self.slots = []
        self.create_slots()
        
        self.buff_appear_duration = 1.0
        self.buff_appear_start = 0
        self.buff_appear_alpha = 0
        self.buff_y_offset = 40
        self.buff_appear_done = False
        self.showing_buff = False
        self.buff_cards = []
        
        self.battle_message = ""
        self.message_timer = 0
        self.selected_card_index = 0
        
    def create_slots(self):
        slot_size = 16
        margin = 2
        start_x = 255
        for i in range(3):
            position = (start_x + i * (slot_size + margin), 190)
            slot = CardSlot(position, i)
            self.slots.append(slot)

    def update(self, cards):
        deck = self.e['Game'].deck
        for i, slot in enumerate(self.slots):
            if i < len(deck.cards):
                slot.set_card(deck.cards[i])
            else:
                slot.clear()
        
        if len(cards) == 3 and not self.showing_buff:
            self.buff_appear_start = time.time()
            self.buff_appear_alpha = 0
            self.buff_y_offset = 40
            self.buff_appear_done = False
            self.showing_buff = True
            self.buff_cards = cards.copy()
        elif len(cards) < 3:
            self.showing_buff = False
            self.buff_cards = []
        
        if self.showing_buff and not self.buff_appear_done:
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
                
        if self.message_timer > 0:
            self.message_timer -= 0.016

    def render(self):
        for slot in self.slots:
            slot.render()
        
        if self.showing_buff:
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
        
        self.render_battle_message()
        self.render_battle_stats(enemy, player, turn)
        self.render_player_cards(turn)
    
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
    
    def render_player_cards(self, turn):
        deck = self.e['Game'].deck
        
        if turn == 'player' and len(deck.cards) > 0:
            for i, card in enumerate(deck.cards):
                highlight = (i == self.selected_card_index)
                color = (255, 255, 100) if highlight else (200, 200, 200)
                card_type = card.type if hasattr(card, 'type') else card.spell.type
                self.e['Text']['small_font'].renderzb(
                    f"{card_type}", (130 + i * 40, 185),
                    line_width=0, color=color,
                    bgcolor=(40, 35, 40), group='ui'
                )
        
    def get_color(self, card_id):
        if card_id >= len(self.buff_cards):
            return (255, 255, 255)
            
        if self.buff_cards[card_id].type == 'fire':
            return (255, 131, 1)
        elif self.buff_cards[card_id].type == 'water':
            return (69, 198, 210)
        else:
            return (128, 50, 0)
            
    def get_selected_card(self):
        for slot in self.slots:
            if slot.is_selected and slot.card:
                return slot.card, slot.index
        return None, -1
        
    def set_battle_message(self, message, timer=5):
        self.battle_message = message
        self.message_timer = timer
        
    def set_selected_card_index(self, index):
        self.selected_card_index = index