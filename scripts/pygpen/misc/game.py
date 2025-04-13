import sys

import pygame

from ..utils.elements import ElementSingleton

class PygpenGame(ElementSingleton):
    def __init__(self):
        super().__init__()
        
    def load(self):
        pass
    
    def update(self):
        pass
    
    def run(self):
        self.load()
        while True:
            self.update()
            
    def quit(self):
        pygame.quit()
        sys.exit()
