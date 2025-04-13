import os

import pygame

from ..utils.elements import ElementSingleton
from ..utils.io import read_json, write_json
from ..assets.asset_utils import load_img_directory
from ..assets.animation import Animation

class EntityData:
    def __init__(self, config, animations=None):
        self.config = config
        self.assets = load_img_directory(self.config['file_path'], colorkey=self.config['colorkey'])
        self.animations = {}
        for animation in self.config['animations']:
            if animation in self.assets:
                frame1_name = list(self.assets[animation])[0]
                frame_i = frame1_name.split('_')[-1]
                if len(frame_i) and frame_i.isnumeric():
                    frame_names = [(int(frame_name.split('_')[-1]), '_'.join(frame_name.split('_')[:-1])) for frame_name in self.assets[animation] if frame_name.split('_')[-1].isnumeric()]
                    frame_names.sort()
                    frame_names = [frame_name[1] + ('_' if len(frame_name[1]) else '') + str(frame_name[0]) for frame_name in frame_names]
                    animation_images = [self.assets[animation][frame_name] for frame_name in frame_names if type(self.assets[animation][frame_name]) == pygame.Surface]
                else:
                    animation_images = [img for img in self.assets[animation].values() if type(img) == pygame.Surface]
                self.animations[animation] = Animation(animation_images, config=self.config['animations'][animation])

class EntityDB(ElementSingleton):
    def __init__(self, path=None):
        super().__init__()
        self.path = path
        self.configs = {}
        if path:
            self.load(path)
        
    def load(self, path):
        self.path = path
        self.generate_configs()
        
    def __getitem__(self, key):
        if key in self.configs:
            return self.configs[key]
        else:
            return None
    
    def generate_configs(self):
        for entity in os.listdir(self.path):
            animations = []
            images = []
            config = {'images': {}, 'animations': {}, 'file_path': self.path + '/' + entity, 'id': entity, 'centered': False, 'offset': [0, 0], 'colorkey': [0, 0, 0],
                      'size': [1, 1], 'group': 'entity', 'collide_with': [], 'default': None}
            for file in os.listdir(self.path + '/' + entity):
                if file.find('.') == -1:
                    animations.append(file)
                elif file.split('.')[-1] == 'png':
                    images.append(file.split('.')[0])
                if file == 'config.json':
                    config = read_json(self.path + '/' + entity + '/' + file)
                    
            for image in images:
                if image not in config['images']:
                    config['images'][image] = {'offset': [0, 0]}
                    
            for animation in animations:
                if animation not in config['animations']:
                    frames = os.listdir(self.path + '/' + entity + '/' + animation)
                    config['animations'][animation] = {'offset': [0, 0], 'speed': 1.0, 'loop': True, 'paused': False, 'frames': []}
                    for frame in frames:
                        if frame.split('.')[-1] == 'png':
                            config['animations'][animation]['frames'].append(0.1)
            
            if not config['default']:
                if len(animations):
                    config['default'] = animations[0]
                elif len(images):
                    config['default'] = images[0]
            
            write_json(self.path + '/' + entity + '/config.json', config)
            self.configs[config['id']] = EntityData(config)
