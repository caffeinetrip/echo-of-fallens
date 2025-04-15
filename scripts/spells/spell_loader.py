import json
import os
import scripts.pygpen as pp

class SpellRegistry:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SpellRegistry, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.spell_data = {}
        self.loaded = False
    
    def load_spell_data(self):
        if self.loaded:
            return
            
        try:
            json_path = 'data/dbs/spells/spells.json'

            os.makedirs(os.path.dirname(json_path), exist_ok=True)
            
            if not os.path.exists(json_path):
                self._create_default_spells_json(json_path)
            
            with open(json_path, 'r') as f:
                data = json.load(f)
                self.spell_data = {spell['id']: spell for spell in data['spells']}
            
            self.loaded = True
        except Exception as e:
            print(f"Error loading spell data: {e}")
            self.spell_data = self._get_default_spell_data()
    
    def _create_default_spells_json(self, json_path):
        default_data = {"spells": list(self._get_default_spell_data().values())}
        with open(json_path, 'w') as f:
            json.dump(default_data, f, indent=2)
    
    def _get_default_spell_data(self):
        return {
            "fire": {
                "id": "fire",
                "dmg": 20
            },
            "water": {
                "id": "water",
                "dmg": 20
            },
            "earth": {
                "id": "earth",
                "dmg": 20
            },
            "dark": {
                "id": "dark",
                "dmg": 40
            }
        }
    
    def create_spell(self, spell_id):
        if not self.loaded:
            self.load_spell_data()
            
        if spell_id not in self.spell_data:
            print(f"Warning: Unknown spell ID: {spell_id}, using default")
            return SpellBase({"id": spell_id, "dmg": 10})
            
        data = self.spell_data[spell_id]
        return SpellBase(data)


class SpellBase(pp.ElementSingleton):
    def __init__(self, data):
        super().__init__(data['id'])
        self.id = data['id']
        self.dmg = data.get('dmg', 10)
        self.type = data.get('id', 'unknown')
        
    def use(self, enemy):
        if hasattr(enemy, 'tkd'):
            enemy.tkd(self.dmg)
            return True
        return False

registry = SpellRegistry()

def create_spell(spell_id):
    return registry.create_spell(spell_id)

registry.load_spell_data()