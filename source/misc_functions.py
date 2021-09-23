import math

WIDTH = 0
HEIGHT = 0
MOD = 1
DIFFICULTY = None

def get_distance(xy1, xy2):
    """ Calculate euclidean distance. """

    x1 = xy1[0]
    y1 = xy1[1]
    x2 = xy2[0]
    y2 = xy2[1]

    delta_x = (x1-x2) ** 2
    delta_y = (y1-y2) ** 2
    sum_ = delta_x + delta_y

    return (sum_ ** 0.5)


def in_bounds(screen_width, screen_height, item, buffer=0):
    """ Check if given item is within bounds of the screen. """

    if any((
                item.rect.right < (0 - buffer),
                item.rect.left > (screen_width + buffer),
                item.rect.bottom < (0 - buffer),
                item.rect.top > (screen_height + buffer)
              )):
        return False

    return True


def mod(*args):
    """ Modifies values based on screen resolution. """
    
    results = list()
    for val in args:
        results.append(round(val * MOD))
    
    return results[0] if len(results) == 1 else tuple(results)


def get_delta_length(length, angle):
    angle = (angle % 90) * 2
    angle = math.radians(angle)
    delta = (abs(math.sin(angle)) * (length * 0.24))
    return (delta / 2)


def set_globs(w=None, h=None, m=None, d=None):
    global WIDTH
    global HEIGHT
    global MOD
    global DIFFICULTY

    WIDTH = WIDTH if w is None else w
    HEIGHT = HEIGHT if h is None else h
    MOD = MOD if m is None else m
    DIFFICULTY = DIFFICULTY if d is None else d