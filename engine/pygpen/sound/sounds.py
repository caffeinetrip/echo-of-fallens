import pygame
import os
from ..utils.elements import ElementSingleton
from ..utils import io

class Sounds(ElementSingleton):
    def __init__(self, path=None, filetype='wav'):
        super().__init__()
        pygame.mixer.init()
        pygame.mixer.set_num_channels(64)
        self.path = path
        self.filetype = filetype
        self.pan_vol = True
        self.sounds = {}
        
        self.current_music = None
        self.music_volume = 0.5
        
        if path:
            self.load(path, filetype)
            
    def load(self, path, filetype='wav'):
        self.path = path
        self.filetype = filetype
        if os.path.exists(path):
            self.sounds = io.recursive_file_op(path, lambda x: pygame.mixer.Sound(x), filetype=filetype)
        
    def play(self, sound_id, volume=1.0, pan=0, times=0):
        if not self.sounds:
            return None
        
        if volume > 0.7:
            volume = 0.2
            
        sound_id_split = sound_id.split('/')
        s = self.sounds
        
        try:
            while len(sound_id_split):
                next_id = sound_id_split.pop(0)
                if (type(s) == dict) and (next_id in s):
                    s = s[next_id]
                else:
                    return None
                    
            if type(s) != pygame.mixer.Sound:
                return None
                
            channel = s.play(times)
            
            if channel:
                if pan:
                    volumes = (1 - (pan + 1) / 2, (pan + 1) / 2)
                    if self.pan_vol:
                        volume *= 1 - abs(pan) * 0.9
                    channel.set_volume(volumes[0] * volume, volumes[1] * volume)
                else:
                    channel.set_volume(volume)
                    
            return channel
        except Exception as e:
            print(f"Error playing sound {sound_id}: {e}")
            return None
            
    def play_music(self, music_id, volume=None, loop=True):
        if volume is None:
            volume = self.music_volume
        else:
            self.music_volume = volume
            
        if self.current_music == music_id and pygame.mixer.music.get_busy():
            pygame.mixer.music.set_volume(volume)
            return
            
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
            music_path = os.path.join(self.path, f"{music_id}.{self.filetype}")
            
            if not os.path.exists(music_path):
                music_path = os.path.join(os.path.dirname(self.path), 'music', f"{music_id}.{self.filetype}")
                
            if not os.path.exists(music_path):
                music_path = os.path.join(os.path.dirname(self.path), 'music', f"{music_id}.mp3")
                
            if os.path.exists(music_path):
                pygame.mixer.music.load(music_path)
                pygame.mixer.music.set_volume(volume)
                
                if loop:
                    pygame.mixer.music.play(-1)
                else:
                    pygame.mixer.music.play()
                    
                self.current_music = music_id
        except Exception as e:
            print(f"Error playing music {music_id}: {e}")
            
    def stop_music(self, fade_out_ms=500):
        try:
            pygame.mixer.music.fadeout(fade_out_ms)
            self.current_music = None
        except:
            pass