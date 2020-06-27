import random
import statistics as stats
import math
from pathlib import Path

import pygame as pg

from misc_functions import get_distance, in_bounds, mod

# Define working directory
DIR_PATH = Path.cwd().parent
# Modify DIR_PATH if game is being run from executable
if DIR_PATH.name == "dist":
    DIR_PATH = Path.cwd().parent.parent

WHITE = (255, 255, 255)
COLOR_ACTIVE = (0, 0, 0)
COLOR_INACTIVE = (80, 80, 80)
WIDTH = 0
HEIGHT = 0
MOD = 1
DIFFICULTY = None

# Define difficulty scalars
SPEED_SCALAR = {"Easy": 0.5, "Medium": 1.5, "Hard": 3}
SCORE_SCALAR = {"Easy": 1, "Medium": 2, "Hard": 3}


class Autophagosome(pg.sprite.Sprite):
    """
        Spherical sprite that can contain cargo and is removed through dragging by the player.
        AP: autophagosome
    """

    def __init__(self, phago_locs):
        super().__init__()

        # Collect x and y coordinates of precursor phagophore
        xs = sorted([xy[0] for xy in phago_locs])
        ys = sorted([xy[1] for xy in phago_locs])

        # Get radius of ellipse drawn by user
        x_rad = (xs[-1] - xs[0])
        y_rad = (ys[-1] - ys[0])
        self.area = (x_rad * y_rad * math.pi)

        # Calculate radius of circle with same radius
        rad = ((self.area / math.pi) ** 0.5) / 2
        self.radius = round(rad)

        # Establish appearance of AP
        AP_dim = round((self.radius * 2) * 1.2)
        self.image = pg.image.load(str(DIR_PATH / "images" / "AP.png")).convert()
        self.image = pg.transform.scale(self.image, (AP_dim, AP_dim))
        self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect()

        # Initalize location
        self.rect.x = round(stats.mean(xs)) - (self.radius * 1.1)
        self.rect.y = round(stats.mean(ys)) - self.radius

        self.dx = 0
        self.dy = 0

        self.contents = []

    def handle_event(self, event, prev_loc, cur_loc):
        """ Respond to player mouse dragging by accelerating AP. """
        if pg.mouse.get_pressed()[0]:
            # See if click is within AP
            distance = get_distance(self.rect.center, cur_loc)
            if distance < self.radius:
                # Update velocities
                self.dx = (cur_loc[0] - prev_loc[0])
                self.dy = (cur_loc[1] - prev_loc[1])

    def update(self, screen):
        """ Update AP position. """

        self.rect.move_ip(self.dx, self.dy)
        
        # Update content positions
        for item in self.contents:
            item.rect.move_ip(self.dx, self.dy)

        # Delete AP if off screen
        if not in_bounds(WIDTH, HEIGHT, self, buffer=100):
            self.kill()
    
    def draw(self, screen):
        """ Blit the AP. """
        screen.blit(self.image, self.rect)


class Cargo(pg.sprite.Sprite):
    """
        Intracellular entity that can become encapsulated by phagophore.
    """

    def __init__(self, file_name, x_dim, y_dim, score_val, x_speed_cap, y_speed_cap, x=None, y=None, dx=None, dy=None):
        super().__init__()

        # Esablish appearance
        self.image = pg.image.load(str(DIR_PATH / "images" / file_name)).convert()
        self.image = pg.transform.scale(self.image, (round(x_dim), round(y_dim)))

        self.image.set_colorkey(WHITE)
        self.rect = self.image.get_rect()


        # Initialize positions and velocites
        adj_x_speed = round(x_speed_cap * SPEED_SCALAR[DIFFICULTY])
        adj_y_speed = round(y_speed_cap * SPEED_SCALAR[DIFFICULTY])

        self.rect.x = x if x is not None else random.randrange(0, WIDTH)
        self.rect.y = y if y is not None else random.randrange(0, HEIGHT)
        self.dx = dx if dx is not None else random.randrange(-adj_x_speed, adj_x_speed + 1)
        self.dy = dy if dy is not None else random.randrange(-adj_y_speed, adj_y_speed + 1)

        self.dx_cap = adj_x_speed
        self.dy_cap = adj_y_speed

        self.trapped = False
        self.score_val = score_val * SCORE_SCALAR[DIFFICULTY]

    def update(self):
        """ Update position and velocity. """
        if not self.trapped:
            # Mutate velocities
            self.dx += random.randrange(-3, 4)
            self.dy += random.randrange(-3, 4)

            # Cap velocities
            if self.dx > self.dx_cap:
                self.dx = self.dx_cap
            if self.dx < -(self.dx_cap):
                self.dx = -(self.dx_cap)
            if self.dy > self.dy_cap:
                self.dy = self.dy_cap
            if self.dy < -(self.dy_cap):
                self.dy = -(self.dy_cap)

            # Update position
            self.rect.move_ip(self.dx, self.dy)

            # Constrain to screen and flip velocities
            if self.rect.left < 0:
                self.rect.left = 0
                self.dx = -(self.dx)
            if self.rect.right > WIDTH:
                self.rect.right = WIDTH
                self.dx = -(self.dx)
            if self.rect.top < 0:
                self.rect.top = 0
                self.dy = -(self.dy)
            if self.rect.bottom > HEIGHT:
                self.rect.bottom = HEIGHT
                self.dy = -(self.dy)


class Mitochondrion(Cargo):
    def __init__(
        self, 
        file_name="mito.png", 
        x_dim=mod(300), 
        y_dim=mod(165), 
        score_val=100, 
        x_speed_cap=mod(7), 
        y_speed_cap=mod(7), 
        x=None, 
        y=None, 
        dx=None, 
        dy=None
    ):

        super().__init__(file_name, x_dim, y_dim, score_val, x_speed_cap, y_speed_cap, x, y, dx, dy)

class Ribosome(Cargo):
    def __init__(
        self, 
        file_name="ribo.png", 
        x_dim=mod(90), 
        y_dim=mod(90), 
        score_val=50, 
        x_speed_cap=mod(15), 
        y_speed_cap=mod(15), 
        x=None, 
        y=None, 
        dx=None, 
        dy=None
    ):

        super().__init__(file_name, x_dim, y_dim, score_val, x_speed_cap, y_speed_cap, x, y, dx, dy)


class RNA(Cargo):
    def __init__(
        self, 
        file_name="rna.png", 
        x_dim=mod(75), 
        y_dim=mod(300), 
        score_val=150, 
        x_speed_cap=mod(2), 
        y_speed_cap=mod(12), 
        x=None, 
        y=None, 
        dx=None, 
        dy=None
    ):

        super().__init__(file_name, x_dim, y_dim, score_val, x_speed_cap, y_speed_cap, x, y, dx, dy)


class Pill(Cargo):
    def __init__(
        self, 
        file_name="pill.png", 
        x_dim=mod(150), 
        y_dim=mod(75), 
        score_val=-300, 
        x_speed_cap=mod(2), 
        y_speed_cap=mod(2), 
        x=None, 
        y=None, 
        dx=None, 
        dy=None
    ):

        super().__init__(file_name, x_dim, y_dim, score_val, x_speed_cap, y_speed_cap, x, y, dx, dy)


class Button:
    """ Clickable button. """

    def __init__(self, x, y, w, h, font_, text_, toggle_=False, callback_=None, *args_, **kwargs_):
        self.rect = pg.Rect(x, y, w, h)
        self.text = text_
        self.font = font_
        self.txt_surface = font_.render(text_, True, WHITE)
        self.toggle = toggle_
        self.callback = callback_
        self.args = args_
        self.kwargs = kwargs_
        self.color = COLOR_INACTIVE
        self.active = False

    def handle_event(self, event, glob_diff=None):
        """ Detect button click and respond accordingly. """

        # Check if button is currently being clicked
        clicked = False
        if event.type == pg.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                clicked = True

        # Handle toggle buttons
        if self.toggle:
            if clicked:
                self.active = True
                glob_diff = self.text
        # Handle non-toggle buttons
        else:
            if clicked:            
                self.active = True
                
            # Trigger callback if button click completed
            elif not clicked:
                if self.active:
                    self.callback(*self.args, **self.kwargs)

                self.active = False
            
        # Set color based on activation state
        self.color = COLOR_ACTIVE if self.active else COLOR_INACTIVE

        return glob_diff


    def draw(self, screen):
        """ Center text and blit button to screen. """
        pg.draw.rect(screen, self.color, self.rect)
        text_x = self.rect.x + ((self.rect.w - self.txt_surface.get_width()) / 2)
        text_y =  self.rect.y + ((self.rect.h - self.txt_surface.get_height()) / 2)
        screen.blit(self.txt_surface, (text_x, text_y))

def set_globs(w=None, h=None, m=None, d=None):
    global WIDTH
    global HEIGHT
    global MOD
    global DIFFICULTY

    WIDTH = WIDTH if w is None else w
    HEIGHT = HEIGHT if h is None else h
    MOD = MOD if m is None else m
    DIFFICULTY = DIFFICULTY if d is None else d
