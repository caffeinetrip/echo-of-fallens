import scripts.pygpen as pp

class Deck(pp.ElementSingleton):
    def __init__(self, custom_id=None):
        super().__init__(custom_id)
        
        self.cards = []
        
