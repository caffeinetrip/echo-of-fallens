import pygame

from ..utils.io import recursive_file_op

def load_img(path, alpha=False, colorkey=None):
    if alpha:
        img = pygame.image.load(path).convert_alpha()
    else:
        img = pygame.image.load(path).convert()
    if colorkey:
        img.set_colorkey(colorkey)
    return img

def load_img_directory(path, alpha=False, colorkey=None):
    return recursive_file_op(path, lambda x: load_img(x, alpha=alpha, colorkey=colorkey), filetype='png')