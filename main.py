import pygame
import sys
import time
import scripts.pygpen as pp
from scripts.hooks import gen_hook
from scripts.player import Player
from scripts.room_manager import RoomManager
from scripts.deck import Deck
from scripts.hud import HUD
from scripts.battle_manager import BattleManager
from scripts.dialogue_manager import DialogueManager
from scripts.scenes import PrologueScene

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
        
        self.bg_surf = pygame.Surface((340, 220), pygame.SRCALPHA)
        self.display = pygame.Surface((340, 220), pygame.SRCALPHA)
        self.ui_surf = pygame.Surface((340, 220), pygame.SRCALPHA)
        
        self.e['Assets'].load_folder('data/images/cards', colorkey=(0, 0, 0))
        self.e['Assets'].load_folder('data/images/enemy', colorkey=(0, 0, 0))
        self.e['Renderer'].set_groups(['default', 'ui', 'background'])
        
        self.camera = pp.Camera(self.display.get_size(), slowness=0.3, pos=(5, 0))
        self.hud = HUD()
        self.battle_manager = BattleManager()
        self.dialogue_manager = DialogueManager()
        self.prologue = PrologueScene(self)
        
        self.scene = 'prologue'
        self.player_deaths = 0
        
        self.scene_transition_timer = 0
        self.transition_duration = 2.0
        self.game_over_start_time = 0
        
        self.reset()
        
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

        self.scene_transitioning = False
        self.deep_room_warning_shown = False
        
        self.e['Window'].start_transition()
        self.play_music()
        
    def play_music(self):
        if self.scene != 'prologue':
            self.e['Sounds'].play_music('default', volume=0.4)
        else:
            self.e['Sounds'].play_music('default', volume=0.4)
             
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
                self.battle_manager.check_for_battle(current_room)
                
            self.battle_manager.update()
            self.battle_manager.render()
            self.battle_manager.handle_end_game()
            
            self.dialogue_manager.update()
            self.dialogue_manager.render()

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
        
        self.update_room_effects()
        
    def update_room_effects(self):
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