import scripts.pygpen as pp

class Earth(pp.ElementSingleton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.dmg = 20
        
    def use(self, enemy):
        enemy.tkd(self.dmg)