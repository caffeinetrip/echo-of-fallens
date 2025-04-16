import pygame
from .. import pygpen as pp

class SpellSlot(pp.Element):
    def __init__(self, position, index):
        super().__init__(f'spell_slot_{index}')
        self.position = position
        self.index = index
        self.spell = None
        self.is_selected = False

    def render(self):
        slot_pos = (self.position[0], self.position[1])
        self.e['Renderer'].blit(self.e['Assets'].images['scrolls']['slot'], slot_pos, group='ui')
        if self.spell:
            spell_pos = (self.position[0]+1, self.position[1]+1)
            spell_img = self._get_spell_image()
            self.e['Renderer'].blit(
                pygame.transform.scale(
                    pygame.transform.flip(spell_img, False, True), 
                    (14,14)
                ), 
                spell_pos, 
                group='ui'
            )
    
    def _get_spell_image(self):
        if hasattr(self.spell, 'img'):
            return self.spell.img

        try:
            return self.e['Assets'].images['scrolls'][self.spell.type]
        except:
            return pygame.Surface((14, 14), pygame.SRCALPHA)

    def set_spell(self, spell):
        self.spell = spell

    def clear(self):
        self.spell = None
        self.is_selected = False
