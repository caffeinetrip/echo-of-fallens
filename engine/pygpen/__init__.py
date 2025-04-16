from . import entities
from . import vfx
from . import data_structures as ds
from .utils import game_math
from .utils.elements import elems, Element, ElementSingleton
from .utils import gfx as gfx_util
from .utils import io as io
from .assets.assets import Assets
from .entities.entity import Entity, PhysicsEntity
from .hot_script.game_script import GameScript
from .entities.entity_db import EntityDB
from .entities.entity_groups import EntityGroups
from .misc.game import PygpenGame
from .misc.window import Window
from .misc.camera import Camera
from .misc.input import Input
from .rendering.renderer import Renderer
from .sound.sounds import Sounds
from .tiles.tilemap import Tilemap, Tile
from .ui.text import Text
from .ui.textbox import Textbox
from .hot_script.script_loader import ScriptLoader

def init(dimensions=(640, 480), caption='pygpen window', entity_path=None,
        sounds_path=None, spritesheet_path=None, input_path=None,
        font_path=None, flags=0, fps_cap=60, dt_cap=1,
        opengl=False, frag_path=None, sound_filetype='wav', scripts_path='engine/scripts'):
    window = Window(dimensions=dimensions, caption=caption, flags=flags, fps_cap=fps_cap, 
                   dt_cap=dt_cap, opengl=opengl, frag_path=frag_path)
    entity_groups = EntityGroups()
    entity_db = EntityDB(path=entity_path)
    renderer = Renderer()
    sounds = Sounds(path=sounds_path, filetype=sound_filetype)
    assets = Assets(spritesheet_path=spritesheet_path)
    input = Input(path=input_path)
    text = Text(path=font_path)
    script_loader = ScriptLoader(scripts_path)
    elements = elems
    
    return elements