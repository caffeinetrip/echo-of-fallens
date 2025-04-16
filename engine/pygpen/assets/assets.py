from ..utils.io import read_tjson
from ..utils.elements import ElementSingleton
from ..ui.boxer import UIBoxer
from ..vfx.foliage import FoliageAssets
from ..vfx.water import WaterManager
from .spritesheets import load_spritesheets
from .asset_utils import load_img_directory

class Assets(ElementSingleton):
    def __init__(self, spritesheet_path=None, colorkey=(0, 0, 0)):
        super().__init__()
        self.spritesheet_path = spritesheet_path
        self.spritesheets = load_spritesheets(spritesheet_path, colorkey=colorkey) if spritesheet_path else {}
        self.autotile_config = self.parse_autotile_config(read_tjson(spritesheet_path + '/autotile.json')) if spritesheet_path else {}
        self.boxer = UIBoxer()
        self.foliage = FoliageAssets()
        self.water = WaterManager()
        self.foliage.load()
        self.custom_tile_renderers = {}
        self.images = {}
        
    def load_folder(self, path, alpha=False, colorkey=None):
        self.images[path.split('/')[-1]] = load_img_directory(path, alpha=alpha, colorkey=colorkey)
    
    def enable(self, *args, **kwargs):
        if 'foliage' in args:
            self.custom_tile_renderers.update(self.foliage.render_functions())
        if ('boxer' in args) and ('box_path' in kwargs):
            self.boxer.load(kwargs['box_path'])
        if ('water' in args) and ('water_group' in kwargs):
            spacing = kwargs['water_spacing'] if 'water_spacing' in kwargs else 2
            self.custom_tile_renderers.update(self.water.render_functions(kwargs['water_group'], spacing=spacing))

    def parse_autotile_config(self, config):
        checks = {}
        for mapping in config['mappings']:
            checks[mapping] = []
            for offset in config['mappings'][mapping]:
                if type(config['mappings'][mapping][offset]) != str:
                    for check in config['mappings'][mapping][offset]:
                        checks[mapping].append(tuple(check[:2]))
            checks[mapping] = list(set(checks[mapping]))
        config['checks'] = checks
        return config