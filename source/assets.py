import random
import statistics as stats
import math
from pathlib import Path

import pygame as pg
from pygame import transform

from misc_functions import get_distance, in_bounds, mod, get_delta_length

# Define working directory
DIR_PATH = Path.cwd().parent
# Modify DIR_PATH if game is being run from executable
if DIR_PATH.name == "dist":
    DIR_PATH = Path.cwd().parent.parent

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BACKGROUND_BLUE = (188, 238, 240)
COLOR_ACTIVE = (0, 0, 0)
COLOR_INACTIVE = (80, 80, 80)
WIDTH = 0
HEIGHT = 0
MOD = 1
DIFFICULTY = None
PILL_IMAGES = {}
RIBO_IMAGES = {}
RNA_IMAGES = {}
MITO_LARGE_IMAGES = {}
MITO_MED_IMAGES = {}
MITO_SMALL_IMAGES = {}

# Define difficulty scalars
SPEED_SCALAR = {"Easy": 0.5, "Medium": 1, "Hard": 1.7}
SCORE_SCALAR = {"Easy": 1, "Medium": 2, "Hard": 3}

ANGLE_LIST = [-5, -4, -3, -2, -1, 1, 2, 3, 4, 5]

def set_image_dicts():
    def get_images(cargo):
        image = pg.image.load(str(DIR_PATH / "images" / cargo.file_name)).convert_alpha()
        image = pg.transform.scale(image, (int(cargo.x_dim), int(cargo.y_dim)))
        image_dict = {}

        for angle in range(0, 360):
            rotated_surface = pg.transform.rotozoom(image, angle, 1)
            rotated_surface.set_colorkey(BLACK)
            image_dict[angle] = rotated_surface

        return image_dict

    global PILL_IMAGES
    global RIBO_IMAGES
    global RNA_IMAGES
    global MITO_LARGE_IMAGES
    global MITO_MED_IMAGES
    global MITO_SMALL_IMAGES


    PILL_IMAGES = get_images(Pill())
    RIBO_IMAGES = get_images(Ribosome())
    RNA_IMAGES = get_images(RNA())

    _mito = Mitochondrion()
    MITO_LARGE_IMAGES = get_images(Mitochondrion())
    MITO_MED_IMAGES = get_images(Mitochondrion(x_dim=_mito.image_static.get_width()/2, y_dim=_mito.image_static.get_height()/2))
    MITO_SMALL_IMAGES = get_images(Mitochondrion(x_dim=_mito.image_static.get_width()/4, y_dim=_mito.image_static.get_height()/4))



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
        self.image.set_colorkey(BLACK)
        self.rect = self.image.get_rect()

        # Initalize location
        self.rect.center = (round(stats.mean([min(xs), max(xs)])), round(stats.mean([min(ys), max(ys)])))

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
                dx = (cur_loc[0] - prev_loc[0])
                dy = (cur_loc[1] - prev_loc[1])
                self.dx, self.dy = dx, dy


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

    def __init__(
        self, 
        file_name, 
        image_dict,
        x_dim, y_dim, 
        score_val, 
        x_speed_cap, 
        y_speed_cap, 
        x=None, 
        y=None, 
        dx=None, 
        dy=None, 
        adjust_box=False, 
        scale_score=True
        ):
        

        self.file_name = file_name
        self.image_dict = image_dict
        self.x_dim = x_dim
        self.y_dim = y_dim

        super().__init__()

        # Esablish appearance
        self.image = pg.image.load(str(DIR_PATH / "images" / file_name)).convert_alpha()
        self.image = pg.transform.scale(self.image, (round(x_dim), round(y_dim)))

        self.image.set_colorkey(WHITE)
        self.image_static = self.image
        self.rect = self.image.get_rect()

        # Initialize positions, velocites and angles
        self.dx_cap = round(x_speed_cap * SPEED_SCALAR[DIFFICULTY])
        self.dy_cap = round(y_speed_cap * SPEED_SCALAR[DIFFICULTY])

        self.angle = random.randrange(0, 360)
        self.angle_rate = 0
        while self.angle_rate == 0:
            self.angle_rate=random.randrange(-5, 5)

        self.rect.x = x if x is not None else random.randrange(0, WIDTH)
        self.rect.y = y if y is not None else random.randrange(0, HEIGHT)

        self.dx, self.dy = 0, 0
        while 0 in [self.dx, self.dy]:
            self.dx = dx if dx is not None else random.randrange(-self.dx_cap, self.dx_cap + 1)
            self.dy = dy if dy is not None else random.randrange(-self.dy_cap, self.dy_cap + 1)

        self.trapped = False
        self.bound = True
        self.score_val = score_val * SCORE_SCALAR[DIFFICULTY] if scale_score else score_val

        self.adjust_box = adjust_box


    def rotate(self):
        """ Rotate cargo by angle stored in self.angle. """

        rotated_surface = transform.rotozoom(self.image_static, self.angle, 1)
        rotated_surface.set_colorkey(BLACK)
        rotated_rect = rotated_surface.get_rect()
        return rotated_surface, rotated_rect


    def update(self):
        """ Update position and velocity. """

        if not self.trapped:
            # Save information on original rectangle
            old_rect = self.rect

            # Update position
            self.rect.move_ip(self.dx, self.dy)

            delta = get_delta_length(self.rect.width, self.angle) if self.adjust_box else 0

            left = self.rect.left if not self.adjust_box else self.rect.left + delta
            right = self.rect.right if not self.adjust_box else self.rect.right - delta
            top = self.rect.top if not self.adjust_box else self.rect.top + delta
            bottom = self.rect.bottom if not self.adjust_box else self.rect.bottom - delta

            if self.bound:
                # Constrain to screen and flip velocities
                rand_angle = random.choice(ANGLE_LIST)

                if left < 0:
                    self.rect.left = 0 - delta
                    self.dx = -(self.dx)
                    self.angle_rate = rand_angle
                if right > WIDTH:
                    self.rect.right = WIDTH + delta
                    self.dx = -(self.dx)
                    self.angle_rate = rand_angle
                if top < 0:
                    self.rect.top = 0 - delta
                    self.dy = -(self.dy)
                    self.angle_rate = rand_angle
                if bottom > HEIGHT:
                    self.rect.bottom = HEIGHT + delta
                    self.dy = -(self.dy)
                    self.angle_rate = rand_angle

                # Update angle and rotate cargo
                self.angle = (self.angle + self.angle_rate) % 360
                self.image = self.image_dict[self.angle]
                self.rect = self.image.get_rect()

                # Determine new x, y coordinates and move cargo
                new_x = old_rect.x + ((old_rect.width - self.rect.width) / 2) + self.dx
                new_y = old_rect.y + ((old_rect.height - self.rect.height) / 2) + self.dy
                self.rect.move_ip(new_x, new_y)    


class Mitochondrion(Cargo):
    def __init__(
        self, 
        file_name="mito.png", 
        image_dict=None,
        x_dim=mod(300), 
        y_dim=mod(165), 
        score_val=100, 
        x_speed_cap=mod(5), 
        y_speed_cap=mod(5), 
        x=None, 
        y=None, 
        dx=None, 
        dy=None,
        adjust_box=True,
        scale_score=True
    ):
        # Mutable defaults are the source of all evil
        if image_dict is None:
            image_dict = MITO_LARGE_IMAGES

        super().__init__(file_name, image_dict, x_dim, y_dim, score_val, x_speed_cap, y_speed_cap, x, y, dx, dy, adjust_box, scale_score)

class Ribosome(Cargo):
    def __init__(
        self, 
        file_name="ribo.png", 
        image_dict=None,
        x_dim=mod(90), 
        y_dim=mod(90), 
        score_val=50, 
        x_speed_cap=mod(15), 
        y_speed_cap=mod(15), 
        x=None, 
        y=None, 
        dx=None, 
        dy=None,
        adjust_box=False
    ):
        # Mutable defaults are the source of all evil
        if image_dict is None:
            image_dict = RIBO_IMAGES

        super().__init__(file_name, image_dict, x_dim, y_dim, score_val, x_speed_cap, y_speed_cap, x, y, dx, dy, adjust_box)


class RNA(Cargo):
    def __init__(
        self, 
        file_name="rna.png", 
        image_dict=None,
        x_dim=mod(75), 
        y_dim=mod(300), 
        score_val=150, 
        x_speed_cap=mod(10), 
        y_speed_cap=mod(10), 
        x=None, 
        y=None, 
        dx=None, 
        dy=None,
        adjust_box=False        
    ):
        # Mutable defaults are the source of all evil
        if image_dict is None:
            image_dict = RNA_IMAGES

        super().__init__(file_name, image_dict, x_dim, y_dim, score_val, x_speed_cap, y_speed_cap, x, y, dx, dy, adjust_box)


class Pill(Cargo):
    def __init__(
        self, 
        file_name="pill.png", 
        image_dict=None,
        x_dim=mod(150), 
        y_dim=mod(75), 
        score_val=-300, 
        x_speed_cap=mod(2), 
        y_speed_cap=mod(2), 
        x=None, 
        y=None, 
        dx=None, 
        dy=None,
        adjust_box=False
    ):

        # Mutable defaults are the source of all evil
        if image_dict is None:
            image_dict = PILL_IMAGES

        super().__init__(file_name, image_dict, x_dim, y_dim, score_val, x_speed_cap, y_speed_cap, x, y, dx, dy, adjust_box)

class Particle(Cargo):
    def __init__(
        self, 
        file_name="pill.png", 
        image_dict=None,
        x_dim=mod(50), 
        y_dim=mod(25), 
        score_val=0, 
        x_speed_cap=mod(4), 
        y_speed_cap=mod(4), 
        x=None, 
        y=None, 
        dx=None, 
        dy=None,
        adjust_box=False
    ):

        # Mutable defaults are the source of all evil
        if image_dict is None:
            image_dict = PILL_IMAGES

        super().__init__(file_name, image_dict, x_dim, y_dim, score_val, x_speed_cap, y_speed_cap, x, y, dx, dy, adjust_box)



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
    
        # Initialize image
        base_up = pg.image.load(str(DIR_PATH / "images" / "button_up.png")).convert()
        base_down = pg.image.load(str(DIR_PATH / "images" / "button_down.png")).convert()
        self.image_up = pg.transform.scale(base_up, (w, h))
        self.image_down = pg.transform.scale(base_down, (w, h))
        self.image_up.set_colorkey(BLACK)
        self.image_down.set_colorkey(BLACK)

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

        image = self.image_down if self.active else self.image_up
        delta = (0.14*self.rect.h) if self.active else 0
        
        text_x = self.rect.x + ((self.rect.w - self.txt_surface.get_width()) / 2)
        text_y =  self.rect.y + ((self.rect.h - self.txt_surface.get_height()) / 2) - (self.rect.h * 0.1)
        screen.blit(image, self.rect)
        screen.blit(self.txt_surface, (text_x, text_y+delta))
        

def set_globs(w=None, h=None, m=None, d=None):
    global WIDTH
    global HEIGHT
    global MOD
    global DIFFICULTY


    WIDTH = WIDTH if w is None else w
    HEIGHT = HEIGHT if h is None else h
    MOD = MOD if m is None else m
    DIFFICULTY = DIFFICULTY if d is None else d