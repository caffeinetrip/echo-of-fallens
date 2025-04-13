import random
import scripts.pygpen as pp
from scripts.cards import Card

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
        self.rm = self.e['RoomManager']
        self.card = None
        self.enemy = None
        
        if self.e['Game'].player_chance == 50:
            self.e['Game'].player_chance = 8
            self.e['Game'].player_boss_chance_amp = 0.5
        elif self.e['Game'].player_chance > 2:
            self.e['Game'].player_chance -= 1
        
        if room_id == "0,0":
            self.ways['left'] = True
            self.ways['right'] = True
            self.enemy = self.e['RoomManager'].bosses['main_boss']
            
        else:
            if len(self.e['Game'].avalible_spells) != 0:
                if random.randint(1,self.e['Game'].player_chance) == 1:
                    self.card = Card(random.choice(self.e['Game'].avalible_spells), 1)
                    self.e['Game'].avalible_spells.remove(self.card.type)
                    self.e['Game'].player_chance = 50
                    
            available_directions = ['left', 'left', 'right', 'right', 'up', 'down', 'down', 'down']
            num_ways = random.randint(2, 3)
            for _ in range(num_ways):
                if available_directions:
                    direction = random.choice(available_directions)
                    self.ways[direction] = True
                    
                    available_directions = [item for item in available_directions if
                                            item != direction]
            
            room_id_list = pp.game_math.convert_string_to_list(room_id)
            
            if room_id_list[0] == -1 and room_id_list[1] < 0 and 'right' in self.ways:
                self.ways['right'] = False
            elif room_id_list[0] == 1 and room_id_list[1] < 0 and 'left' in self.ways:
                self.ways['left'] = False
            elif room_id == "0,1" and 'up' in self.ways:
                self.ways['up'] = False
                
            elif room_id_list[0] == -1 and room_id_list[1] == 0:
                self.ways['down'] = True
                self.ways['right'] = True
            elif room_id_list[0] == 1 and room_id_list[1] == 0:
                self.ways['down'] = True
                self.ways['left'] = True
            if len(self.e['Game'].avalible_bosses) != 0 and self.card == None and sum([abs(room_id_list[0]), abs(room_id_list[1])]) > 1:
                if random.randint(1, int(max(2*self.e['Game'].player_boss_chance_amp, 1))) == 1:
                    self.enemy = self.e['RoomManager'].bosses[random.choice(self.e['Game'].avalible_bosses)]
                    self.e['Game'].avalible_bosses.remove(self.enemy.type)
                    self.e['Game'].player_boss_chance_amp = 2
                
            self.update_adjacent_rooms() 
            
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