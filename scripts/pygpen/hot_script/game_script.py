
from ..utils.elements import Element

class GameScript(Element):
    is_game_script = True
    
    def __init__(self):
        self.active = True
    
    def update(self):
        if self.active:
            self.on_update()
    
    def on_update(self):
        pass
    
    def activate(self):
        self.active = True
    
    def deactivate(self):
        self.active = False