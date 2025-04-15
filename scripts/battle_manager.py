import pygame
import scripts.pygpen as pp
from scripts.vfx import BattleVFX

class BattleManager(pp.ElementSingleton):
    def __init__(self, custom_id=None):
        super().__init__(custom_id)
        self.is_battling = False
        self.current_enemy = None
        self.turn = 'player'
        self.tremor_value = 0
        self.tremor_decay = 1
        self.game_over = False
        self.game_over_timer = 0
        self.player_die = False
        self.e_player_health = None
        self.end_game = False
        self.post_battle_enemy_type = None
        self.waiting_for_dialogue = False
        self.battle_end_time = 0
        
        self.vfx = None
        
    def _ensure_vfx(self):
        if self.vfx is None:
            self.vfx = BattleVFX(self.e)
        
    def start_battle(self, enemy):
        self._ensure_vfx()
        self.is_battling = True
        self.current_enemy = enemy
        self.turn = 'player'
        self.e['HUD'].set_battle_message("Battle started! Select a card.")
        self.e['HUD'].set_selected_card_index(0)
        self.set_tremor(0.5)
        self.game_over = False
        self.game_over_timer = 0
        
    def end_battle(self):
        self.is_battling = False
        self.e['HUD'].set_battle_message("")
        
        if hasattr(self.e['Game'].player, 'moves'):
            self.e['Game'].player.moves = [0, 0, 0, 0]
            if self.current_enemy.type == 'main_boss' and not self.player_die:
                self.end_game = True
        
        if self.current_enemy and self.current_enemy.hp <= 0:
            enemy_type = self.current_enemy.type
            pygame.time.set_timer(pygame.USEREVENT, 2000)
            self.e['Sounds'].play('death', volume=0.05)
            self.on_battle_end(enemy_type)

        if self.player_die and self.e['Game'].player.hp <= 10:
            pygame.time.set_timer(pygame.USEREVENT, 25000)
            self.on_battle_end('author')
        
    def on_battle_end(self, enemy):
        if enemy:
            self.post_battle_enemy_type = enemy
            self.battle_end_time = pygame.time.get_ticks() / 1000
            self.waiting_for_dialogue = True
            
            if enemy == 'main_boss':
                self.e['Sounds'].play_music('end_game', volume=0.5)
        
    def set_tremor(self, value):
        self.tremor_value = value
        self.e["Window"].tremor = value
        
        if self.game_over and value > 0:
            self.tremor_decay = 3.0
        
    def update(self):
        if hasattr(self.e['Game'], 'dialogue_manager') and self.e['Game'].dialogue_manager.active:
            return
        
        self._ensure_vfx()
        current_time = pygame.time.get_ticks() / 1000
        
        if self.waiting_for_dialogue:
            if current_time - self.battle_end_time >= 1.0:  
                self.e['Game'].dialogue_manager.start_post_battle_dialogue(self.post_battle_enemy_type)
                self.post_battle_enemy_type = None
                self.waiting_for_dialogue = False
        
        if not self.is_battling and not self.game_over:
            self.vfx.cleanup_old_sparks(current_time, force=True)
        
        if self.tremor_value > 0:
            self.tremor_value = max(0, self.tremor_value - self.tremor_decay * 0.016)
            self.e["Window"].tremor = self.tremor_value

        if self.game_over:
            self.game_over_timer -= 0.016
            if self.game_over_timer <= 0:
                self.game_over = False
                self.set_tremor(0)
                self.vfx.clear_all_sparks()
                return

        if not self.is_battling:
            return

        if self.e['HUD'].message_timer > 0:
            pass
        elif self.turn == 'player':
            self.handle_player_turn()
        elif self.turn == 'enemy':
            self.handle_enemy_turn()
        
        self.check_battle_end()
        
        self.vfx.update_sparks()
        
    def check_for_battle(self, current_room):
        if current_room.enemy is not None and not self.is_battling and not self.e['Game'].dialogue_manager.active:
            if current_room.enemy.type == 'main_boss':
                if self.e['Input'].pressed('action'):
                    self.e['Sounds'].play('action')
                    self.e['Game'].dialogue_manager.start_dialogue(current_room.enemy.type)
            elif self.e['Game'].player.action == 'idle' and not self.e['Game'].dialogue_manager.active:
                self.e['Game'].dialogue_manager.start_dialogue(current_room.enemy.type)
        
    def handle_player_turn(self):
        deck = self.e['Game'].deck
        
        if len(deck.cards) == 0:
            self.e['HUD'].set_battle_message("No spells available!")
            self.turn = 'enemy'
            return
      
        if self.e['Input'].pressed('left'):
            self.e['HUD'].set_selected_card_index(max(0, self.e['HUD'].selected_card_index - 1))
            self.e['Sounds'].play('action', volume=0.2)
            
        if self.e['Input'].pressed('right'):
            self.e['HUD'].set_selected_card_index(min(len(deck.cards) - 1, self.e['HUD'].selected_card_index + 1))
            self.e['Sounds'].play('action', volume=0.2)
        
        if self.e['Input'].pressed('action'):
            if self.e['HUD'].selected_card_index < len(deck.cards):
                self._use_player_card()
    
    def _use_player_card(self):
        deck = self.e['Game'].deck
        selected_card = deck.cards[self.e['HUD'].selected_card_index]
        
        amplifier = 5 if len(deck.cards) == 3 else 1
        damage = selected_card.spell.dmg * amplifier
        
        self.current_enemy.tkd(damage)
        self.e['Sounds'].play('damage', volume=0.5)

        tremor_intensity = min(1, 0.2 + (damage / 20))
        self.set_tremor(tremor_intensity)

        enemy_pos = self.current_enemy.center
        player_pos = self.e['Game'].player.rect.center if hasattr(self.e['Game'].player, 'rect') else (150, 150)

        if hasattr(selected_card, 'type'):
            card_type = selected_card.type.lower()
        else:
            card_type = selected_card.spell.type.lower()

        spark_color = self.vfx.get_attack_color(card_type)
        self.vfx.create_attack_effect(player_pos, enemy_pos, spark_color, damage, True)

        card_type_display = selected_card.type if hasattr(selected_card, 'type') else selected_card.spell.type
        self.e['HUD'].set_battle_message(f"Player used {card_type_display}! Dealt {damage} damage.")
        self.turn = 'enemy'
    
    def handle_enemy_turn(self):
        enemy = self.current_enemy
        player = self.e['Game'].player

        damage = enemy.use_card()

        if enemy.type == 'main_boss' and len(self.e['Game'].deck.cards) == 3 and self.e_player_health is None:
            self.e_player_health = player.hp
        
        if self.e_player_health is not None:
            damage = int((self.e_player_health // 4) + 5)

        if hasattr(player, 'tkd'):
            player.tkd(damage)
        else:
            player.take_damage(damage)
            self.e['Sounds'].play('damage', volume=0.5)

        tremor_intensity = min(1.5, 0.3 + (damage / 15))
        self.set_tremor(tremor_intensity)

        player_pos = player.center if hasattr(player, 'center') else player.rect.center if hasattr(player, 'rect') else (150, 150)
        enemy_pos = enemy.rect.center if hasattr(enemy, 'rect') else enemy.center if hasattr(enemy, 'center') else (200, 100)

        attack_type = enemy.cards[0].type if hasattr(enemy.cards[0], 'type') else enemy.cards[0].spell.type
        spark_color = self.vfx.get_attack_color(attack_type)

        self.vfx.create_attack_effect(enemy_pos, player_pos, spark_color, damage, False)

        self.e['HUD'].set_battle_message(f"Enemy attacks! Player takes {damage} damage.")
        self.turn = 'player'
    
    def check_battle_end(self):
        if self.current_enemy and self.current_enemy.hp <= 0:
            self._handle_enemy_defeat()

        if self.e['Game'].player.hp <= 0:
            self._handle_player_defeat()
    
    def _handle_enemy_defeat(self):
        if hasattr(self.e['Window'], 'fight'):
            self.e['Window'].fight = False

        self.e['HUD'].set_battle_message("Victory! Enemy defeated.", 15)

        current_room = self.e['Game'].room_manager.current_room_id
        self.e['Game'].room_manager.rooms[current_room].enemy = None
        
        self.set_tremor(0.6)

        self.e['Sounds'].play('death', volume=0.05)

        self.vfx.clear_all_sparks()
        self.game_over_timer = 0.4
        self.e['Window'].e_start_transition()
        self.end_battle()
    
    def _handle_player_defeat(self):
        if hasattr(self.e['Window'], 'fight'):
            self.e['Window'].fight = False

        self.e['HUD'].set_battle_message("Defeat! Player lost.")

        self.set_tremor(0.7)

        self.e['Sounds'].play('death', volume=0.05)

        self.vfx.clear_all_sparks()
        self.game_over = True
        self.game_over_timer = 0.4
        self.player_die = True
        self.end_battle()
    
    def handle_end_game(self):
        if self.end_game:
            self.e['Game'].start_scene_transition('game_over_1')
            self.e['Game'].game_over_start_time = pygame.time.get_ticks() / 1000
            self.e['Game'].scene = 'game_over_1'
            self.e['Game'].room_manager.update_tilemap(self.e['Game'].tilemap, '01')
            self.end_game = False
    
    def render(self):
        if not self.is_battling and not self.game_over and (self.vfx is None or len(self.vfx.sparks) == 0):
            return
        
        self._ensure_vfx()
        
        if self.game_over:
            self._handle_game_over_render()
            return

        if self.is_battling:
            self.e['HUD'].render_battle_ui(
                self.is_battling, 
                self.current_enemy, 
                self.e['Game'].player, 
                self.turn
            )

        self.vfx.render()
    
    def _handle_game_over_render(self):
        if self.player_die and self.e['Game'].player.hp < 40:
            self.e['Window'].e_start_transition()
            if hasattr(self.e['EntityGroups'], 'groups'):
                self.e['EntityGroups'].groups = {}
            self.e['Game'].reset()
        elif self.current_enemy and self.current_enemy.type == 'main_boss':
            self.end_game = True
        
        self.e['Window'].e_start_transition()
        self.game_over = False