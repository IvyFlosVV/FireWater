"""
main.py
=======
Entry point for Fireboy & Watergirl.

Run this file to start the game:
    python main.py

Requirements
────────────
    pip install pygame

How the project is structured
──────────────────────────────
    main.py       ← you are here — initializes pygame, creates Game, starts loop
    game.py       ← Game class: FSM, event loop, HUD, overlays, particles
    player.py     ← Player class: physics, collision, interactions
    level.py      ← Level class + LEVELS data: geometry, pools, gems, doors
    constants.py  ← all magic numbers in one place (sizes, colors, physics)

Controls
────────
    Fireboy   → Arrow keys   (← move left  |  → move right  |  ↑ jump)
    Watergirl → WASD keys    (A  move left  |  D  move right |  W jump)

Goal
────
    Both characters must reach their color-matched exit door at the same time.
    Fireboy dies in water or poison pools.
    Watergirl dies in lava  or poison pools.
    Collect gems along the way for a high score.
"""

import pygame
import sys
from game import Game


def main():
    """
    Initialize pygame and hand control to the Game object.

    Putting initialization here (rather than inside Game.__init__) keeps the
    Game class unit-testable — tests can import Game without triggering a
    display window.
    """
    pygame.init()
    pygame.display.set_caption("Fireboy & Watergirl")

    game = Game()
    game.run()

    # Clean shutdown after the game loop exits
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()