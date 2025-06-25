
# common filament mixures

from typ import ColorFilamentLayer

def bwc4levels(color: str, level: int)->list[ColorFilamentLayer]:
    '''
    black, white, color, 4 levels of color mixture
    '''
    if level == 4:
        return [
            ColorFilamentLayer(l = 1, c=color),
            ColorFilamentLayer(l = 2, c="000000"),
        ]
    elif level == 3:
        return [
            ColorFilamentLayer(l = 2, c=color),
            ColorFilamentLayer(l = 2, c="000000"),
        ]
    elif level == 2:
        return [
            ColorFilamentLayer(l = 3, c=color),
            ColorFilamentLayer(l = 1, c="000000"),
        ]
    elif level == 1:
        return [
            ColorFilamentLayer(l = 1, c="FFFFFF"),
            ColorFilamentLayer(l = 2, c=color),
        ]
    else:
        raise ValueError("Level must be between 1 and 4")
    

def bw4levels(level: int)->list[ColorFilamentLayer]:
    '''
    black, white, 4 levels of black and white mixture
    '''
    if level == 4:
        return [
            ColorFilamentLayer(l = 1, c="FFFFFF"),
            ColorFilamentLayer(l = 2, c="000000"),
        ]
    elif level == 3:
        return [
            ColorFilamentLayer(l = 2, c="FFFFFF"),
            ColorFilamentLayer(l = 2, c="000000"),
        ]
    elif level == 2:
        return [
            ColorFilamentLayer(l = 3, c="FFFFFF"),
            ColorFilamentLayer(l = 2, c="000000"),
        ]
    elif level == 1:
        return [
            ColorFilamentLayer(l = 4, c="FFFFFF"),
            ColorFilamentLayer(l = 2, c="000000"),
        ]
    else:
        raise ValueError("Level must be between 1 and 4")
