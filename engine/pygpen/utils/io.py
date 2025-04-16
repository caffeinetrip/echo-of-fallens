import os
import json
import pygame

def read_f(path):
    f = open(path, 'r')
    data = f.read()
    f.close()
    return data

def write_f(path, data):
    f = open(path, 'w')
    f.write(data)
    f.close()

def read_json(path):
    f = open(path, 'r')
    data = json.load(f)
    f.close()
    return data

def write_json(path, data):
    f = open(path, 'w')
    json.dump(data, f)
    f.close()
    
def tjson_hook(obj):
    if type(obj) == dict:
        for key in list(obj):
            if (type(key) == str) and (key.translate({ord(k): None for k in ' (),t\0'}).isalnum()) and (key.find(',') != -1) and (key[:2] == 't\0'):
                new_key = tuple(int(v) for v in key.translate({ord(k): None for k in ' ()t\0'}).split(','))
                obj[new_key] = obj[key]
                del obj[key]
    return obj

def tjson_hook_loose(obj):
    if type(obj) == dict:
        for key in list(obj):
            if (type(key) == str) and (key.translate({ord(k): None for k in ' (),t\0'}).isalnum()) and (key.find(',') != -1):
                new_key = tuple(int(v) for v in key.translate({ord(k): None for k in ' ()t\0'}).split(','))
                obj[new_key] = obj[key]
                del obj[key]
    return obj

def tuple_change_keys(obj, convert):
    if isinstance(obj, (str, int, float)):
        return obj
    if isinstance(obj, dict):
        new = obj.__class__()
        for k, v in obj.items():
            new[convert(k)] = tuple_change_keys(v, convert)
    elif isinstance(obj, (list, set, tuple)):
        new = obj.__class__(tuple_change_keys(v, convert) for v in obj)
    else:
        return obj
    return new

def tuplestrkey(obj):
    if type(obj) == tuple:
        obj = 't\0' + str(obj).replace(' ', '')
    return obj

def tjson_encode(data):
    return json.dumps(tuple_change_keys(data, tuplestrkey))

def tjson_decode(data, loose=False):
    if loose:
        return json.loads(data, object_hook=tjson_hook_loose)
    else:
        return json.loads(data, object_hook=tjson_hook)

def read_tjson(path, loose=False):
    return tjson_decode(read_f(path), loose=loose)

def write_tjson(path, data):
    write_f(path, tjson_encode(data))

def recursive_file_op(path, func, filetype=None):
    data = {}
    base_path = path.split('/')
    for f in os.walk(path):
        wpath = f[0].replace('\\', '/').split('/')
        path_ref = wpath.copy()
        data_ref = data

        # iteratively generate file structure
        while len(path_ref) > len(base_path):
            current_dir = path_ref[len(base_path)]
            if current_dir not in data_ref:
                data_ref[current_dir] = {}
            data_ref = data_ref[current_dir]
            path_ref.pop(len(base_path))

        # load assets
        for asset in f[2]:
            asset_type = asset.split('.')[-1]
            if (asset_type == filetype) or (filetype == None):
                data_ref[asset.split('.')[0]] = func(f[0] + '/' + asset)

    return data

def load_music_from_folder(path):
    pygame.mixer.init()
    valid_extensions = {'mp3', 'wav', 'ogg', 'flac'}
    music_files = []
    
    for root, _, files in os.walk(path):
        for file in files:
            if file.split('.')[-1].lower() in valid_extensions:
                full_path = os.path.join(root, file)
                music_files.append(pygame.mixer.Sound(full_path))
    
    return music_files
