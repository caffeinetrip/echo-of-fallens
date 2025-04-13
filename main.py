import pygame
import sys
import math
import time
import os
import scripts.pygpen as pp
from scripts.hooks import gen_hook, LOCATIONS
from scripts.player import Player
from scripts.room_manager import RoomManager
from scripts.deck import Deck
from scripts.hud import HUD
from scripts.battle_manager import BattleManager
from scripts.dialogue_manager import DialogueManager
from scripts.scenes import PrologueScene, GameOverScene
from scripts.cards import Card

moves = ['left', 'right', 'up', 'down']

class Game(pp.PygpenGame):
    def load(self):
        pp.init(
            (1020, 660),
            fps_cap=165,
            caption='Echo of Fallens',
            opengl=True,
            input_path='data/key_configs/config.json',
            spritesheet_path='data/images/spritesheets',
            entity_path='data/images/entities',
            font_path='data/fonts',
            frag_path='shaders/shader.frag',
            sounds_path='data/sounds',
            sound_filetype='mp3'
        )
        self.post_battle_enemy_type = None
        self.battle_end_time = 0
        self.waiting_for_dialogue = False 
        
        self.player_deaths = 0
        self.game_over_start_time = 0
        self.scene_transition_timer = 0
        self.transition_duration = 2.0
        self.scene_transitioning = False
            
        self.bg_surf = pygame.Surface((340, 220), pygame.SRCALPHA)
        self.display = pygame.Surface((340, 220), pygame.SRCALPHA)
        self.ui_surf = pygame.Surface((340, 220), pygame.SRCALPHA)
        self.e['Assets'].load_folder('data/images/cards', colorkey=(0, 0, 0))
        self.e['Assets'].load_folder('data/images/enemy', colorkey=(0, 0, 0))
        self.e['Renderer'].set_groups(['default', 'ui', 'background'])
        
        self.camera = pp.Camera(self.display.get_size(), slowness=0.3, pos=(5, 0))
        self.scene = 'prologue'
        self.hud = HUD()
        self.battle_manager = BattleManager()
        self.dialogue_manager = DialogueManager()
        self.prologue = PrologueScene(self)
        self.on_battle_end_enemy = None
        self.deep_room_warning_shown = False
        self.reset()
        self.e['Window'].start_transition()

        self.e['Sounds'].play_music('default', volume=0.4)
        
    def reset(self):
        self.tilemap = pp.Tilemap(tile_size=(16, 16))
        self.tilemap.load('data/saves/map/rooms/spawn.pmap', spawn_hook=gen_hook())
        self.avalible_spells = ["fire", "water", "earth"]
        self.avalible_bosses = ["mom_ghost", "father_ghost"]
        self.player_chance = 1
        self.player_boss_chance_amp = 1
        self.room_manager = RoomManager()
        self.player = Player('player', (184, 110), room=self.room_manager.current_room_id)
        self.e['EntityGroups'].add(self.player, 'entities')
        self.deck = Deck()
        self.player_deaths += 1
        self.battle_manager.player_die = False

        self.post_battle_enemy_type = None
        self.waiting_for_dialogue = False 
        self.scene_transitioning = False
        self.deep_room_warning_shown = False
        
        self.on_battle_end(self.on_battle_end_enemy)

        if self.scene != 'prologue':
            self.e['Sounds'].play_music('default', volume=0.4)
             
    def on_battle_end(self, enemy):
        if enemy:
            self.post_battle_enemy_type = enemy
            self.battle_end_time = time.time()
            self.waiting_for_dialogue = True
            self.on_battle_end_enemy = enemy
            if enemy == 'main_boss':
                self.e['Sounds'].play_music('end_game', volume=0.5)
        
    def start_scene_transition(self, next_scene):
        self.scene_transitioning = True
        self.scene_transition_timer = time.time()
        self.next_scene = next_scene
        self.e['Window'].e_start_transition()
        
    def update(self):
        self.bg_surf.fill((22, 22, 22, 0))
        self.display.fill((0, 0, 0, 0))
        self.ui_surf.fill((0, 0, 0, 0))
        
        current_time = time.time()

        if self.waiting_for_dialogue:
            if current_time - self.battle_end_time >= 1.0:  
                self.dialogue_manager.start_post_battle_dialogue(self.post_battle_enemy_type)
                self.post_battle_enemy_type = None
                self.waiting_for_dialogue = False

        if self.scene_transitioning:
            if current_time - self.scene_transition_timer >= self.transition_duration:
                self.scene = self.next_scene
                self.scene_transitioning = False
                self.e['Window'].e_start_transition()
                
                if self.scene == 'game_over_2':
                    self.room_manager.update_tilemap(self.tilemap, '02')
        
        if self.scene == 'prologue':
            self.prologue.update()
            self.prologue.render()
        elif self.scene == 'game_over':
            self.game_over_screen.update()
            self.game_over_screen.render()
        elif self.scene in ['game', 'game_over_1', 'game_over_2']:
            if self.scene == 'game' and self.e['Sounds'].current_music != 'default':
                self.e['Sounds'].play_music('default', volume=0.3)
                
            self.camera.update()
            self.tilemap.renderz(pygame.Rect(self.camera[0] - 16, self.camera[1] - 16,
                                          self.display.get_width() + 16, self.display.get_height() + 16),
                               offset=self.camera)

            self.e['EntityGroups'].update()
            self.e['EntityGroups'].renderz(offset=self.camera)
            
            text = f"Room: {self.room_manager.current_room_id}"
            self.e['Text']['small_font'].renderzb(text, (10, 10), line_width=0,
                                              color=(255, 255, 255), bgcolor=(40, 35, 40),
                                              group='ui')
            
            self.hud.update(self.deck.cards)
            self.hud.render()
            
            current_room = self.room_manager.rooms[self.room_manager.current_room_id]
            
            if current_room.card != None:
                current_room.card.render()
            
            if current_room.enemy != None:
                current_room.enemy.render()
                
                if not self.battle_manager.is_battling and not self.dialogue_manager.active:
                    if current_room.enemy.type == 'main_boss':
                        if self.e['Input'].pressed('action'):
                            self.e['Sounds'].play('action')
                            self.dialogue_manager.start_dialogue(current_room.enemy.type)
                    elif self.player.action == 'idle' and not self.dialogue_manager.active:
                        self.dialogue_manager.start_dialogue(current_room.enemy.type)
                
            self.battle_manager.update()
            self.battle_manager.render()
            
            self.dialogue_manager.update()
            self.dialogue_manager.render()

            if self.battle_manager.end_game:
                self.start_scene_transition('game_over_1')
                self.game_over_start_time = current_time
                self.scene = 'game_over_1'
                self.room_manager.update_tilemap(self.tilemap, '01')
                self.battle_manager.end_game = False
                
            if self.scene == 'game_over_1' and not self.scene_transitioning:
                if current_time - self.game_over_start_time >= 2.0:
                    self.scene = 'game_over_2'
                    self.start_scene_transition('game_over_2')
                    
        self.e['Renderer'].cycle({'default': self.display,
                                'ui': self.ui_surf,
                                'background': self.bg_surf})
        
        if self.e['Input'].pressed('quit'):
            pygame.quit()
            sys.exit()
        
        self.e['Window'].cycle({'surface': self.display,
                              'bg_surf': self.bg_surf,
                              'ui_surf': self.ui_surf})
        
        room = [abs(pp.game_math.convert_string_to_list(self.room_manager.current_room_id)[0]), 
                abs(pp.game_math.convert_string_to_list(self.room_manager.current_room_id)[1])]

        room_sum = sum(room)

        if room_sum > 10 and not self.deep_room_warning_shown and not self.dialogue_manager.active and len(self.deck.cards) == 3:
            self.dialogue_manager.show_center_text()
            self.deep_room_warning_shown = True

        if room_sum > 10:
            target_gain = ((room_sum - 10) * 3) / 10 + 1
            current_gain = self.e['Window'].noise_gain
            self.e['Window'].noise_gain = current_gain + (target_gain - current_gain) * 0.1


if __name__ == "__main__":
    Game().run()