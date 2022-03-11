import ctypes
import datetime
import json
import sys
from pathlib import Path
import random

import pygame as pg
from pygame.locals import *


import math
import pygame.gfxdraw

# Import personal files
import misc_functions
from misc_functions import get_distance, in_bounds, mod

# Define working directory
DIR_PATH = Path.cwd().parent
# Modify DIR_PATH if game is being run from executable
if DIR_PATH.name == "dist":
    DIR_PATH = Path.cwd().parent.parent

# Initialize variables for screen resolution
WIDTH = ctypes.windll.user32.GetSystemMetrics(0)
HEIGHT = ctypes.windll.user32.GetSystemMetrics(1)
MOD = round(WIDTH / 1920, 3) # Standardize to 1920x1080 resolution 

misc_functions.set_globs(w=WIDTH, h=HEIGHT,m=MOD)

import assets
from assets import Autophagosome, Button, Mitochondrion, Ribosome, RNA, Pill, Particle

assets.set_globs(w=WIDTH, h=HEIGHT, m=MOD)

# Define colors
GRAY = (80, 80, 80)
RED = (255, 0, 0)
YELLOW = (255, 255, 0)
BACKGROUND_BLUE = (188, 238, 240)
BLACK = (0, 0, 0)
PHAGO_LIGHT =  (218, 200, 101)
PHAGO_DARK = (196, 143, 85)

TICKRATE = 60
GAMETITLE = "Gameophagy"
HIT_CIRCLE_RADIUS = mod(100)
MITO_NUM = 5 #default 5
RIBO_NUM = 20 #default 20
RNA_NUM = 10 #default 10
TIMEOUT_THRESH = {"Easy": 240, "Medium": 60, "Hard": 20}
TIMEOUT_PENALTY = -300
MISS_PENALTY = 50
MIN_AREA = mod(20000)
DIFFICULTY = None
FISSION_THRESH = 1
ATG8_MIN_DIST = mod(100)


# Define fonts
pg.font.init()
conthrax_path = str(DIR_PATH / "fonts" / "PermanentMarker-Regular.ttf")
FONT_1 = pg.font.Font(conthrax_path, mod(130))
FONT_2 = pg.font.Font(conthrax_path, mod(80))
FONT_3 = pg.font.Font(conthrax_path, mod(60))
FONT_4 = pg.font.Font(conthrax_path, mod(30))

# Initialize game
pg.init()
clock = pg.time.Clock()
pg.display.set_caption(GAMETITLE)
SCREEN = pg.display.set_mode((WIDTH, HEIGHT))
try:
    SCREEN = pg.display.set_mode((0, 0), pg.FULLSCREEN)
except pg.error: # Error sometimes encountered with 4K displays
    SCREEN = pg.display.set_mode((WIDTH, HEIGHT))

icon = pg.image.load(str(DIR_PATH / "images" / "icon.png"))
pg.display.set_icon(icon)


class ParticleProfile:
    """ Stores key information about particles to be generated. """

    def __init__(self, AP):
        # Get particle spawn location based on source autophagosome
        center = AP.rect.center
        radius = 0.5 * Particle().x_dim
        self.x = center[0] - radius
        self.y = center[1] - radius

        # Cap velocity and reverse
        speed_cap = mod(15)
        d_mod = max([abs(AP.dx), abs(AP.dy)]) / speed_cap
        mod_dx = -round(AP.dx / d_mod, 1)
        mod_dy = -round(AP.dy / d_mod, 1)

        # Make non-zero
        if mod_dx == 0:
            mod_dx += 0.1 * (-1**random.randint(1, 2))

        if mod_dy == 0:
            mod_dy += 0.1 * (-1**random.randint(1, 2))

        self.base_dx = mod_dx
        self.base_dy = mod_dy

        # Determine number of particles to spawn based on captured cargo
        num_particles = len(AP.contents) * 6

        self.queue = num_particles

    def spawn(self, num_particles, particle_cargo):
        """ Generate particles based on particle profile. """

        for _ in range(min(self.queue, num_particles)):
            # Get unique velocities from base velocity
            dx = self.base_dx + (random.randint(mod(-300), mod(300)) / 100)
            dy = self.base_dy + (random.randint(mod(-300), mod(300)) / 100)

            # Generate particle and add to cargo group
            _particle = Particle(x=self.x, y=self.y, dx=dx, dy=dy)
            particle_cargo.add(_particle)
            self.queue -= 1
        
        return particle_cargo


def check_trapped(APs, items):
    """
        Checks if any cargo items were inside upon AP formation then update
        cargo and AP parameters accordingly.
    """

    trapped_cargo = pg.sprite.Group()

    for AP in APs:
        for item in items:
            max_distance = max([
                get_distance(AP.rect.center, item.rect.topleft),
                get_distance(AP.rect.center, item.rect.topright),
                get_distance(AP.rect.center, item.rect.bottomleft),
                get_distance(AP.rect.center, item.rect.bottomright),
            ])

            if max_distance < AP.radius:
                item.trapped = True
                AP.contents.append(item)
                trapped_cargo.add(item)

    return trapped_cargo


def purge_cargo(all_sprites_group, buffer=0):
    """ Kill captured sprites and update score accordingly. """

    score_change = 0
    for sprite in all_sprites_group:
        if not in_bounds(WIDTH, HEIGHT, sprite, buffer):
            score_change += sprite.score_val
            sprite.kill()


    return score_change


def inactivate_buttons(buttons):
    """ Inactive buttons due to mutual exclusivity. """

    for button in buttons:
        if button.text != DIFFICULTY:
            button.active = False


def display_page(pages):
    def incriment_page(val):
        nonlocal cur_page
        cur_page += val
    
        # Handle out of bounds
        if cur_page < 0:
            cur_page = 0
        if cur_page >= len(images):
            cur_page = len(images) - 1

    images = []
    for page in pages:
        # Create main image object
        image = pg.image.load(str(DIR_PATH / "images" / page)).convert()
        image_aspect = round(image.get_width() / image.get_height(), 3)
        screen_aspect = round(WIDTH / HEIGHT, 3)

        if image_aspect >= screen_aspect:
            new_width = WIDTH
            new_height = WIDTH / image_aspect
        else:
            new_height = HEIGHT
            new_width = HEIGHT * image_aspect

        image = pg.transform.scale(image, (int(new_width), int(new_height)))
        images.append(image)

    home_button = Button(mod(1580), mod(30), mod(250), mod(105), FONT_3, "Home", callback_=intro_screen)
    back_button = Button(mod(1500), images[0].get_height()-mod(100), mod(180), mod(60), FONT_4, "Back", callback_=incriment_page, val=-1)
    next_button = Button(mod(1700), images[0].get_height()-mod(100), mod(180), mod(60), FONT_4, "Next", callback_=incriment_page, val=1)

    cur_page = 0

    while True:
        SCREEN.blit(images[cur_page], (0, 0))

    
        for event in pg.event.get():
            exit_check(event)
            home_button.handle_event(event)
            back_button.handle_event(event)
            next_button.handle_event(event)
               
        home_button.draw(SCREEN)

        if cur_page > 0:
            back_button.draw(SCREEN)

        if cur_page < (len(images) - 1):
            next_button.draw(SCREEN)

        pg.display.flip()


def intro_screen():
    """ Show introduciton screen and acquire difficulty setting. """

    # Set up intro screen background
    into_bg = pg.image.load(str(DIR_PATH / "images" / "start_screen_basic.png")).convert()
    into_bg = pg.transform.scale(into_bg, (WIDTH, HEIGHT))
    
    # Set up title
    title = FONT_1.render(GAMETITLE, True, BLACK)

    pg.display.update()

    # Initalize buttons
    instruct_button = Button(mod(1250), mod(70), mod(280), mod(60), FONT_4, "Instructions", callback_=display_page, pages=["instructions.png"])
    sci_button = Button(mod(1550), mod(70), mod(280), mod(60), FONT_4, "Science", callback_=display_page, pages=["science_1.png", "science_2.png", "science_3.png"])
    easy_button = Button(mod(1250), mod(150), mod(180), mod(60), FONT_4, "Easy", toggle_=True)
    med_button = Button(mod(1450), mod(150), mod(180), mod(60), FONT_4, "Medium", toggle_=True)
    hard_button = Button(mod(1650), mod(150), mod(180), mod(60), FONT_4, "Hard", toggle_=True)
    play_button = Button(mod(1580), mod(230), mod(250), mod(105), FONT_3, "Play", callback_=game_loop)
    buttons = [instruct_button, sci_button, easy_button, med_button, hard_button, play_button]

    # Initalize difficulty
    global DIFFICULTY
    DIFFICULTY = "Medium"
    med_button.active = True

    # Intro page loop
    intro = True
    while intro:
        SCREEN.blit(into_bg, (0, 0))
        SCREEN.blit(title, mod(40, 21))

        for event in pg.event.get():
            exit_check(event)

            # Allow quick play with return key
            if event.type == KEYDOWN:
                if event.key == K_RETURN:
                    game_loop()

            # Check for difficulty change
            for button in buttons:
                glob_diff_ori = DIFFICULTY
                DIFFICULTY = button.handle_event(event, DIFFICULTY)
                if DIFFICULTY != glob_diff_ori:
                    inactivate_buttons([easy_button, med_button, hard_button])

        for button in buttons:
            button.draw(SCREEN)

        pg.display.flip()


def end_screen(score):
    """ Display end screen including final score and high scores. """
    
    score = int(score)

    # Read in high scores from JSON
    try:
        with open((DIR_PATH / "scores" / "high_scores.json"), "r") as in_file:
            score_list = json.loads(in_file.read())
    
        # Add line for current game
        cur_date = datetime.date.today()
        cur_date_fmt = f"{cur_date.month}/{cur_date.day}/{cur_date.year}"
        score_list.append({"score": int(score), "difficulty": DIFFICULTY, "date": cur_date_fmt})    

        # Update high scores JSON
        with open((DIR_PATH / "scores" / "high_scores.json"), "w") as out_file:
            json.dump(score_list, out_file, indent=4)
    
    # If error encountered, reset high scores file and try again
    except json.decoder.JSONDecodeError:
        with open((DIR_PATH / "scores" / "high_scores.json"), "w") as out_file:
            out_file.write("[]")
        end_screen(score)

    play_button = Button(mod(1300), mod(20), mod(425), mod(120), FONT_3, "Play again", callback_=intro_screen)

    # Show final score
    bg = pg.image.load(str(DIR_PATH / "images" / "full_background.png")).convert()
    bg = pg.transform.scale(bg, (WIDTH, HEIGHT))

    final_score_text = FONT_2.render(("Final Score: " + str(score)), True, (0, 0, 0))

    # Sort high scores
    score_list = sorted(score_list, key=lambda x: int(round(float(x["score"]))), reverse=True)

    # End page loop
    while True:
        SCREEN.blit(bg, (0, 0))
        SCREEN.blit(final_score_text, mod(100, 20))
        
        # Show high scores
        for i, line in enumerate(score_list[:10]):
            core_text = FONT_3.render(str(line["score"]), True, (0, 0, 0))
            diff_text = FONT_3.render(line["difficulty"], True, (0, 0, 0))
            date_text = FONT_3.render(line["date"], True, (0, 0, 0))
            SCREEN.blit(core_text, mod(100, 150 + (i * 80)))
            SCREEN.blit(diff_text, mod(700, 150 + (i * 80)))
            SCREEN.blit(date_text, mod(1300, 150 + (i * 80)))

        for event in pg.event.get():
            exit_check(event)

            play_button.handle_event(event, DIFFICULTY)

        play_button.draw(SCREEN)
        pg.display.flip()


def exit_check(event):
    """ Check if user requested to exit game. """

    # Exit by escape key
    if event.type == KEYDOWN:
        if event.key == K_ESCAPE:
            pg.quit()
            sys.exit()

    # Exit by clicking close button
    if event.type==pg.QUIT:
        pg.quit()
        sys.exit()

def spawn_cargo():
    """ Add cargo to game. """
    
    # Initalize sprite groups
    all_cargo = pg.sprite.Group()
    good_cargo = pg.sprite.Group()
    particle_cargo = pg.sprite.Group()

    # Generate mitochondria
    for _ in range(MITO_NUM):
        _mito = Mitochondrion()
        all_cargo.add(_mito)
        good_cargo.add(_mito)

    # # Generate ribosomes
    for _ in range(RIBO_NUM):
        _ribo = Ribosome()
        all_cargo.add(_ribo)
        good_cargo.add(_ribo)

    # # Generate RNAs
    for _ in range(RNA_NUM):
        _rna = RNA()
        all_cargo.add(_rna)
        good_cargo.add(_rna)

    return all_cargo, good_cargo, particle_cargo


def fission_mito(all_cargo, good_cargo):
    """ Split mitochondrion into two smaller mitochondria. """

    rand = random.randint(1, 100)
    if rand >= 15: #15% chance of fission
        return all_cargo, good_cargo

    # Extract largest mitochondrion
    main_mito = None
    for cargo in all_cargo:
        if isinstance(cargo, assets.Mitochondrion):
            if not cargo.trapped:
                if main_mito is None:
                    main_mito = cargo
                if cargo.image_static.get_width() > main_mito.image_static.get_width():
                    main_mito = cargo
    
    # Skip if none left
    if main_mito is None:
        return all_cargo, good_cargo

    # Skip if all mitos have gone through two fissions
    if round(main_mito.image_static.get_width()) == round((Mitochondrion().image_static.get_width()/4)):
        return all_cargo, good_cargo

    # Create mini-mitos
    for _ in range(2):
        if round(main_mito.image_static.get_width()) == (Mitochondrion().image_static.get_width()):
            image_dict = assets.MITO_MED_IMAGES
        else:
            image_dict = assets.MITO_SMALL_IMAGES
       
        _mito = Mitochondrion(
                image_dict = image_dict,
                x_dim=main_mito.image_static.get_width()/2, 
                y_dim=main_mito.image_static.get_height()/2,
                score_val=main_mito.score_val/2,
                x=main_mito.rect.center[0]-(main_mito.image_static.get_width()/4),
                y=main_mito.rect.center[1]-(main_mito.image_static.get_height()/4),
                scale_score=False
                )

        all_cargo.add(_mito)
        good_cargo.add(_mito)
    
    # Destory original mito
    main_mito.kill()

    return all_cargo, good_cargo


def aaline(surface, color, start_pos, end_pos, width=1):
    """ Draws wide transparent anti-aliased lines. """
    # ref https://stackoverflow.com/a/30599392/355230

    x0, y0 = start_pos
    x1, y1 = end_pos
    midpnt_x, midpnt_y = (x0+x1)/2, (y0+y1)/2  # Center of line segment.
    length = math.hypot(x1-x0, y1-y0)
    angle = math.atan2(y0-y1, x0-x1)  # Slope of line.
    width2, length2 = width/2, length/2
    sin_ang, cos_ang = math.sin(angle), math.cos(angle)

    width2_sin_ang  = width2*sin_ang
    width2_cos_ang  = width2*cos_ang
    length2_sin_ang = length2*sin_ang
    length2_cos_ang = length2*cos_ang

    # Calculate box ends.
    ul = (midpnt_x + length2_cos_ang - width2_sin_ang,
          midpnt_y + width2_cos_ang  + length2_sin_ang)
    ur = (midpnt_x - length2_cos_ang - width2_sin_ang,
          midpnt_y + width2_cos_ang  - length2_sin_ang)
    bl = (midpnt_x + length2_cos_ang + width2_sin_ang,
          midpnt_y - width2_cos_ang  + length2_sin_ang)
    br = (midpnt_x - length2_cos_ang + width2_sin_ang,
          midpnt_y - width2_cos_ang  - length2_sin_ang)

    pg.gfxdraw.aapolygon(surface, (ul, ur, br, bl), color)
    pg.gfxdraw.filled_polygon(surface, (ul, ur, br, bl), color)


def game_loop():
    """ Initialize and run game loop. """

    assets.set_globs(d=DIFFICULTY)
    assets.set_image_dicts()

    # Initialize internal variables
    score_text = FONT_3.render("0", True, (0, 0, 0))
    score = 0
    phago_count = 0
    running = True
    mouse_pressed = False
    timed_out = False
    phago_locs = None
    start_loc = None
    prev_loc = None
    particle_profile = None

    timer = 1
    tick_count = 0

    # Set caption
    pg.display.set_caption(GAMETITLE)

    # Initialize sprite groups
    APs = pg.sprite.Group()
    trapped_cargo = pg.sprite.Group()
    all_cargo, good_cargo, particle_cargo = spawn_cargo()

    # Add background
    game_bg = pg.image.load(str(DIR_PATH / "images" / "full_background.png")).convert()
    game_bg = pg.transform.scale(game_bg, (WIDTH, HEIGHT))
    PAS_image = pg.image.load(str(DIR_PATH / "images" / "PAS.png")).convert()
    PAS_image = pg.transform.scale(PAS_image, (mod(210), mod(210)))
    PAS_image.set_colorkey(BLACK)

    # Main game loop
    while running:      

        SCREEN.blit(game_bg, (0, 0))
        # SCREEN.fill(BACKGROUND_BLUE)

        # Allow for closing
        for event in pg.event.get():
            exit_check(event)
            
            # Add quit option
            if event.type == KEYDOWN:
                if event.key == K_q:
                    for sprite in all_cargo:
                        sprite.kill()
                        score = 0

        #Handle timing
        tick_count += 1
        if tick_count >= TICKRATE:
            # Chance of fission every second
            all_cargo, good_cargo = fission_mito(all_cargo, good_cargo)
            
            tick_count = 0
            timer += 1

        # Update cargo and particles on screen
        particle_cargo.update()
        particle_cargo.draw(SCREEN)
        all_cargo.update()
        all_cargo.draw(SCREEN)

        # Store mouse position for current frame
        cur_loc = pg.mouse.get_pos()

        # Handle AP acceleration due to mouse dragging
        for AP in APs:
            dead_AP = AP
            AP.handle_event(event, prev_loc, cur_loc)
            AP.update(SCREEN)
            AP.draw(SCREEN)

            # Purge cargo sprites and generate particle profile if AP has left screen
            if len(APs) == 0:
                score += purge_cargo(all_cargo)
                particle_profile = ParticleProfile(dead_AP)

        # Spawn particles if necessary
        if particle_profile is not None and particle_profile.queue > 0:
            particle_cargo = particle_profile.spawn(2, particle_cargo)

        # Redraw trapped cargo to bring to front
        trapped_cargo.draw(SCREEN)

        #-----------------------------PHAGOPHORE HANDLING--------------------------
        if len(APs) < 1:
            # Mouse pressed
            if pg.mouse.get_pressed()[0]:
                if not timed_out:
                    # Initial presss
                    if not mouse_pressed:
                        start_loc = cur_loc
                        phago_locs = []
                        mouse_pressed = True

                    phago_locs.append(cur_loc)

                    # Check for phagophore drawing timeout
                    distance = get_distance(start_loc, cur_loc)
                    if len(phago_locs) >= TIMEOUT_THRESH[DIFFICULTY]:
                        if distance >= HIT_CIRCLE_RADIUS:
                            _pill = Pill(score_val=TIMEOUT_PENALTY)
                            all_cargo.add(_pill)
                            SCREEN.fill(RED)
                        # If the circle was completed
                        else:
                            AP = Autophagosome(phago_locs)
                            if AP.area > MIN_AREA:
                                APs.add(AP)
                                phago_count += 1
                                trapped_cargo = check_trapped(APs, all_cargo)

                        timed_out = True
                        start_loc, phago_locs = None, None

            # Mouse released
            elif not pg.mouse.get_pressed()[0]:
                if timed_out:
                    timed_out = False
                    mouse_pressed = False
                # Initial release
                elif mouse_pressed and not timed_out:
                    # If the circle was completed
                    distance = get_distance(start_loc, cur_loc)
                    if distance >= HIT_CIRCLE_RADIUS:
                        score -= MISS_PENALTY
                        phago_count += 1
                    # If circle was not completed
                    else:
                        AP = Autophagosome(phago_locs)
                        if AP.area > MIN_AREA:
                            APs.add(AP)
                            phago_count += 1
                            trapped_cargo = check_trapped(APs, all_cargo)

                    start_loc, phago_locs = None, None
                    mouse_pressed = False

            # Draw phagophore
            if phago_locs is not None:
                if len(phago_locs) > 2:
                    # Draw outer line
                    last_loc = phago_locs[0]
                    for loc in phago_locs[1:]:
                        pg.draw.circle(SCREEN, PHAGO_LIGHT, (last_loc[0], last_loc[1]), mod(31))
                        aaline(SCREEN, PHAGO_LIGHT, last_loc, loc, mod(60))                   
                        last_loc = loc

                    # Draw inner line
                    last_loc = phago_locs[0]
                    for loc in phago_locs[1:]:
                        pg.draw.circle(SCREEN, PHAGO_DARK, (last_loc[0], last_loc[1]), mod(11))
                        aaline(SCREEN, PHAGO_DARK, last_loc, loc, mod(23))                     
                        last_loc = loc

            # Draw PAS
            if start_loc is not None:
                # Define function to get image print location based on click location
                shift = lambda x, y: (x-mod(105), y-mod(105))
                SCREEN.blit(PAS_image, shift(*start_loc))
                # pg.draw.circle(SCREEN, PHAGO_LIGHT, start_loc, mod(100))
                PAS_label = FONT_4.render(("PAS"), True, (0, 0, 0))
                text_x, text_y = start_loc
                SCREEN.blit(PAS_label, (text_x-32, text_y-25))

        prev_loc = cur_loc

        # Display score
        score = int(score)
        score_text = FONT_3.render(str(score), True, (0, 0, 0))
        SCREEN.blit(score_text, mod(15, 0))
        
        # FPS counter
        # fps = str(int(clock.get_fps()))
        # fps_text = FONT_3.render(fps, True, (0, 0, 0))
        # SCREEN.blit(fps_text, (500, 10))

        # Display phagophore count
        phago_count_text = FONT_3.render(str(phago_count), True, (0, 0, 0))
        x_pos = (WIDTH - phago_count_text.get_size()[0]) - mod(40)
        SCREEN.blit(phago_count_text, (x_pos, 0))

        # Check for end of game
        if len(good_cargo) < 1:
            running = False
            end_screen(str(score))

        # Refresh Screen
        pg.display.flip()

        # Set number of frames per second
        clock.tick(TICKRATE)

intro_screen()
pg.quit()
sys.exit()