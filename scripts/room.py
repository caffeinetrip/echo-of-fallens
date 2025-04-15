import random
import scripts.pygpen as pp
from scripts.spell import Spell

class Room(pp.Element):
    def __init__(self, custom_id=None, singleton=False, register=False, room_id="0,0"):
        super().__init__(custom_id, singleton, register)
        self.room_id = room_id
        self.ways = {
            'left': False,
            'right': False,
            'down': False,
            'up': False
        }
        self.rm = self.e['RoomSystem']
        self.spell = None
        self.enemy = None
        
        self._initialize_room()
    
    def _initialize_room(self):
        self._adjust_player_chance()
        
        if self.room_id == "0,0":
            self._setup_starting_room()
        else:
            self._setup_random_room()
    
    def _adjust_player_chance(self):
        game = self.e['Game']
        if not hasattr(game, 'player_chance'):
            game.player_chance = 8 
            
        if not hasattr(game, 'player_boss_chance_amp'):
            game.player_boss_chance_amp = 1 
            
        if game.player_chance == 50:
            game.player_chance = 8
            game.player_boss_chance_amp = 0.5
        elif game.player_chance > 2:
            game.player_chance -= 1
    
    def _setup_starting_room(self):
        self.ways['left'] = True
        self.ways['right'] = True
        self.enemy = self.e['RoomSystem'].bosses['main_boss']
    
    def _setup_random_room(self):
        self._try_place_spell()
        self._setup_room_ways()
        self._adjust_ways_by_position()
        self._try_place_enemy()
        self.update_adjacent_rooms()
    
    def _try_place_spell(self):
        game = self.e['Game']
        if not hasattr(game, 'available_spells'):
            game.available_spells = ["fire", "water", "earth"]
            
        if len(game.available_spells) != 0:
            if random.randint(1, game.player_chance) == 1:
                spell_type = random.choice(game.available_spells)
                self.spell = Spell(spell_type, 1)
                game.available_spells.remove(spell_type)
                game.player_chance = 50
    
    def _setup_room_ways(self):
        available_directions = ['left', 'left', 'right', 'right', 'up', 'down', 'down', 'down']
        num_ways = random.randint(2, 3)
        for _ in range(num_ways):
            if available_directions:
                direction = random.choice(available_directions)
                self.ways[direction] = True
                available_directions = [item for item in available_directions if item != direction]
    
    def _adjust_ways_by_position(self):
        room_id_list = pp.game_math.convert_string_to_list(self.room_id)
        
        if room_id_list[0] == -1 and room_id_list[1] < 0 and 'right' in self.ways:
            self.ways['right'] = False
        elif room_id_list[0] == 1 and room_id_list[1] < 0 and 'left' in self.ways:
            self.ways['left'] = False
        elif self.room_id == "0,1" and 'up' in self.ways:
            self.ways['up'] = False
        elif room_id_list[0] == -1 and room_id_list[1] == 0:
            self.ways['down'] = True
            self.ways['right'] = True
        elif room_id_list[0] == 1 and room_id_list[1] == 0:
            self.ways['down'] = True
            self.ways['left'] = True
    
    def _try_place_enemy(self):
        game = self.e['Game']
        if not hasattr(game, 'available_bosses'):
            game.available_bosses = ["mom_ghost", "father_ghost"]
            
        room_id_list = pp.game_math.convert_string_to_list(self.room_id)
        
        if (len(game.available_bosses) != 0 and 
            self.spell is None and 
            sum([abs(room_id_list[0]), abs(room_id_list[1])]) > 1):
            
            if random.randint(1, int(max(2*game.player_boss_chance_amp, 1))) == 1:
                enemy_type = random.choice(game.available_bosses)
                self.enemy = self.e['RoomSystem'].bosses[enemy_type]
                game.available_bosses.remove(enemy_type)
                game.player_boss_chance_amp = 2
    
    def detect_ways(self):
        return self.ways
    
    def update_adjacent_rooms(self):
        room_id_list = pp.game_math.convert_string_to_list(self.room_id)
        
        for direction, is_open in self.ways.items():
            if not is_open:
                continue
                
            adj_coords = room_id_list.copy()
            opposite_dir = ""
            
            if direction == 'left':
                adj_coords[0] -= 1
                opposite_dir = 'right'
            elif direction == 'right':
                adj_coords[0] += 1
                opposite_dir = 'left'
            elif direction == 'up':
                adj_coords[1] -= 1
                opposite_dir = 'down'
            elif direction == 'down':
                adj_coords[1] += 1
                opposite_dir = 'up'
            
            adj_room_id = f"{adj_coords[0]},{adj_coords[1]}"
            
            if adj_room_id in self.rm.rooms:
                self.rm.rooms[adj_room_id].ways[opposite_dir] = True