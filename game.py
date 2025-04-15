import pygame
import sys
import time
import scripts.pygpen as pp
from scripts.hooks import gen_hook
from scripts.player import Player
from scripts.spell_deck import SpellDeck
from scripts.systems.hud import HUD
from scripts.systems.room_system import RoomSystem
from scripts.systems.battle_system import BattleSystem
from scripts.systems.dialogue_system import DialogueSystem
from scripts.scene import PrologueScene

class Game(pp.PygpenGame):
    def load(self):
        self._init_pygame()
        self._create_surfaces()
        self._load_assets()
        self._setup_camera()
        self._init_game_state()
        self.reset()
    
    def _init_pygame(self):
        pp.init(
            (1020, 660),
            fps_cap=165,
            caption='Echo of Fallens',
            opengl=True,
            input_path='data/dbs/key_configs/config.json',
            spritesheet_path='data/images/spritesheets',
            entity_path='data/images/entities',
            font_path='data/fonts',
            frag_path='shaders/shader.frag',
            sounds_path='data/sounds',
            sound_filetype='mp3'
        )
    
    def _create_surfaces(self):
        self.bg_surf = pygame.Surface((340, 220), pygame.SRCALPHA)
        self.display = pygame.Surface((340, 220), pygame.SRCALPHA)
        self.ui_surf = pygame.Surface((340, 220), pygame.SRCALPHA)
    
    def _load_assets(self):
        self.e['Assets'].load_folder('data/images/scrolls', colorkey=(0, 0, 0))
        self.e['Assets'].load_folder('data/images/enemy', colorkey=(0, 0, 0))
        self.e['Renderer'].set_groups(['default', 'ui', 'background'])

        # try:
        #     if 'cards' in self.e['Assets'].images:
        #         self.e['Assets'].images['spells'] = self.e['Assets'].images['cards']
        # except:
        #     print("Warning: Could not create 'spells' asset alias")
    
    def _setup_camera(self):
        self.camera = pp.Camera(self.display.get_size(), slowness=0.3, pos=(5, 0))
    
    def _init_game_state(self):
        self.scene = 'prologue'
        self.player_deaths = 0
        self.scene_transition_timer = 0
        self.transition_duration = 2.0
        self.game_over_start_time = 0
        self.scene_transitioning = False
        self.deep_room_warning_shown = False
        self.next_scene = None

        self.player_chance = 8
        self.player_boss_chance_amp = 1
        self.available_spells = ["fire", "water", "earth"]
        self.available_bosses = ["mom_ghost", "father_ghost"]
    
    def load_systems(self):
        self.room_system = RoomSystem()
        self.spell_deck = SpellDeck()
        self.hud_system = HUD()
        self.battle_system = BattleSystem()
        self.dialogue_system = DialogueSystem()
        self.prologue = PrologueScene()
    
    def reset(self):
        self.load_systems()
        self._reset_game_state()
        self._init_player()
        self.e['Window'].start_transition()
        self.play_music()
    
    def _reset_game_state(self):
        self.tilemap = pp.Tilemap(tile_size=(16, 16))
        self.tilemap.load('data/dbs/rooms/spawn.pmap', spawn_hook=gen_hook())
        
        self.available_spells = ["fire", "water", "earth"]
        self.available_bosses = ["mom_ghost", "father_ghost"]
        
        self.player_chance = 1
        self.player_boss_chance_amp = 1
        
        self.scene_transitioning = False
        self.deep_room_warning_shown = False
    
    def _init_player(self):
        self.player = Player('player', (184, 110), room=self.room_system.current_room_id)
        self.e['EntityGroups'].add(self.player, 'entities')
        self.player_deaths += 1
        if hasattr(self.battle_system, 'player_die'):
            self.battle_system.player_die = False
        if self.player_deaths > 1:
            self.battle_system.handle_player_defeat()
        
    def play_music(self, track='default', volume=0.4):
        self.e['Sounds'].play_music(track, volume=volume)
             
    def start_scene_transition(self, next_scene):
        self.scene_transitioning = True
        self.scene_transition_timer = time.time()
        self.next_scene = next_scene
        self.e['Window'].e_start_transition()
    
    def update(self):
        self._clear_surfaces()
        current_time = time.time()
        self._handle_scene_transition(current_time)
        
        if self.scene == 'prologue':
            self._update_prologue()
        elif self.scene == 'game_over':
            self._update_game_over()
        elif self.scene in ['game', 'game_over_1', 'game_over_2']:
            self._update_gameplay(current_time)
        
        self._update_rendering()
        self._handle_inputs()
        self._update_window()
        self.update_room_effects()
    
    def _clear_surfaces(self):
        self.bg_surf.fill((22, 22, 22, 0))
        self.display.fill((0, 0, 0, 0))
        self.ui_surf.fill((0, 0, 0, 0))
    
    def _handle_scene_transition(self, current_time):
        if self.scene_transitioning and current_time - self.scene_transition_timer >= self.transition_duration:
            self.scene = self.next_scene
            self.scene_transitioning = False
            self.e['Window'].e_start_transition()
            
            if self.scene == 'game_over_2':
                self.room_system.update_tilemap(self.tilemap, '02')
    
    def _update_prologue(self):
        self.prologue.update()
        self.prologue.render()
    
    def _update_game_over(self):
        if hasattr(self, 'game_over_screen'):
            self.game_over_screen.update()
            self.game_over_screen.render()
    
    def _update_gameplay(self, current_time):
        if self.scene == 'game' and self.e['Sounds'].current_music != 'default':
            self.e['Sounds'].play_music('default', volume=0.3)
        
        self._update_camera_and_entities()
        self._render_room_info()
        self._update_hud()
        self._handle_room_objects()
        self._update_managers()
        
        if self.scene == 'game_over_1' and not self.scene_transitioning:
            if current_time - self.game_over_start_time >= 2.0:
                self.scene = 'game_over_2'
                self.start_scene_transition('game_over_2')
    
    def _update_camera_and_entities(self):
        self.camera.update()
        self.tilemap.renderz(
            pygame.Rect(
                self.camera[0] - 16, 
                self.camera[1] - 16,
                self.display.get_width() + 16, 
                self.display.get_height() + 16
            ),
            offset=self.camera
        )
        
        self.e['EntityGroups'].update()
        self.e['EntityGroups'].renderz(offset=self.camera)
    
    def _render_room_info(self):
        text = f"Room: {self.room_system.current_room_id}"
        self.e['Text']['small_font'].renderzb(
            text, (10, 10), 
            line_width=0,
            color=(255, 255, 255), 
            bgcolor=(40, 35, 40),
            group='ui'
        )
    
    def _update_hud(self):
        self.hud_system.update(self.spell_deck.spells)
        self.hud_system.render()
    
    def _handle_room_objects(self):
        current_room = self.room_system.rooms[self.room_system.current_room_id]
        
        if current_room.spell is not None:
            current_room.spell.render()
        
        if current_room.enemy is not None:
            current_room.enemy.render()
            self.battle_system.check_for_battle(current_room)
    
    def _update_managers(self):
        self.battle_system.update()
        self.battle_system.render()
        self.battle_system.handle_end_game()
        
        self.dialogue_system.update()
        self.dialogue_system.render()
    
    def _update_rendering(self):
        self.e['Renderer'].cycle({
            'default': self.display,
            'ui': self.ui_surf,
            'background': self.bg_surf
        })
    
    def _handle_inputs(self):
        if self.e['Input'].pressed('quit'):
            pygame.quit()
            sys.exit()
    
    def _update_window(self):
        self.e['Window'].cycle({
            'surface': self.display,
            'bg_surf': self.bg_surf,
            'ui_surf': self.ui_surf
        })
    
    def update_room_effects(self):
        room_coords = pp.game_math.convert_string_to_list(self.room_system.current_room_id)
        room = [abs(room_coords[0]), abs(room_coords[1])]
        room_sum = sum(room)

        self._check_deep_room_warning(room_sum)
        self._update_noise_level(room_sum)
    
    def _check_deep_room_warning(self, room_sum):
        if (room_sum > 10 and 
            not self.deep_room_warning_shown and 
            not self.dialogue_system.active and 
            len(self.spell_deck.spells) == 3):
            self.dialogue_system.show_center_text()
            self.deep_room_warning_shown = True
    
    def _update_noise_level(self, room_sum):
        if room_sum > 10:
            target_gain = ((room_sum - 10) * 3) / 10 + 1
            current_gain = self.e['Window'].noise_gain
            self.e['Window'].noise_gain = current_gain + (target_gain - current_gain) * 0.1

if __name__ == "__main__":
    Game().run()