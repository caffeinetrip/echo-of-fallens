import time

import pygame

from ..utils.elements import Element

class TextInputBuffer:
    def __init__(self, text='', parent=None):
        self.text = text
        self.cursor = 0
        self.parent = parent
    
    def insert(self, chars):
        self.text = self.text[:self.cursor] + chars + self.text[self.cursor:]
        self.cursor += len(chars)
    
    def delete(self, all=False):
        if all:
            self.text = ''
            self.cursor = 0
        else:
            self.text = self.text[:max(self.cursor - 1, 0)] + self.text[self.cursor:]
            self.cursor = max(0, self.cursor - 1)
    
    def enter(self):
        if self.parent:
            self.parent.enter()

class Textbox(Element):
    def __init__(self, font, width, color=(255, 255, 255), return_event=None, show_cursor=True, autoclear=False):
        super().__init__()
        self.buffer = TextInputBuffer(parent=self)
        try:
            self.font = self.e['Text'][font]
        except KeyError:
            self.font = None
        self.width = width
        self.height = self.font.line_height
        self.color = color
        self.return_event = return_event
        self.show_cursor = show_cursor
        self.autoclear = autoclear
        
    @property
    def bound(self):
        return self.e['Input'].text_buffer == self.buffer
    
    def bind(self):
        self.e['Input'].set_text_buffer(self.buffer)
        
    def unbind(self):
        self.e['Input'].set_text_buffer()
        
    def enter(self):
        self.unbind()
        if self.return_event:
            self.return_event(self.buffer)
        if self.autoclear:
            self.buffer.delete(all=True)
    
    @property
    def surf(self):
        text_width = self.font.width(self.buffer.text)
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        offset = min(0, -(text_width - (self.width - 2)))
        self.font.render(surf, self.buffer.text, (offset, 0), color=self.color)
        if (self.e['Window'].time % 1 < 0.6) and self.bound:
            pygame.draw.line(surf, self.color, (offset + text_width + 1, 0), (offset + text_width + 1, surf.get_height()))
        return surf
    
        