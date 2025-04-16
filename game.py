import pygame
import sys
import time
from enum import Enum

import scripts.pygpen as pp
from scripts.hooks import gen_hook
from scripts.player import Player
from scripts.spell_deck import SpellDeck
from scripts.systems.hud import HUD
from scripts.systems.room_system import RoomSystem
from scripts.systems.battle_system import BattleSystem
from scripts.systems.dialogue_system import DialogueSystem
from scripts.systems.game_state_system import GameStateSystem
from scripts.scene import PrologueScene

WINDOW_SIZE = (1020, 660)
DISPLAY_SIZE = (340, 220)
TILE_SIZE = (16, 16)
DEFAULT_SPELLS = ["fire", "water", "earth"]
DEFAULT_BOSSES = ["mom_ghost", "father_ghost"]


class Game(pp.PygpenGame):
    def load(self):
        pp.init(
            WINDOW_SIZE, fps_cap=165, caption='Echo of Fallens', opengl=True,
            input_path='data/dbs/key_configs/config.json',
            spritesheet_path='data/images/spritesheets',
            entity_path='data/images/entities',
            font_path='data/fonts',
            frag_path='shaders/shader.frag',
            sounds_path='data/sounds',
            sound_filetype='mp3'
        )
        
        self.bg_surf = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)
        self.display = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)
        self.ui_surf = pygame.Surface(DISPLAY_SIZE, pygame.SRCALPHA)
        
        self.e['Assets'].load_folder('data/images/scrolls', colorkey=(0, 0, 0))
        self.e['Assets'].load_folder('data/images/enemy', colorkey=(0, 0, 0))
        self.e['Renderer'].set_groups(['default', 'ui', 'background'])
        
        self.camera = pp.Camera(DISPLAY_SIZE, slowness=0.3, pos=(5, 0))
        
        self._init_state()
        self.reset()
    
    def _init_state(self):
        self.player_chance = 8
        self.player_boss_chance_amp = 1
        self.available_spells = DEFAULT_SPELLS.copy()
        self.available_bosses = DEFAULT_BOSSES.copy()
        self.deep_room_warning_shown = False
        self.last_update_time = time.time()
    
    def load_systems(self):
        self.room_system = RoomSystem()
        self.spell_deck = SpellDeck()
        self.hud_system = HUD()
        self.battle_system = BattleSystem()
        self.dialogue_system = DialogueSystem()
        self.gamestate_system = GameStateSystem()
        self.prologue = PrologueScene()
    
    def reset(self):
        self.load_systems()
        
        self.tilemap = pp.Tilemap(tile_size=TILE_SIZE)
        self.tilemap.load('data/dbs/rooms/spawn.pmap', spawn_hook=gen_hook())
        self.player_chance = 1
        self.player_boss_chance_amp = 1
        self.available_spells = DEFAULT_SPELLS.copy()
        self.available_bosses = DEFAULT_BOSSES.copy()
        self.deep_room_warning_shown = False
        
        self.player = Player('player', (184, 110), room=self.room_system.current_room_id)
        self.e['EntityGroups'].add(self.player, 'entities')
        self.gamestate_system.player_deaths += 1
        
        if hasattr(self.battle_system, 'player_die'):
            self.battle_system.player_die = False
        
        if self.gamestate_system.player_deaths > 1:
            self.battle_system.handle_player_defeat()
        
        self.e['Window'].start_transition()
        self.e['Sounds'].play_music('default', volume=0.4)
    
    def update(self):
        current_time = time.time()
        self.last_update_time = current_time
        
        self.bg_surf.fill((22, 22, 22, 0))
        self.display.fill((0, 0, 0, 0))
        self.ui_surf.fill((0, 0, 0, 0))
        
        self.gamestate_system.update(current_time)
        
        if self.gamestate_system.is_in_prologue():
            self.prologue.update()
            self.prologue.render()
        elif self.gamestate_system.is_in_gameplay():
            self._update_gameplay()
        
        self.e['Renderer'].cycle({
            'default': self.display,
            'ui': self.ui_surf,
            'background': self.bg_surf
        })
        
        if self.e['Input'].pressed('quit'):
            pygame.quit()
            sys.exit()
        
        self.e['Window'].cycle({
            'surface': self.display,
            'bg_surf': self.bg_surf,
            'ui_surf': self.ui_surf
        })
        
        self._update_room_effects()
    
    def _update_gameplay(self):
        game_state = self.gamestate_system
        
        if game_state.scene == 'game' and self.e['Sounds'].current_music != 'default':
            self.e['Sounds'].play_music('default', volume=0.3)
        
        self.camera.update()
        visible_rect = pygame.Rect(
            self.camera[0] - 16, 
            self.camera[1] - 16,
            self.display.get_width() + 32, 
            self.display.get_height() + 32
        )
        self.tilemap.renderz(visible_rect, offset=self.camera)
        
        self.e['EntityGroups'].update()
        self.e['EntityGroups'].renderz(offset=self.camera)
        
        self.e['Text']['small_font'].renderzb(
            f"Room: {self.room_system.current_room_id}", 
            (10, 10), 
            line_width=0,
            color=(255, 255, 255), 
            bgcolor=(40, 35, 40),
            group='ui'
        )

        self.hud_system.update(self.spell_deck.spells)
        self.hud_system.render()
        
        current_room = self.room_system.rooms[self.room_system.current_room_id]
        if current_room.spell is not None:
            current_room.spell.render()
        
        if current_room.enemy is not None:
            current_room.enemy.render()
            self.battle_system.check_for_battle(current_room)

        self.battle_system.update()
        self.battle_system.render()
        self.battle_system.handle_end_game()
        
        self.dialogue_system.update()
        self.dialogue_system.render()
    
    def _update_room_effects(self):
        room_coords = pp.game_math.convert_string_to_list(self.room_system.current_room_id)
        room_depth = abs(room_coords[0]) + abs(room_coords[1])
        
        if (room_depth > 10 and 
            not self.deep_room_warning_shown and 
            not self.dialogue_system.active and 
            len(self.spell_deck.spells) == 3):
            self.dialogue_system.show_center_text()
            self.deep_room_warning_shown = True
        
        if room_depth > 10:
            target_gain = ((room_depth - 10) * 3) / 10 + 1
            current_gain = self.e['Window'].noise_gain
            self.e['Window'].noise_gain = current_gain + (target_gain - current_gain) * 0.1


if __name__ == "__main__":
    Game().run()