SCREENWIDTH = 1900
SCREENHEIGHT = 1000


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


def in_bounds(item, buffer=0):
    '''
        Check if given item is within bounds of the screen.
    '''

    if any((
                item.rect.right < (0 - buffer),
                item.rect.left > (SCREENWIDTH + buffer),
                item.rect.bottom < (0 - buffer),
                item.rect.top > (SCREENHEIGHT + buffer)
              )):
        return False

    return True
