# models.py
class FrameData:
    """ 
    Represents a single 'Line' (or Page). 
    Stores vector paths and metadata.
    """
    def __init__(self, index):
        self.index = index
        self.paths = [] # List of QPainterPath objects
