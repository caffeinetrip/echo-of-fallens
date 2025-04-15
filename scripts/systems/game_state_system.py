import time
import scripts.pygpen as pp

class GameStateSystem(pp.ElementSingleton):
    def __init__(self, custom_id=None):
        super().__init__(custom_id)
        self.scene = 'prologue'
        self.player_deaths = 0
        
        self.scene_transition_timer = 0
        self.transition_duration = 2.0
        self.game_over_start_time = 0
        self.scene_transitioning = False
        self.next_scene = None
    
    def start_scene_transition(self, next_scene):
        self.scene_transitioning = True
        self.scene_transition_timer = time.time()
        self.next_scene = next_scene
        self.e['Window'].e_start_transition()
    
    def update(self, current_time):
        if self.scene_transitioning and current_time - self.scene_transition_timer >= self.transition_duration:
            self.scene = self.next_scene
            self.scene_transitioning = False
            self.e['Window'].e_start_transition()
            
            if self.scene == 'game_over_2':
                self.e['Game'].room_manager.update_tilemap(self.e['Game'].tilemap, '02')
        
        if self.scene == 'game_over_1' and not self.scene_transitioning:
            if current_time - self.game_over_start_time >= 2.0:
                self.scene = 'game_over_2'
                self.start_scene_transition('game_over_2')
    
    def is_in_prologue(self):
        return self.scene == 'prologue'
    
    def is_in_game_over(self):
        return self.scene == 'game_over'
    
    def is_in_gameplay(self):
        return self.scene in ['game', 'game_over_1', 'game_over_2']