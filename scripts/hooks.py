LOCATIONS = {
    'spawn': (160, 120)
}

def gen_hook():
    def hook(tile_data, ongrid):
        wpos = tile_data['pos']
        if ongrid:
            wpos = (wpos[0] * 16, wpos[1] * 16)
            
        if tile_data['group'] == 'entities':
            if tuple(tile_data['tile_id']) == (0, 0):
                LOCATIONS['spawn'] = wpos
            return True
            
        return True
        
    return hook