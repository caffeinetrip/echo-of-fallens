import math, pygame
import scripts.pygpen as pp
from scripts.spells.fire import Fire
from scripts.spells.water import Water
from scripts.spells.earth import Earth
from scripts.spells.dark import Dark

spells = {
    'fire': Fire(),
    'water': Water(),
    'earth': Earth(),
    'dark': Dark()
}

class Spell(pp.Element):
    def __init__(self, type, rarity):
        super().__init__(type)
        self.type = type
        self.rarity = rarity
        self.player_offset = 0
        self.kd = 2
        self.kd_now = 0
    
    @property
    def spell(self):
        return spells[self.type]
    
    @property
    def img(self):
        try:
            return self.e['Assets'].images['cards'][self.type]
        except (KeyError, AttributeError):
            print(f"Warning: could not load image for spell type '{self.type}'")
            return pygame.Surface((16, 16), pygame.SRCALPHA)
    
    def render(self):
        y_offset = math.sin(2 * self.e['Window'].time) * 2 - self.player_offset
        
        if self.e['Game'].player.action == 'idle':
            if self.player_offset < 15:
                self.player_offset += 0.3
            else:
                text = f"Press E to collect"
                self.e['Text']['small_font'].renderzb(
                    text, (145, 130+y_offset), 
                    line_width=0, 
                    color=(255, 255, 255), 
                    bgcolor=(40, 35, 40), 
                    group='ui'
                )
                
            if self.e['Input'].pressed('action'):
                if hasattr(self.e['Game'], 'spell_deck'):
                    self.e['Game'].spell_deck.spells.append(self)
                    self.e['Sounds'].play('equip', 0.25)
                    if self.e['RoomManager'].current_room_id in self.e['RoomManager'].rooms:
                        self.e['RoomManager'].rooms[self.e['RoomManager'].current_room_id].spell = None
                
        if self.e['Game'].player.action != 'idle' and self.player_offset > 0:
            self.player_offset -= 0.5
            
        self.e['Renderer'].blit(self.img, (170, 150+y_offset), group='ui')