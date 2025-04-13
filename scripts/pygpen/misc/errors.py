class InvalidAsset(KeyError):
    def __init__(self, asset_id):
        self.value = f"{asset_id} is an invalid asset ID."
    
    def __str__(self):
        return repr(self.value)