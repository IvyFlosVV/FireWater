"""
level.py
========
Defines the Level class and the LEVELS list that drives level progression.

HOW LEVELS WORK
───────────────
Each entry in LEVELS is a plain Python dict describing the layout:
  • platforms  — solid collidable rects (list of (x, y, w, h) tuples)
  • pools      — hazardous liquids      (list of (x, y, w, h, type) tuples)
  • gems       — collectibles           (list of (x, y, type) tuples)
  • buttons    — pressure plates        (list of (x, y, gate_index) tuples)
  • gates      — closable barriers      (list of (x, y, w, h) tuples)
  • fire_door, water_door — exit rects  ((x, y, w, h))
  • spawn_fire, spawn_water — player starts ((x, y))
  • name       — displayed on the HUD

Level.__init__() converts these raw tuples into pygame.Rect objects and
wraps them in the dicts that Player.update() and Level.draw() expect.

ADDING A NEW LEVEL
──────────────────
1. Append a new dict to LEVELS (see existing entries for the schema).
2. Place platforms, pools, doors, and spawns.
3. Optionally add gems, buttons, gates.
4. The game will automatically include it in level progression.

COORDINATE SYSTEM
─────────────────
  Origin (0, 0) is the top-left corner of the window.
  x increases rightward.
  y increases downward.

  Screen dimensions: SCREEN_W × SCREEN_H  (900 × 600).
  Border walls:
    Left  wall  → x = 0,         width = 18
    Right wall  → x = 882,       width = 18
    Ceiling     → y = 0,         height = 18
    Floor/ground → y = 550,      height = 50
"""

import pygame
from constants import *


# ═══════════════════════════════════════════════════════════════════════════════
# RAW LEVEL DATA
# ═══════════════════════════════════════════════════════════════════════════════

LEVELS = [

    # ─────────────────────────────────────────────────────────────────────────
    # LEVEL 1  "The Crystal Temple"
    # Tutorial level — introduces the basic mechanics:
    #   • Two characters, separate controls
    #   • Lava kills Watergirl, water kills Fireboy
    #   • Both must reach their doors to win
    #   • Red gems for Fireboy, blue gems for Watergirl
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name":        "The Crystal Temple",
        "spawn_fire":  (55,  460),    # Fireboy starts left side
        "spawn_water": (120, 460),    # Watergirl just to the right

        # (x, y, width, height)
        "platforms": [
            # ── Borders ──────────────────────────────────────────────────────
            (0,   0,   18,  600),    # left wall
            (882, 0,   18,  600),    # right wall
            (0,   0,   900, 18 ),    # ceiling
            (0,   550, 900, 50 ),    # ground floor

            # ── Interior geometry ─────────────────────────────────────────────
            # Left raised ledge — Fireboy can reach the lava side above
            (110, 450, 160, 16),
            # Middle floating platform — spans the central gap
            (330, 370, 240, 16),
            # Right raised ledge — Watergirl side
            (630, 450, 160, 16),
            # Small step up to the doors (right side)
            (790, 490, 110, 16),
        ],

        # (x, y, width, height, pool_type)
        # pool_type ∈ {"lava", "water", "poison"}
        "pools": [
            (210, 532, 110, 18, "lava" ),   # lava trench — lethal to Watergirl
            (580, 532, 110, 18, "water"),   # water trench — lethal to Fireboy
        ],

        # Fire door + water door: (x, y, width, height)
        # Positioned on the right-side step, flush with the right wall.
        "fire_door":  (818, 421, DOOR_W, DOOR_H),
        "water_door": (852, 421, DOOR_W, DOOR_H),

        # (x, y, gem_type)  — gem_type ∈ {"red", "blue"}
        "gems": [
            # Left-ledge red gems (Fireboy)
            (125, 428, "red"), (165, 428, "red"), (205, 428, "red"),
            # Middle platform blue gems (Watergirl)
            (360, 348, "blue"), (420, 348, "blue"), (480, 348, "blue"),
            # Right-ledge red gem bonus
            (650, 428, "red"),
        ],

        # No buttons or gates in the tutorial level
        "buttons": [],
        "gates":   [],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # LEVEL 2  "The Cavern of Cooperation"
    # Introduces the pressure-button / gate mechanic:
    #   • One player must stand on a button to open a gate
    #   • The other player passes through while the gate is held open
    #   • Releasing the button closes the gate again
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name":        "The Cavern of Cooperation",
        "spawn_fire":  (40,  460),
        "spawn_water": (100, 460),

        "platforms": [
            # ── Borders ──────────────────────────────────────────────────────
            (0,   0,   18,  600),
            (882, 0,   18,  600),
            (0,   0,   900, 18 ),
            (0,   550, 900, 50 ),

            # ── Left section ──────────────────────────────────────────────────
            # Low platform — jump over the lava pit
            (18,  480, 120, 16),
            # Mid-left ledge
            (18,  350, 180, 16),
            # Tall left pillar (wall-like)
            (340, 200, 16,  350),

            # ── Right section ─────────────────────────────────────────────────
            # Platform directly after the gate gap
            (430, 350, 200, 16),
            # Upper right ledge
            (680, 260, 180, 16),
            # Step to doors
            (790, 460, 110, 16),
        ],

        "pools": [
            # Large lava channel in the left section
            (140, 532, 180, 18, "lava"),
            # Smaller water puddle right section
            (500, 532, 140, 18, "water"),
            # Poison pool in the middle (kills both)
            (355, 532, 70,  18, "poison"),
        ],

        "fire_door":  (818, 391, DOOR_W, DOOR_H),
        "water_door": (852, 391, DOOR_W, DOOR_H),

        "gems": [
            # Left mid-ledge red gems
            (30,  328, "red"), (80, 328, "red"), (130, 328, "red"),
            # Right platform blue gems
            (450, 328, "blue"), (510, 328, "blue"), (570, 328, "blue"),
            # Upper right ledge — bonus mixed gems
            (690, 238, "red"), (740, 238, "blue"),
        ],

        # Pressure buttons: (x, y, gate_index)
        # gate_index ties this button to gates[gate_index]
        "buttons": [
            # Button sits on top of the pillar at x=340 — right edge
            # Fireboy must stand here to open the gate beside the pillar
            (310, 469, 0),   # on the ground left of the pillar, gate_index=0
        ],

        # Gates: (x, y, width, height)
        # Gate 0 is a vertical barrier just right of the pillar
        # When closed it blocks the narrow gap between pillar and right section.
        "gates": [
            (356, 200, GATE_W, 350),   # tall gate filling the gap in the pillar
        ],
    },

    # ─────────────────────────────────────────────────────────────────────────
    # LEVEL 3  "The High Road"
    # A tall vertical level — players must ascend via staggered platforms.
    # More complex pool layout; Fireboy and Watergirl paths diverge then reunite.
    # ─────────────────────────────────────────────────────────────────────────
    {
        "name":        "The High Road",
        "spawn_fire":  (40,  460),
        "spawn_water": (100, 460),

        "platforms": [
            # ── Borders ──────────────────────────────────────────────────────
            (0,   0,   18,  600),
            (882, 0,   18,  600),
            (0,   0,   900, 18 ),
            (0,   550, 900, 50 ),

            # ── Ground-level platforms ────────────────────────────────────────
            (18,  490, 200, 16),
            (680, 490, 200, 16),

            # ── First tier ────────────────────────────────────────────────────
            (80,  390, 160, 16),
            (420, 390, 160, 16),
            (660, 390, 200, 16),

            # ── Second tier ───────────────────────────────────────────────────
            (18,  290, 200, 16),
            (340, 290, 180, 16),
            (700, 290, 160, 16),

            # ── Third tier ────────────────────────────────────────────────────
            (130, 200, 200, 16),
            (500, 200, 260, 16),

            # ── Top ledge → doors ─────────────────────────────────────────────
            (790, 120, 110, 16),
        ],

        "pools": [
            # Ground floor hazards — force players to jump to the side platforms
            (240, 532, 160, 18, "lava"  ),
            (500, 532, 160, 18, "water" ),
            # Mid-level hazards
            (260, 370, 140, 20, "poison"),
            (530, 370, 110, 20, "lava"  ),
        ],

        "fire_door":  (818, 51, DOOR_W, DOOR_H),
        "water_door": (852, 51, DOOR_W, DOOR_H),

        "gems": [
            # Ground platforms
            (100, 468, "red" ), (150, 468, "red" ),
            (700, 468, "blue"), (750, 468, "blue"),
            # First tier
            (100, 368, "red" ), (440, 368, "blue"), (680, 368, "red" ),
            # Second tier
            (80,  268, "blue"), (360, 268, "red" ), (720, 268, "blue"),
            # Third tier
            (150, 178, "red" ), (520, 178, "blue"), (620, 178, "blue"),
        ],

        "buttons": [
            # Button on the top ledge → opens gate blocking door access
            (760, 469, 0),
        ],

        "gates": [
            # Gate across the top-ledge approach (right side, mid-height)
            (790, 136, GATE_W, 120),
        ],
    },
]


# ═══════════════════════════════════════════════════════════════════════════════
# LEVEL CLASS
# ═══════════════════════════════════════════════════════════════════════════════

class Level:
    """
    Holds all runtime state for a single level, converted from the raw LEVELS
    dict into pygame.Rect objects and interaction-ready data structures.

    The Level is responsible for:
      • Storing geometry (platforms, pools, gems, gates, buttons, doors)
      • Updating button-press state each frame (before players are updated)
      • Drawing all level elements onto the screen surface
      • Providing the pulsing color animation for hazard pools
    """

    # How fast pools pulse (frames per full color cycle)
    POOL_PULSE_PERIOD = 90

    def __init__(self, data: dict):
        """
        Build a Level from a raw data dict (one entry from LEVELS).

        Parameters
        ----------
        data : dict
            A single entry from the LEVELS list above.
        """
        self.name = data["name"]

        # ── Spawn positions ───────────────────────────────────────────────────
        self.spawn_fire  = data["spawn_fire"]
        self.spawn_water = data["spawn_water"]

        # ── Solid platforms ───────────────────────────────────────────────────
        # Stored as plain pygame.Rects — passed directly to Player._resolve_x/y.
        self.platforms = [
            pygame.Rect(x, y, w, h)
            for x, y, w, h in data["platforms"]
        ]

        # ── Hazard pools ──────────────────────────────────────────────────────
        # Each pool is a dict so Player.update() can read pool["type"].
        self.pools = [
            {"rect": pygame.Rect(x, y, w, h), "type": ptype}
            for x, y, w, h, ptype in data["pools"]
        ]

        # ── Exit doors ────────────────────────────────────────────────────────
        # Stored in a dict so Player._check_door() can look them up by key.
        fx, fy, fw, fh = data["fire_door"]
        wx, wy, ww, wh = data["water_door"]
        self.doors = {
            "fire":  pygame.Rect(fx, fy, fw, fh),
            "water": pygame.Rect(wx, wy, ww, wh),
        }

        # ── Gems ──────────────────────────────────────────────────────────────
        self.gems = [
            {
                "rect":      pygame.Rect(gx - GEM_R, gy - GEM_R, GEM_R*2, GEM_R*2),
                "type":      gtype,
                "collected": False,
            }
            for gx, gy, gtype in data["gems"]
        ]

        # ── Buttons ───────────────────────────────────────────────────────────
        # Each button carries its current pressed state and a pointer to its gate.
        self.buttons = [
            {
                "rect":       pygame.Rect(bx, by, BTN_W, BTN_H),
                "pressed":    False,
                "gate_index": gi,
            }
            for bx, by, gi in data["buttons"]
        ]

        # ── Gates ─────────────────────────────────────────────────────────────
        # Gates start closed.  Player._check_buttons() sets open = True while
        # a player stands on the linked button.
        self.gates = [
            {"rect": pygame.Rect(gx, gy, gw, gh), "open": False}
            for gx, gy, gw, gh in data["gates"]
        ]

        # ── Animation counter ─────────────────────────────────────────────────
        self._tick = 0   # incremented each update(); drives pool pulsing

    # ─────────────────────────────────────────────────────────────────────────
    # UPDATE
    # ─────────────────────────────────────────────────────────────────────────

    def update(self, players):
        """
        Update level-side state for one frame.

        This must be called BEFORE Player.update() each frame so that gate
        state is correct when players resolve collisions.

        Steps:
          1. Increment animation tick.
          2. Reset all button pressed states to False.
             (Player.update() will set them back to True if a player is on them.)
          3. Close all gates that have no player pressing their button.
             (Gate opens in Player._check_buttons(); closes here if not pressed.)

        Parameters
        ----------
        players : list[Player]
            Both players — used to determine which buttons are currently pressed.
        """
        self._tick += 1

        # Reset button states — players will re-press them during their update()
        for btn in self.buttons:
            btn["pressed"] = False

        # Close all gates; they'll reopen if a button is pressed this frame
        for gate in self.gates:
            gate["open"] = False

    # ─────────────────────────────────────────────────────────────────────────
    # DRAW
    # ─────────────────────────────────────────────────────────────────────────

    def draw(self, surface):
        """
        Render the full level onto *surface* (background drawn by Game).

        Draw order (painter's algorithm — back to front):
          1. Platforms
          2. Hazard pools (with pulsing color)
          3. Gems (uncollected only)
          4. Pressure buttons
          5. Gates (with open/closed color)
          6. Exit doors (with active glow if player is at door)
        """
        self._draw_platforms(surface)
        self._draw_pools(surface)
        self._draw_gems(surface)
        self._draw_buttons(surface)
        self._draw_gates(surface)
        self._draw_doors(surface)

    def draw_doors_active(self, surface, fireboy, watergirl):
        """
        Re-draw just the doors with an active glow when players are at them.
        Called after players are drawn so the glow appears on top.
        """
        # Fire door glow
        if fireboy.at_door:
            glow = self.doors["fire"].inflate(6, 6)
            pygame.draw.rect(surface, FIRE_DOOR_ACTIVE, glow, border_radius=5)
        # Water door glow
        if watergirl.at_door:
            glow = self.doors["water"].inflate(6, 6)
            pygame.draw.rect(surface, WATER_DOOR_ACTIV, glow, border_radius=5)

    # ─────────────────────────────────────────────────────────────────────────
    # PRIVATE DRAW HELPERS
    # ─────────────────────────────────────────────────────────────────────────

    def _draw_platforms(self, surface):
        """
        Draw each platform as a filled rect with a highlight edge on top.
        The highlight gives the platforms a beveled, stone-like appearance.
        """
        for plat in self.platforms:
            pygame.draw.rect(surface, PLATFORM_COLOR, plat)
            # Top-edge highlight (1 px lighter stripe)
            highlight = pygame.Rect(plat.x, plat.y, plat.width, 3)
            lighter = tuple(min(255, c + 40) for c in PLATFORM_COLOR)
            pygame.draw.rect(surface, lighter, highlight)
            # Outline
            pygame.draw.rect(surface, BLACK, plat, 1)

    def _draw_pools(self, surface):
        """
        Draw hazard pools with a two-color pulse animation.

        The pulse is driven by self._tick.  A sine-like interpolation between
        color_A and color_B creates a gentle "bubbling" visual.
        """
        # Compute blend factor in [0.0, 1.0] using triangle wave
        phase = (self._tick % self.POOL_PULSE_PERIOD) / self.POOL_PULSE_PERIOD
        t = phase * 2 if phase < 0.5 else 2 - phase * 2   # triangle wave

        for pool in self.pools:
            ptype = pool["type"]

            if ptype == "lava":
                a, b = LAVA_COL_A, LAVA_COL_B
            elif ptype == "water":
                a, b = WATER_COL_A, WATER_COL_B
            else:  # poison
                a, b = POISON_COL_A, POISON_COL_B

            # Linear interpolation between a and b
            col = tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))

            rect = pool["rect"]
            pygame.draw.rect(surface, col, rect, border_radius=3)
            # Subtle inner highlight line
            inner = pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, 3)
            lighter = tuple(min(255, c + 60) for c in col)
            pygame.draw.rect(surface, lighter, inner, border_radius=1)

    def _draw_gems(self, surface):
        """
        Draw uncollected gems as filled circles with a small specular dot.
        Collected gems are skipped — they've been "taken" from the level.
        """
        for gem in self.gems:
            if gem["collected"]:
                continue
            cx = gem["rect"].centerx
            cy = gem["rect"].centery
            col = RED_GEM_COL if gem["type"] == "red" else BLUE_GEM_COL
            pygame.draw.circle(surface, col,      (cx, cy), GEM_R)
            pygame.draw.circle(surface, BLACK,    (cx, cy), GEM_R, 1)
            # Specular highlight (upper-left)
            pygame.draw.circle(surface, GEM_SHINE, (cx - 3, cy - 3), 2)

    def _draw_buttons(self, surface):
        """
        Draw pressure buttons as flat slabs.  Color shifts when pressed.
        A small arrow drawn on top indicates which gate the button controls.
        """
        for btn in self.buttons:
            col = BTN_PRESS_COL if btn["pressed"] else BTN_COLOR
            pygame.draw.rect(surface, col, btn["rect"], border_radius=3)
            pygame.draw.rect(surface, BLACK, btn["rect"], 1, border_radius=3)

    def _draw_gates(self, surface):
        """
        Draw closed gates as striped barriers.  Open gates become faint outlines
        so the player can see the gap is passable.
        """
        for gate in self.gates:
            r = gate["rect"]
            if gate["open"]:
                # Faint outline only — gate is retracted
                pygame.draw.rect(surface, GATE_OPEN_COL, r, 2)
            else:
                # Solid filled gate with diagonal stripes
                pygame.draw.rect(surface, GATE_COLOR, r)
                pygame.draw.rect(surface, BLACK, r, 2)
                # Draw 3 horizontal stripes to imply "bars"
                stripe_h = max(4, r.height // 8)
                for i in range(1, 4):
                    sy = r.y + i * (r.height // 4)
                    pygame.draw.line(surface, BLACK,
                                     (r.x + 2, sy), (r.right - 2, sy), 2)

    def _draw_doors(self, surface):
        """
        Draw the two exit doors as tall arched rects.

        Each door shows its character color.  An arch is approximated by
        drawing the rect body plus a circle cap on top.
        """
        door_data = [
            (self.doors["fire"],  FIRE_DOOR_COLOR),
            (self.doors["water"], WATER_DOOR_COLOR),
        ]
        for rect, base_col in door_data:
            # Door body
            pygame.draw.rect(surface, base_col, rect, border_radius=4)
            pygame.draw.rect(surface, BLACK,    rect, 2,  border_radius=4)
            # Arch cap (semicircle at the top)
            cap_cx = rect.centerx
            cap_cy = rect.top
            cap_r  = rect.width // 2
            pygame.draw.circle(surface, base_col, (cap_cx, cap_cy), cap_r)
            pygame.draw.circle(surface, BLACK,    (cap_cx, cap_cy), cap_r, 2)
            # Inner door panel
            inner = rect.inflate(-8, -10)
            inner.top = rect.top + 8
            darker = tuple(max(0, c - 60) for c in base_col)
            pygame.draw.rect(surface, darker, inner, border_radius=2)