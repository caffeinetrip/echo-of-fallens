import scripts.pygpen as pp
from scripts.room import Room
from scripts.enemy import main_boss, mom_ghost, father_ghost

name_index = ['left', 'right', 'top', 'down']

class RoomSystem(pp.ElementSingleton):
    def __init__(self, custom_id=None):
        super().__init__(custom_id)
        self.reset()
        
    @property
    def bosses(self):
        return {
            'main_boss': main_boss,
            'mom_ghost': mom_ghost,
            'father_ghost': father_ghost
        }
    
    def reset(self):
        self.current_room_id = "0,0"
        self.rooms = {}
        self.room_transitions = {
            'left': (-1, 0),
            'right': (1, 0),
            'up': (0, -1),
            'down': (0, 1)
        }
        self.get_or_create_room(self.current_room_id)
    
    def get_or_create_room(self, room_id):
        if room_id not in self.rooms:
            self.rooms[room_id] = Room(room_id=room_id)
        return self.rooms[room_id]
    
    def move_to_room(self, direction, tilemap):
        if not self.rooms[self.current_room_id].ways[direction]:
            return False
        
        x, y = self.room_position(self.current_room_id)
        dx, dy = self.room_transitions[direction]
        new_x, new_y = x + dx, y + dy
        new_room_id = f"{new_x},{new_y}"
        
        new_room = self.get_or_create_room(new_room_id)
        
        opposite_directions = {
            'left': 'right',
            'right': 'left',
            'up': 'down',
            'down': 'up'
        }
        
        new_room.ways[opposite_directions[direction]] = True
        
        for adj_dir, (adj_dx, adj_dy) in self.room_transitions.items():
            if not new_room.ways[adj_dir]:
                continue
                
            adj_x, adj_y = new_x + adj_dx, new_y + adj_dy
            adj_room_id = f"{adj_x},{adj_y}"
            
            if adj_room_id in self.rooms and adj_room_id != self.current_room_id:
                self.rooms[adj_room_id].ways[opposite_directions[adj_dir]] = True
        
        self.current_room_id = new_room_id
        self.update_tilemap(tilemap, new_room_id)
        return True
    
    def update_tilemap(self, tilemap, room_id):
        if self.e['Game'].scene == 'game_over_1':
            tilemap_name = '01.pmap'
        elif self.e['Game'].scene == 'game_over_2':
            tilemap_name = '02.pmap'
        elif room_id != "0,0":
            room = self.rooms[room_id]
            directions = []
            
            for name, val in room.ways.items():
                if val:
                    if name == 'up':
                        directions.append('top')
                    else:
                        directions.append(name)
            
            if directions:
                tilemap_name = ""
                for d in name_index:
                    if d in directions:
                        tilemap_name += d + "_"
                        directions.remove(d)
                tilemap_name = tilemap_name[:-1]+'.pmap'
            else:
                tilemap_name = 'spawn.pmap'
        else:
            tilemap_name = 'spawn.pmap'
            
        tilemap.load(f"data/dbs/rooms/{tilemap_name}")
    
    def room_position(self, room_id):
        x, y = map(int, room_id.split(','))
        return (x, y)
    
    def position_to_room_id(self, x, y):
        return f"{x},{y}"