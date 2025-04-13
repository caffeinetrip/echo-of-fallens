import sys

import pygame

from ..utils.elements import ElementSingleton, Element
from ..utils.gfx import palette_swap, clip
from ..utils.io import recursive_file_op

def load_font_img(path, font_color=(255, 255, 255)):
    fg_color = (255, 0, 0)
    bg_color = (0, 0, 0)
    font_img = pygame.image.load(path).convert_alpha()
    font_img = palette_swap(font_img, {fg_color: font_color})
    last_x = 0
    letters = []
    letter_spacing = []
    for x in range(font_img.get_width()):
        if font_img.get_at((x, 0))[0] == 127:
            letters.append(clip(font_img, pygame.Rect(last_x, 0, x - last_x, font_img.get_height())))
            letter_spacing.append(x - last_x)
            last_x = x + 1
        x += 1
    for letter in letters:
        letter.set_colorkey(bg_color)
    return letters, letter_spacing, font_img.get_height()

class Text(ElementSingleton):
    def __init__(self, path=None):
        super().__init__()
        self.path = path
        self.fonts = {}
        self.load()
        
    def load(self, path=None):
        if path:
            self.path = path
        if self.path:
            self.fonts = recursive_file_op(self.path, Font, filetype='png')
        
    def __getitem__(self, key):
        return self.fonts[key]

class PreppedText:
    def __init__(self, text, size, font):
        self.font = font
        self.text = text
        self.width = size[0]
        self.height = size[1]
        self.size = size

    # maybe add caching?
    def render(self, surf, loc):
        self.font.render(self.text, surf, loc)

    def __repr__(self):
        return ('<PreppedText:' + str(self.width) + 'x' + str(self.height) + '> ' + self.text).replace('\n', '\\n')

    def __str__(self):
        return ('<PreppedText:' + str(self.width) + 'x' + str(self.height) + '> ' + self.text).replace('\n', '\\n')

class Font(Element):
    def __init__(self, path, color=(255, 255, 255)):
        super().__init__()
        self.base_color = color
        self.letters, self.letter_spacing, self.line_height = load_font_img(path, color)
        self.color_cache = {color: self.letters}
        self.font_order = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','a','b','c','d','e','f','g','h','i','j','k','l','m','n','o','p','q','r','s','t','u','v','w','x','y','z','.','-',',',':','+','\'','!','?','0','1','2','3','4','5','6','7','8','9','(',')','/','_','=','\\','[',']','*','"','<','>',';','%']
        self.font_map = {k: i for i, k in enumerate(self.font_order)}
        self.space_width = self.letter_spacing[0]
        self.base_spacing = 1
        self.line_spacing = 2
        
    def prep_color(self, color):
        new_letters = []
        for img in self.letters:
            if len(color) > 3:
                img.convert_alpha()
            new_letters.append(palette_swap(img, {self.base_color: color}))
        self.color_cache[color] = new_letters

    def width(self, text):
        text_width = 0
        for char in text:
            if char == ' ':
                text_width += self.space_width + self.base_spacing
            else:
                text_width += self.letter_spacing[self.font_order.index(char)] + self.base_spacing
        return text_width

    def prep_text(self, text, line_width=0):
        if not line_width:
            return PreppedText(text, (self.width(text), self.line_height), self)

        words = []
        word_width = 0
        word = ''
        for i, char in enumerate(text):
            if char not in ['\n', ' ']:
                word_width += self.letter_spacing[self.font_order.index(char)] + self.base_spacing
                word += char
            else:
                words.append((word, word_width))
                words.append((char, self.space_width + self.base_spacing if char == ' ' else 0))
                word = ''
                word_width = 0
        if word != '':
            words.append((word, word_width))

        x = 0
        y = 0
        processed_text = ''
        max_width = 0
        for word in words:
            if word[0] == '\n':
                y += 1
                x = 0
            else:
                if x + word[1] > line_width:
                    processed_text += '\n'
                    x = 0 if word[0] == ' ' else word[1]
                    y += 1
                else:
                    x += word[1]
                if (word[0] != ' ') or (x != 0):
                    processed_text += word[0]
                max_width = max(max_width, x)

        return PreppedText(processed_text, (max_width, self.line_height + (self.line_height + self.line_spacing) * y), self)
    
    def renderz(self, text, loc, line_width=0, color=None, offset=(0, 0), group='default', z=0):
        self.render(self.e['Renderer'], text, (loc[0] - offset[0], loc[1] - offset[1]), line_width=line_width, color=color, blit_kwargs={'group': group, 'z': z})
    
    def renderzb(self, text, loc, line_width=0, color=None, bgcolor=None, offset=(0, 0), group='default', z=0, hide_chars=0):
        for o in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            self.renderz(text, (loc[0] + o[0], loc[1] + o[1]), line_width=line_width, color=bgcolor, offset=offset, group=group, z=z - 1)
        self.renderz(text, loc, line_width=line_width, color=color, offset=offset, group=group, z=z)

    def render(self, surf, text, loc, line_width=0, color=None, blit_kwargs={}):
        if not color:
            color = self.base_color
        if color not in self.color_cache:
            self.prep_color(color)
        letters = self.color_cache[color]
        x_offset = 0
        y_offset = 0
        if line_width != 0:
            spaces = []
            x = 0
            for i, char in enumerate(text):
                if char == '\n':
                    continue
                if char == ' ':
                    spaces.append((x, i))
                    x += self.space_width + self.base_spacing
                else:
                    x += self.letter_spacing[self.font_map[char]] + self.base_spacing
            line_offset = 0
            for i, space in enumerate(spaces):
                if (space[0] - line_offset) > line_width:
                    line_offset += spaces[i - 1][0] - line_offset
                    if i != 0:
                        text = text[:spaces[i - 1][1]] + '\n' + text[spaces[i - 1][1] + 1:]
        for char in text:
            if char not in ['\n', ' ']:
                surf.blit(letters[self.font_map[char]], (loc[0] + x_offset, loc[1] + y_offset), **blit_kwargs)
                x_offset += self.letter_spacing[self.font_map[char]] + self.base_spacing
            elif char == ' ':
                x_offset += self.space_width + self.base_spacing
            else:
                y_offset += self.line_spacing + self.line_height
                x_offset = 0
