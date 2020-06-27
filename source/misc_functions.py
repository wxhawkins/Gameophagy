WIDTH = 0
HEIGHT = 0
MOD = 1

def get_distance(xy1, xy2):
    '''
        Calculate euclidean distance.
    '''

    x1 = xy1[0]
    y1 = xy1[1]
    x2 = xy2[0]
    y2 = xy2[1]

    delta_x = (x1-x2) ** 2
    delta_y = (y1-y2) ** 2
    sum_ = delta_x + delta_y

    return (sum_ ** 0.5)


def in_bounds(screen_width, screen_height, item, buffer=0):
    '''
        Check if given item is within bounds of the screen.
    '''

    if any((
                item.rect.right < (0 - buffer),
                item.rect.left > (screen_width + buffer),
                item.rect.bottom < (0 - buffer),
                item.rect.top > (screen_height + buffer)
              )):
        return False

    return True


def set_res(width, height, mod):
    global WIDTH
    global HEIGHT
    global MOD

    WIDTH = width
    HEIGHT = height
    MOD = mod

def mod(*args):
    results = list()
    for val in args:
        results.append(round(val * MOD))
    
    return results[0] if len(results) == 1 else tuple(results)
