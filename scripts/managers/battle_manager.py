import pygame
import scripts.pygpen as pp
from scripts.vfx import BattleVFX

class BattleManager(pp.ElementSingleton):
    def __init__(self, custom_id=None):
        super().__init__(custom_id)
        self._init_battle_state()
        self._init_player_state()
        self._init_vfx()
    
    def _init_battle_state(self):
        self.is_battling = False
        self.turn = 'player'
        self.game_over = False
        self.game_over_timer = 0
        self.end_game = False
        self.current_enemy = None
        self.post_battle_enemy_type = None
        self.waiting_for_dialogue = False
        self.battle_end_time = 0
    
    def _init_player_state(self):
        self.player_die = False
        self.e_player_health = None
    
    def _init_vfx(self):
        self.vfx = None
        self.tremor_value = 0
        self.tremor_decay = 1
    
    def _ensure_vfx(self):
        if self.vfx is None:
            self.vfx = BattleVFX(self.e)
    
    def start_battle(self, enemy):
        self._ensure_vfx()
        self.is_battling = True
        self.current_enemy = enemy
        self.turn = 'player'
        self.e['HUD'].set_battle_message("Battle started! Select a spell.")
        self.e['HUD'].set_selected_spell_index(0)
        self.set_tremor(0.5)
        self.game_over = False
        self.game_over_timer = 0
    
    def end_battle(self):
        self.is_battling = False
        self.e['HUD'].set_battle_message("")
        
        self._handle_battle_aftermath()
    
    def _handle_battle_aftermath(self):
        self._reset_player_moves()
        
        if self._enemy_defeated():
            self._process_enemy_defeat()
        
        if self._player_critically_wounded():
            self._process_player_critical()
    
    def _reset_player_moves(self):
        if hasattr(self.e['Game'].player, 'moves'):
            self.e['Game'].player.moves = [0, 0, 0, 0]
            if self.current_enemy and self.current_enemy.type == 'main_boss' and not self.player_die:
                self.end_game = True
    
    def _enemy_defeated(self):
        return self.current_enemy and self.current_enemy.hp <= 0
    
    def _process_enemy_defeat(self):
        enemy_type = self.current_enemy.type
        pygame.time.set_timer(pygame.USEREVENT, 2000)
        self.e['Sounds'].play('death', volume=0.05)
        self.on_battle_end(enemy_type)
    
    def _player_critically_wounded(self):
        return self.player_die and self.e['Game'].player.hp <= 10
    
    def _process_player_critical(self):
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
        if self._dialogue_is_active():
            return
        
        self._ensure_vfx()
        current_time = pygame.time.get_ticks() / 1000
        
        self._check_waiting_dialogue(current_time)
        self._update_vfx_and_tremor(current_time)
        self._update_game_over_state()
        
        if not self.is_battling:
            return
        
        self._update_battle_state()
        self.vfx.update_sparks()
    
    def _dialogue_is_active(self):
        return hasattr(self.e['Game'], 'dialogue_manager') and self.e['Game'].dialogue_manager.active
    
    def _check_waiting_dialogue(self, current_time):
        if self.waiting_for_dialogue and current_time - self.battle_end_time >= 1.0:
            self.e['Game'].dialogue_manager.start_post_battle_dialogue(self.post_battle_enemy_type)
            self.post_battle_enemy_type = None
            self.waiting_for_dialogue = False
    
    def _update_vfx_and_tremor(self, current_time):
        if not self.is_battling and not self.game_over:
            self.vfx.cleanup_old_sparks(current_time, force=True)
        
        if self.tremor_value > 0:
            self.tremor_value = max(0, self.tremor_value - self.tremor_decay * 0.016)
            self.e["Window"].tremor = self.tremor_value
    
    def _update_game_over_state(self):
        if self.game_over:
            self.game_over_timer -= 0.016
            if self.game_over_timer <= 0:
                self.game_over = False
                self.set_tremor(0)
                self.vfx.clear_all_sparks()
    
    def _update_battle_state(self):
        if self.e['HUD'].message_timer > 0:
            return
            
        if self.turn == 'player':
            self.handle_player_turn()
        elif self.turn == 'enemy':
            self.handle_enemy_turn()
        
        self.check_battle_end()
    
    def check_for_battle(self, current_room):
        if current_room.enemy is None or self.is_battling or self.e['Game'].dialogue_manager.active:
            return
            
        if current_room.enemy.type == 'main_boss':
            if self.e['Input'].pressed('action'):
                self.e['Sounds'].play('action')
                self.e['Game'].dialogue_manager.start_dialogue(current_room.enemy.type)
        elif self.e['Game'].player.action == 'idle' and not self.e['Game'].dialogue_manager.active:
            self.e['Game'].dialogue_manager.start_dialogue(current_room.enemy.type)
    
    def handle_player_turn(self):
        deck = self.e['Game'].spell_deck
        
        if len(deck.spells) == 0:
            self.e['HUD'].set_battle_message("No spells available!")
            self.turn = 'enemy'
            return
        
        self._handle_player_input(deck)
    
    def _handle_player_input(self, deck):
        if self.e['Input'].pressed('left'):
            self._select_previous_spell()
        
        if self.e['Input'].pressed('right'):
            self._select_next_spell(deck)
        
        if self.e['Input'].pressed('action'):
            self._try_use_spell(deck)
    
    def _select_previous_spell(self):
        self.e['HUD'].set_selected_spell_index(max(0, self.e['HUD'].selected_spell_index - 1))
        self.e['Sounds'].play('action', volume=0.2)
    
    def _select_next_spell(self, deck):
        self.e['HUD'].set_selected_spell_index(min(len(deck.spells) - 1, self.e['HUD'].selected_spell_index + 1))
        self.e['Sounds'].play('action', volume=0.2)
    
    def _try_use_spell(self, deck):
        if self.e['HUD'].selected_spell_index < len(deck.spells):
            self._use_player_spell()
    
    def _use_player_spell(self):
        deck = self.e['Game'].spell_deck
        selected_spell = deck.spells[self.e['HUD'].selected_spell_index]
        
        damage = self._calculate_damage(selected_spell)
        self._apply_damage_to_enemy(damage)
        self._create_attack_effect(selected_spell, damage)
        self._show_attack_message(selected_spell, damage)
        
        self.turn = 'enemy'
    
    def _calculate_damage(self, spell):
        amplifier = 5 if len(self.e['Game'].spell_deck.spells) == 3 else 1
        return spell.spell.dmg * amplifier
    
    def _apply_damage_to_enemy(self, damage):
        self.current_enemy.tkd(damage)
        self.e['Sounds'].play('damage', volume=0.5)
        
        tremor_intensity = min(1, 0.2 + (damage / 20))
        self.set_tremor(tremor_intensity)
    
    def _create_attack_effect(self, spell, damage):
        enemy_pos = self.current_enemy.center
        player_pos = self._get_player_position()
        
        spell_type = self._get_spell_type(spell)
        spark_color = self.vfx.get_attack_color(spell_type.lower())
        
        self.vfx.create_attack_effect(player_pos, enemy_pos, spark_color, damage, True)
    
    def _get_player_position(self):
        player = self.e['Game'].player
        if hasattr(player, 'rect'):
            return player.rect.center
        return (150, 150)
    
    def _get_spell_type(self, spell):
        if hasattr(spell, 'type'):
            return spell.type
        return spell.spell.type
    
    def _show_attack_message(self, spell, damage):
        spell_type = self._get_spell_type(spell)
        self.e['HUD'].set_battle_message(f"Player used {spell_type}! Dealt {damage} damage.")
    
    def handle_enemy_turn(self):
        enemy = self.current_enemy
        player = self.e['Game'].player
        
        damage = self._calculate_enemy_damage(enemy)
        self._apply_damage_to_player(player, damage)
        self._create_enemy_attack_effect(enemy, player, damage)
        
        self.e['HUD'].set_battle_message(f"Enemy attacks! Player takes {damage} damage.")
        self.turn = 'player'
    
    def _calculate_enemy_damage(self, enemy):
        damage = enemy.use_spell()
        
        if self._is_main_boss_battle():
            if self.e_player_health is None:
                self.e_player_health = self.e['Game'].player.hp
            
            damage = int((self.e_player_health // 4) + 5)
            
        return damage
    
    def _is_main_boss_battle(self):
        return (self.current_enemy.type == 'main_boss' and 
                len(self.e['Game'].spell_deck.spells) == 3 and 
                self.e_player_health is None)
    
    def _apply_damage_to_player(self, player, damage):
        if hasattr(player, 'tkd'):
            player.tkd(damage)
        else:
            player.take_damage(damage)
            self.e['Sounds'].play('damage', volume=0.5)
        
        tremor_intensity = min(1.5, 0.3 + (damage / 15))
        self.set_tremor(tremor_intensity)
    
    def _create_enemy_attack_effect(self, enemy, player, damage):
        player_pos = self._get_entity_position(player)
        enemy_pos = self._get_entity_position(enemy)
        
        attack_type = self._get_enemy_attack_type()
        spark_color = self.vfx.get_attack_color(attack_type)
        
        self.vfx.create_attack_effect(enemy_pos, player_pos, spark_color, damage, False)
    
    def _get_entity_position(self, entity):
        if hasattr(entity, 'center'):
            return entity.center
        if hasattr(entity, 'rect'):
            return entity.rect.center
        return (200, 100) if entity == self.current_enemy else (150, 150)
    
    def _get_enemy_attack_type(self):
        spell = self.current_enemy.spells[0]
        if hasattr(spell, 'type'):
            return spell.type
        return spell.spell.type
    
    def check_battle_end(self):
        if self.current_enemy and self.current_enemy.hp <= 0:
            self._handle_enemy_defeat()
        
        if self.e['Game'].player.hp <= 0:
            self._handle_player_defeat()
    
    def _handle_enemy_defeat(self):
        self._disable_fight_state()
        self.e['HUD'].set_battle_message("Victory! Enemy defeated.", 15)
        self._clear_enemy_from_room()
        
        self.set_tremor(0.6)
        self.e['Sounds'].play('death', volume=0.05)
        
        self._prepare_game_over_state()
        self.end_battle()
    
    def _disable_fight_state(self):
        if hasattr(self.e['Window'], 'fight'):
            self.e['Window'].fight = False
    
    def _clear_enemy_from_room(self):
        current_room = self.e['Game'].room_manager.current_room_id
        self.e['Game'].room_manager.rooms[current_room].enemy = None
    
    def _prepare_game_over_state(self):
        self.vfx.clear_all_sparks()
        self.game_over_timer = 0.4
        self.e['Window'].e_start_transition()
    
    def _handle_player_defeat(self):
        self._disable_fight_state()
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
        if self._nothing_to_render():
            return
        
        self._ensure_vfx()
        
        if self.game_over:
            self._handle_game_over_render()
            return
        
        if self.is_battling:
            self._render_battle_ui()
        
        self.vfx.render()
    
    def _nothing_to_render(self):
        return (not self.is_battling and 
                not self.game_over and 
                (self.vfx is None or len(self.vfx.sparks) == 0))
    
    def _render_battle_ui(self):
        self.e['HUD'].render_battle_ui(
            self.is_battling, 
            self.current_enemy, 
            self.e['Game'].player, 
            self.turn
        )
    
    def _handle_game_over_render(self):
        if self._should_reset_game():
            self._initiate_game_reset()
        elif self._is_main_boss_defeat():
            self.end_game = True
        
        self.e['Window'].e_start_transition()
        self.game_over = False
    
    def _should_reset_game(self):
        return self.player_die and self.e['Game'].player.hp < 40
    
    def _initiate_game_reset(self):
        self.e['Window'].e_start_transition()
        if hasattr(self.e['EntityGroups'], 'groups'):
            self.e['EntityGroups'].groups = {}
        self.e['Game'].reset()
    
    def _is_main_boss_defeat(self):
        return self.current_enemy and self.current_enemy.type == 'main_boss'