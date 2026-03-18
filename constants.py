"""
constants.py
============
Central configuration for Fireboy & Watergirl.

WHY a separate constants file?
  • Every "magic number" lives in ONE place — tweak physics, colors, or
    sizes without grep-and-replacing across five files.
  • Other modules do `from constants import *` and immediately have access
    to every shared value.
  • New contributors can read this file first to understand the game's
    fundamental settings before diving into logic.
"""

# ═══════════════════════════════════════════════════════════════════════════════
# DISPLAY
# ═══════════════════════════════════════════════════════════════════════════════

SCREEN_W = 900        # Window width  in pixels
SCREEN_H = 600        # Window height in pixels
FPS      = 60         # Target frames per second
TITLE    = "Fireboy & Watergirl – The Crystal Temple"

# ═══════════════════════════════════════════════════════════════════════════════
# PHYSICS
# ═══════════════════════════════════════════════════════════════════════════════

GRAVITY        = 0.55   # px / frame²  — added to vel_y every frame
JUMP_FORCE     = -12.5  # initial vel_y when the player jumps (negative = up)
MOVE_SPEED     = 4      # horizontal pixels moved per frame while key is held
MAX_FALL_SPEED = 14     # terminal velocity — prevents tunnelling thin floors

# ═══════════════════════════════════════════════════════════════════════════════
# ENTITY SIZES (pixels)
# ═══════════════════════════════════════════════════════════════════════════════

PLAYER_W  = 28   # player bounding-box width
PLAYER_H  = 42   # player bounding-box height
GEM_R     = 8    # gem circle radius
DOOR_W    = 34   # door width
DOOR_H    = 70   # door height
BTN_W     = 40   # pressure-button width
BTN_H     = 12   # pressure-button height (flat slab)
GATE_W    = 16   # gate / barrier width
# Gate height is set per-level in the level data (gates can be different heights)

# ═══════════════════════════════════════════════════════════════════════════════
# COLORS  (R, G, B)
# ═══════════════════════════════════════════════════════════════════════════════

# ── Neutrals ──────────────────────────────────────────────────────────────────
BLACK     = (0,   0,   0  )
WHITE     = (255, 255, 255)
BG_COLOR  = (18,  18,  28 )   # deep navy — feels like a dark temple

# ── Environment ───────────────────────────────────────────────────────────────
PLATFORM_COLOR = (90,  70,  50 )   # earthy stone-brown platforms
WALL_COLOR     = (60,  50,  35 )   # darker variant for border walls
GATE_COLOR     = (140, 110, 60 )   # closed gate / barrier color
GATE_OPEN_COL  = (60,  50,  30 )   # faded — gate is open (barely visible)
BTN_COLOR      = (160, 140, 90 )   # unpressed button slab
BTN_PRESS_COL  = (100, 85,  50 )   # pressed button slab

# ── Characters ────────────────────────────────────────────────────────────────
FIREBOY_COLOR   = (220, 55,  10 )   # vivid orange-red
WATERGIRL_COLOR = (20,  110, 220)   # bright cerulean blue

# ── Hazard pools ──────────────────────────────────────────────────────────────
LAVA_COL_A   = (255, 80,  0  )   # lava highlight   (pulsing animation frame A)
LAVA_COL_B   = (200, 50,  0  )   # lava shadow      (pulsing animation frame B)
WATER_COL_A  = (20,  150, 255)   # water highlight
WATER_COL_B  = (10,  100, 200)   # water shadow
POISON_COL_A = (30,  200, 30 )   # poison highlight
POISON_COL_B = (15,  140, 15 )   # poison shadow

# ── Doors ─────────────────────────────────────────────────────────────────────
FIRE_DOOR_COLOR  = (180, 30,  0  )   # dark red
FIRE_DOOR_ACTIVE = (255, 100, 30 )   # glowing when player is at the door
WATER_DOOR_COLOR = (0,   60,  180)   # dark blue
WATER_DOOR_ACTIV = (60,  180, 255)   # glowing when player is at the door

# ── Gems ──────────────────────────────────────────────────────────────────────
RED_GEM_COL  = (255, 60,  60 )
BLUE_GEM_COL = (60,  60,  255)
GEM_SHINE    = (255, 255, 255)   # tiny specular dot on each gem

# ── HUD & UI ──────────────────────────────────────────────────────────────────
HUD_TEXT_COL  = (220, 220, 220)
WIN_COL       = (255, 215, 0  )   # gold
DEAD_COL      = (200, 50,  50 )
OVERLAY_ALPHA = 160              # 0-255 alpha for semi-transparent overlays

# ═══════════════════════════════════════════════════════════════════════════════
# CONTROLS  (mapped to pygame.K_* constants — imported in player.py)
# ═══════════════════════════════════════════════════════════════════════════════
# Stored here so levels / game code can reference them without importing pygame.
# The actual pygame.K_* values are assigned in player.py after `import pygame`.
#
#   Fireboy  → Arrow keys:   LEFT / RIGHT / UP
#   Watergirl → WASD keys:   A / D / W