import datetime
import json
import sys
from pathlib import Path

import pygame as pg
from pygame.locals import *

# Import personal files
from assets import Autophagosome, Cargo, Button
from misc_functions import get_distance, in_bounds

# Define working directory
DIR_PATH = Path.cwd().parent
# Modify DIR_PATH if game is being run from executable
if DIR_PATH.name == "dist":
    DIR_PATH = Path.cwd().parent.parent

# Define colors
GRAY = (80, 80, 80)
RED = (255, 0, 0)
BACKGROUND_BLUE = (144, 226, 222)
PHAGO_GREEN_DARK =  (0, 138, 70)

GAMETITLE = "Gameophagy"
SCREENWIDTH = 1900
SCREENHEIGHT = 1000
HIT_CIRCLE_RADIUS = 100
MITO_NUM = 5
RIBO_NUM = 20
RNA_NUM = 10
TIMEOUT_THRESH = {"Easy": 240, "Medium": 60, "Hard": 20}
TIMEOUT_PENALTY = -300
MISS_PENALTY = 50
MAKE_PENALTY = 200
MIN_AREA = 20000

# Define fonts
pg.font.init()
conthrax_path = str(DIR_PATH / "fonts" / "conthrax.ttf")
FONT_1 = pg.font.Font(conthrax_path, 130)
FONT_2 = pg.font.Font(conthrax_path, 80)
FONT_3 = pg.font.Font(conthrax_path, 60)
FONT_4 = pg.font.Font(conthrax_path, 30)

# Initialize game
pg.init()
clock = pg.time.Clock()
pg.display.set_caption(GAMETITLE)
SCREEN = pg.display.set_mode((SCREENWIDTH, SCREENHEIGHT))
DIFFICULTY = None


def check_trapped(APs, items):
    """
        Checks if any cargo items were inside upon AP formation then update
        cargo and AP parameters accordingly.
    """

    for AP in APs:
        for item in items:
            distance = get_distance(AP.rect.center, item.rect.center)
            if distance < AP.radius:
                item.trapped = True
                AP.contents.append(item)


def purge_cargo(all_sprites_group):
    """ Kill captured sprites and update score accordingly. """

    score_change = 0
    for sprite in all_sprites_group:
        if not in_bounds(sprite):
            score_change += sprite.score_val
            sprite.kill()

    return score_change


def inactivate_buttons(buttons):
    """ Inactive buttons due to mutual exclusivity. """

    for button in buttons:
        if button.text != DIFFICULTY:
            button.active = False


def intro_screen():
    """ Show introduciton screen and acquire difficulty setting. """

    # Set up intro screen background
    into_bg = pg.image.load(str(DIR_PATH / "images" / "start_screen_basic.png")).convert()
    into_bg = pg.transform.scale(into_bg, (SCREENWIDTH, SCREENHEIGHT))
    SCREEN.blit(into_bg, (0, 0))

    # Set up title
    title = FONT_1.render(GAMETITLE, True, GRAY)
    SCREEN.blit(title, (40, 21))

    pg.display.update()

    # Initalize buttons
    play_button = Button(1580, 150, 250, 105, FONT_3, "Play", callback_=game_loop)
    easy_button = Button(1250, 70, 180, 60, FONT_4, "Easy", toggle_=True)
    med_button = Button(1450, 70, 180, 60, FONT_4, "Medium", toggle_=True)
    hard_button = Button(1650, 70, 180, 60, FONT_4, "Hard", toggle_=True)
    buttons = [play_button, easy_button, med_button, hard_button]

    # Initalize difficulty
    global DIFFICULTY
    DIFFICULTY = "Medium"
    med_button.active = True

    # Intro page loop
    intro = True
    while intro:
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

    # Read in high scores from JSON
    try:
        with open((DIR_PATH / "scores" / "high_scores.json"), "r") as in_file:
            score_list = json.loads(in_file.read())
    
        # Add line for current game
        cur_date = datetime.date.today()
        cur_date_fmt = f"{cur_date.month}/{cur_date.day}/{cur_date.year}"
        score_list.append({"score": score, "difficulty": DIFFICULTY, "date": cur_date_fmt})    

        # Update high scores JSON
        with open((DIR_PATH / "scores" / "high_scores.json"), "w") as out_file:
            json.dump(score_list, out_file, indent=4)
    
    # If error encountered, reset high scores file and try again
    except json.decoder.JSONDecodeError:
        with open((DIR_PATH / "scores" / "high_scores.json"), "w") as out_file:
            out_file.write("[]")
        end_screen(score)

    play_button = Button(1300, 20, 425, 80, FONT_3, "Play again", callback_=intro_screen)

    # Show final score
    SCREEN.fill(BACKGROUND_BLUE)
    final_score_text = FONT_3.render(("Final Score: " + score), True, (0, 0, 0))
    SCREEN.blit(final_score_text, (100, 20))

    # Sort high scores
    score_list = sorted(score_list, key=lambda x: x["score"], reverse=True)

    # Show high scores
    for i, line in enumerate(score_list[:10]):
        core_text = FONT_3.render(line["score"], True, (0, 0, 0))
        diff_text = FONT_3.render(line["difficulty"], True, (0, 0, 0))
        date_text = FONT_3.render(line["date"], True, (0, 0, 0))
        SCREEN.blit(core_text, (100, 150 + (i * 80)))
        SCREEN.blit(diff_text, (700, 150 + (i * 80)))
        SCREEN.blit(date_text, (1300, 150 + (i * 80)))

    # End page loop
    while True:
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

    # Generate mitochondria
    for _ in range(MITO_NUM):
        _mito = Cargo(DIFFICULTY, "mito.png", x_dim=300, y_dim=165, score_val=100, x_speed_cap=7, y_speed_cap=7)
        all_cargo.add(_mito)
        good_cargo.add(_mito)

    # Generate ribosomes
    for _ in range(RIBO_NUM):
        _ribo = Cargo(DIFFICULTY, "ribo.png", x_dim=90, y_dim=90, score_val=50, x_speed_cap=15, y_speed_cap=15)
        all_cargo.add(_ribo)
        good_cargo.add(_ribo)

    # Generate RNAs
    for _ in range(RNA_NUM):
        _rna = Cargo(DIFFICULTY, "rna.png", x_dim=75, y_dim=300, score_val=150, x_speed_cap=2, y_speed_cap=12)
        all_cargo.add(_rna)
        good_cargo.add(_rna)

    return all_cargo, good_cargo


def game_loop():
    """ Initialize and run game loop. """

    # Initialize internal variables
    score_text = FONT_3.render("0", True, (0, 0, 0))
    score = 0
    running = True
    mouse_pressed = False
    timed_out = False
    phago_locs = None
    start_loc = None
    prev_loc = None

    # Set caption
    pg.display.set_caption(GAMETITLE)

    # Initialize sprite groups
    APs = pg.sprite.Group()
    all_cargo, good_cargo = spawn_cargo()

    # Main game loop
    while running:
        # Allow for closing
        for event in pg.event.get():
            exit_check(event)
            
            # Add quit option
            if event.type == KEYDOWN:
                if event.key == K_q:
                    for sprite in all_cargo:
                        sprite.kill()
                        score = 0

        # Add background
        SCREEN.fill(BACKGROUND_BLUE)

        # Store mouse position for current frame
        cur_loc = pg.mouse.get_pos()

        # Handle AP acceleration due to mouse dragging
        for AP in APs:
            AP.handle_event(event, prev_loc, cur_loc)
            AP.update(SCREEN)
            AP.draw(SCREEN)

            # Purge cargo sprites if AP has left screen
            if len(APs) == 0:
                score += purge_cargo(all_cargo)
                score -= MAKE_PENALTY

        # Update cargo on screen
        all_cargo.update()
        all_cargo.draw(SCREEN)

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
                    if len(phago_locs) > TIMEOUT_THRESH[DIFFICULTY]:
                        start_loc, phago_locs = None, None
                        timed_out = True
                        _pill = Cargo(DIFFICULTY, "pill.png", x_dim=(150), y_dim=(75), score_val=TIMEOUT_PENALTY, x_speed_cap=2, y_speed_cap=2)
                        all_cargo.add(_pill)
                        SCREEN.fill(RED)
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
                    # If circle was not completed
                    else:
                        AP = Autophagosome(phago_locs)
                        if AP.area > MIN_AREA:
                            APs.add(AP)
                            
                            # Freeze cargo within phagophore
                            check_trapped(APs, all_cargo)
                        

                    start_loc, phago_locs = None, None
                    mouse_pressed = False

            # Draw big starting point
            if start_loc is not None:
                pg.draw.circle(SCREEN, PHAGO_GREEN_DARK, start_loc, 100)

            # Draw phagophore
            if phago_locs is not None:
                if len(phago_locs) > 2:
                    last_loc = phago_locs[0]
                    for loc in phago_locs[1:]:
                        pg.draw.line(SCREEN, PHAGO_GREEN_DARK, last_loc, loc, 23)
                        last_loc = loc

        prev_loc = cur_loc

        # Display score
        score_text = FONT_3.render(str(score), True, (0, 0, 0))
        SCREEN.blit(score_text, (15, 0))

        # Check for end of game
        if len(good_cargo) < 1:
            running = False
            end_screen(str(score))

        # Refresh Screen
        pg.display.flip()

        # Set number of frames per second
        clock.tick(60)


intro_screen()
pg.quit()
sys.exit()
