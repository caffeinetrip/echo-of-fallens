import scripts.pygpen as pp

class Dark(pp.ElementSingleton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.dmg = 40
        
    def use(self, enemy):
        enemy.tkd(self.dmg)