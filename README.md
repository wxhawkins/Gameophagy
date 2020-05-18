## Overview

It's a game...about autophagy. Try to catch all of the intracellular cargo in the smallest number of autophagosomes. Why are you trying to degrade *everything*? IDK, man; it's a game made by a grad student in a state of severe, pandemic-induced boredom -- don't overthink this.

## Getting started

**If you're on Windows**, you can simply download the stand-alone release. Go to Gameophagy releases and download the most recent release, unzip the files and find the file "main.exe" in "Gamophagy/dist/main/main.exe". Create a shortcut to this file, place it wherever you want and use it to launch the game -- done.

Otherwise, clone/download the repository. You will need a recent version of python (3.8 used for development) and the package pygame (1.9.6 used for development). Begin the game by running "main.py".

## Game instructions

Select your difficulty on the introduction page. The harder the difficulty, the less time you have to draw the phagophore, the faster cargo moves but the more points you get per cargo item. After selecting "Play", left click the screen and drag to draw a phagophore; your mouse must end within the large circle marking the starting location. And be fast -- there's a time limit for drawing.  Upon phagophore closure, hold left-click on the autophagosome, drag, and then release to send it to the vacuole for degradation. If you run out of time while drawing a phagophore, an autophagy inhibitor pill spawns. Avoid capturing these as they will lower your score.

![image-20200518151940441](./images/intro_page.jpg)

![image-20200518152515181](./images/game_loop_page.jpg)

![image-20200518152450191](./images/end_page.jpg)
