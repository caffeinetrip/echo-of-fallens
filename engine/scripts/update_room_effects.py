
import engine.pygpen as pp

class update_room_effects(pp.GameScript):
    def __init__(self):
        super().__init__()
        self.deep_room_warning_shown = False
    
    def on_update(self):
        room_coords = pp.game_math.convert_string_to_list(self.e['RoomSystem'].current_room_id)
        room_depth = abs(room_coords[0]) + abs(room_coords[1])
        
        if (room_depth > 10 and 
            not self.deep_room_warning_shown and 
            not self.e['DialogueSystem'].active and 
            len(self.e['SpellDeck'].spells) == 3):
            self.e['DialogueSystem'].show_center_text()
            self.deep_room_warning_shown = True
        
        if room_depth > 10:
            target_gain = ((room_depth - 10) * 3) / 10 + 1
            current_gain = self.e['Window'].noise_gain
            self.e['Window'].noise_gain = current_gain + (target_gain - current_gain) * 0.1