"""
player.py
=========
Defines the Player class — the core entity for both Fireboy and Watergirl.

DESIGN OVERVIEW
───────────────
Rather than having two separate Fireboy / Watergirl classes (lots of
duplication), we use ONE Player class that is configured at construction time
with that character's specific:
  • color / visual identity
  • control keys   (arrow keys vs. WASD)
  • lethal pool types  (what kills this character)
  • gem type to collect

This follows the "composition over inheritance" principle — behavior differences
are expressed as data, not as subclass overrides.

PHYSICS MODEL
─────────────
The game uses a simple Euler-integration model:

    vel_y  +=  GRAVITY         # accelerate downward every frame
    rect.y +=  int(vel_y)      # move by current velocity

Horizontal movement is velocity-free (instant response to key presses) which
gives the snappy feel typical of the original Flash game.

COLLISION RESOLUTION
────────────────────
Platforms are solid on all four sides.  We resolve collisions in two separate
passes to avoid the "diagonal corner" glitch:

  1. Move horizontally → resolve horizontal overlaps (push left or right)
  2. Move vertically   → resolve vertical overlaps   (land on top / bonk head)

Resolving each axis independently is simpler and more stable than trying to
handle diagonal collisions simultaneously.
"""

import pygame
from constants import *


class Player:
    """
    A single playable character with gravity, jumping, and interaction logic.

    Parameters
    ----------
    spawn_x, spawn_y : int
        Top-left pixel position at the start of a level (and after reset).
    color : tuple[int,int,int]
        RGB fill color — also identifies which door and gems this player uses.
    lethal_pools : list[str]
        Pool types that kill this character.
        Fireboy  → ["water", "poison"]
        Watergirl → ["lava",  "poison"]
    left_key, right_key, jump_key : int
        pygame.K_* constants for movement controls.
    gem_type : str
        "red"  for Fireboy, "blue" for Watergirl.
    door_key : str
        "fire" for Fireboy, "water" for Watergirl — selects which door to use.
    label : str
        Human-readable name shown in the HUD ("Fireboy" / "Watergirl").

    Attributes (runtime state)
    --------------------------
    rect : pygame.Rect        — bounding box (position + size)
    vel_y : float             — current vertical velocity (positive = down)
    on_ground : bool          — True if standing on a platform this frame
    alive : bool              — False once a lethal pool is touched
    at_door : bool            — True while overlapping the matching exit door
    gems : int                — total gems collected this life
    facing_right : bool       — last horizontal direction (for eye placement)
    """

    def __init__(self, spawn_x, spawn_y, color, lethal_pools,
                 left_key, right_key, jump_key, gem_type, door_key, label):
        # ── Identity ──────────────────────────────────────────────────────────
        self.color        = color
        self.lethal_pools = lethal_pools   # e.g. ["water", "poison"]
        self.gem_type     = gem_type       # "red" or "blue"
        self.door_key     = door_key       # "fire" or "water"
        self.label        = label

        # ── Controls ──────────────────────────────────────────────────────────
        self.left_key  = left_key
        self.right_key = right_key
        self.jump_key  = jump_key

        # ── Spawn (used by reset()) ────────────────────────────────────────────
        self.spawn_x = spawn_x
        self.spawn_y = spawn_y

        # ── Runtime state — set properly by reset() ───────────────────────────
        self.rect         = pygame.Rect(spawn_x, spawn_y, PLAYER_W, PLAYER_H)
        self.vel_y        = 0.0
        self.on_ground    = False
        self.alive        = True
        self.at_door      = False
        self.gems         = 0
        self.facing_right = True   # tracks last horizontal direction for eye

    # ═══════════════════════════════════════════════════════════════════════════
    # PUBLIC API
    # ═══════════════════════════════════════════════════════════════════════════

    def update(self, platforms, pools, gems, doors, buttons, gates):
        """
        Advance the player by exactly one frame.

        This method is the "brain" of the character.  It must be called once
        per game loop tick while the level is active.

        Processing order
        ────────────────
        1. Early-exit if dead (dead players don't move or interact).
        2. Read keyboard input → horizontal movement.
        3. Apply gravity → vertical movement.
        4. Resolve collisions with platforms (horizontal pass, then vertical).
        5. Handle jump input (must come AFTER vertical collision so on_ground
           is accurate).
        6. Resolve collisions with open gates (gates are solid when closed).
        7. Check hazard pools → kill player if lethal pool touched.
        8. Check pressure buttons → press/release based on overlap.
        9. Check door overlap → set at_door flag.
        10. Collect gems.
        11. Clamp to screen boundaries (prevents walking off the sides).

        Parameters
        ----------
        platforms : list[pygame.Rect]
            Solid tiles — the level geometry.
        pools : list[dict]
            {"rect": Rect, "type": str}  hazard areas.
        gems : list[dict]
            {"rect": Rect, "type": str, "collected": bool}
        doors : dict
            {"fire": Rect, "water": Rect}
        buttons : list[dict]
            {"rect": Rect, "pressed": bool, "gate_index": int}
        gates : list[dict]
            {"rect": Rect, "open": bool}
        """
        if not self.alive:
            return   # ── Step 1: skip everything if dead ─────────────────────

        keys = pygame.key.get_pressed()

        # ── Step 2: Horizontal input ──────────────────────────────────────────
        dx = 0
        if keys[self.left_key]:
            dx = -MOVE_SPEED
            self.facing_right = False
        if keys[self.right_key]:
            dx = MOVE_SPEED
            self.facing_right = True

        self.rect.x += dx
        self._resolve_x(platforms)           # push out of platforms sideways

        # ── Step 3: Gravity ───────────────────────────────────────────────────
        self.vel_y += GRAVITY
        self.vel_y  = min(self.vel_y, MAX_FALL_SPEED)  # cap terminal velocity
        self.rect.y += int(self.vel_y)

        # ── Step 4: Vertical collision with platforms ─────────────────────────
        self.on_ground = False               # reset each frame; set by resolver
        self._resolve_y(platforms)

        # ── Step 5: Jump input ────────────────────────────────────────────────
        #   We check jump AFTER resolving vertical collisions so on_ground is
        #   accurate for this frame.  Without this order the player can jump
        #   in mid-air because on_ground hasn't been set yet.
        if keys[self.jump_key] and self.on_ground:
            self.vel_y = JUMP_FORCE

        # ── Step 6: Gate collision (closed gates are solid) ───────────────────
        solid_gates = [g["rect"] for g in gates if not g["open"]]
        self.rect.x -= dx                    # temporarily undo horizontal move
        self.rect.x += dx
        self._resolve_x(solid_gates)
        self._resolve_y(solid_gates)

        # ── Step 7: Hazard pools ──────────────────────────────────────────────
        self._check_pools(pools)

        # ── Step 8: Pressure buttons ──────────────────────────────────────────
        self._check_buttons(buttons, gates)

        # ── Step 9: Door check ────────────────────────────────────────────────
        self._check_door(doors)

        # ── Step 10: Gem collection ───────────────────────────────────────────
        self._collect_gems(gems)

        # ── Step 11: Screen clamping (left/right edges only) ──────────────────
        #   The top and bottom are handled by the level's wall/floor platforms.
        self.rect.x = max(0, min(self.rect.x, SCREEN_W - PLAYER_W))

    def draw(self, surface):
        """
        Render the player onto *surface*.

        Visual elements:
          • Filled rounded rectangle for the body (in the character's color).
          • Dark outline for contrast against all backgrounds.
          • White sclera + dark iris "eye" — positioned based on facing direction.
          • Grey "feet" stripe at the bottom of the body for visual grounding.

        Dead players are not drawn (caller should show a particle effect instead).
        """
        if not self.alive:
            return

        r = self.rect

        # Body fill + outline ────────────────────────────────────────────────
        pygame.draw.rect(surface, self.color, r, border_radius=7)
        pygame.draw.rect(surface, BLACK,      r, 2, border_radius=7)

        # Feet stripe (bottom 8 px, slightly darker shade) ───────────────────
        feet = pygame.Rect(r.x + 2, r.bottom - 9, r.width - 4, 7)
        darker = tuple(max(0, c - 50) for c in self.color)
        pygame.draw.rect(surface, darker, feet, border_radius=3)

        # Eye (tracks facing direction) ────────────────────────────────────
        eye_x = (r.right - 10) if self.facing_right else (r.left + 10)
        eye_y = r.top + 12
        pygame.draw.circle(surface, WHITE,                  (eye_x, eye_y), 6)
        pupil_offset = 2 if self.facing_right else -2
        pygame.draw.circle(surface, BLACK, (eye_x + pupil_offset, eye_y), 3)

    def reset(self):
        """
        Restore the player to their spawn position with fresh state.
        Called when the level resets after a death (or when starting a new level).
        """
        self.rect.topleft = (self.spawn_x, self.spawn_y)
        self.vel_y        = 0.0
        self.on_ground    = False
        self.alive        = True
        self.at_door      = False
        self.gems         = 0
        self.facing_right = True

    def set_spawn(self, x, y):
        """Update the spawn position (called when loading a new level)."""
        self.spawn_x = x
        self.spawn_y = y

    # ═══════════════════════════════════════════════════════════════════════════
    # PRIVATE COLLISION HELPERS
    # ═══════════════════════════════════════════════════════════════════════════

    def _resolve_x(self, rects):
        """
        Push the player OUT of any rect they overlap on the horizontal axis.

        How it works:
          If the player's center is to the LEFT of the rect's center, then the
          player came from the left and should be pushed left (right edge = rect
          left edge).  Vice-versa for the other side.

        This is called separately from _resolve_y so each axis is handled
        independently, avoiding diagonal-corner sticking bugs.
        """
        for obj in rects:
            if self.rect.colliderect(obj):
                if self.rect.centerx < obj.centerx:
                    self.rect.right = obj.left    # player is on the left side
                else:
                    self.rect.left  = obj.right   # player is on the right side

    def _resolve_y(self, rects):
        """
        Snap the player to the top/bottom of any rect they overlap vertically.

        Landing (vel_y > 0):
          Snap rect.bottom to obj.top.  Set vel_y = 0 and on_ground = True.

        Bonking head (vel_y < 0):
          Snap rect.top to obj.bottom.  Set vel_y = 0 so gravity takes over
          immediately (no floating against the ceiling).
        """
        for obj in rects:
            if self.rect.colliderect(obj):
                if self.vel_y >= 0:
                    # Falling or stationary — land on top
                    self.rect.bottom = obj.top
                    self.vel_y       = 0
                    self.on_ground   = True
                else:
                    # Rising — bonk on underside
                    self.rect.top = obj.bottom
                    self.vel_y    = 0

    # ═══════════════════════════════════════════════════════════════════════════
    # PRIVATE INTERACTION HELPERS
    # ═══════════════════════════════════════════════════════════════════════════

    def _check_pools(self, pools):
        """
        Kill the player if they overlap a pool type that is lethal to them.

        Lethal combinations:
          Fireboy   dies in water  and poison.
          Watergirl dies in lava   and poison.

        We check the player rect against pool["rect"].  The pool must be in
        self.lethal_pools for it to trigger a kill.  Once alive = False the
        update() method will skip all further processing.
        """
        for pool in pools:
            if pool["type"] in self.lethal_pools:
                if self.rect.colliderect(pool["rect"]):
                    self.alive = False
                    return   # no need to check more pools once dead

    def _check_buttons(self, buttons, gates):
        """
        Detect pressure-button presses / releases and propagate to linked gates.

        A button becomes "pressed" when the player's BOTTOM edge overlaps the
        button rect (i.e. the player is standing on it, not just touching the
        side).  We use a slightly enlarged rect check on the bottom 4 px of the
        player to handle the imprecision of integer pixel math.

        Each button has a "gate_index" field that indexes into the gates list.
        When pressed  → gates[gate_index]["open"] = True.
        When released → the gate may or may not close (depends on level design;
                         here we close it on release — cooperative holding needed).
        """
        for btn in buttons:
            # Build a thin rect covering just the player's feet area
            feet_rect = pygame.Rect(
                self.rect.x,
                self.rect.bottom - 4,
                self.rect.width,
                8
            )
            if feet_rect.colliderect(btn["rect"]):
                btn["pressed"] = True
                # Open the linked gate
                idx = btn.get("gate_index", -1)
                if 0 <= idx < len(gates):
                    gates[idx]["open"] = True
            # Note: gate is closed again by Level.update() if NO player presses it.

    def _check_door(self, doors):
        """
        Set at_door = True while the player overlaps their designated exit door.

        The door key matches the character:
          Fireboy   → doors["fire"]
          Watergirl → doors["water"]

        Both players must have at_door = True simultaneously for the level to
        register as won.  (Checked by Game.update().)
        """
        door_rect = doors.get(self.door_key)
        if door_rect:
            self.at_door = self.rect.colliderect(door_rect)

    def _collect_gems(self, gems):
        """
        Collect any uncollected gem whose type matches this player's gem_type.

        Fireboy collects red gems.  Watergirl collects blue gems.
        Neither player can collect the other's gems — this is enforced by
        the gem_type comparison.

        Sets gem["collected"] = True so the rendering code skips it and
        it cannot be collected again.  Increments self.gems counter.
        """
        for gem in gems:
            if gem["collected"]:
                continue   # already taken
            if gem["type"] != self.gem_type:
                continue   # not for this player
            if self.rect.colliderect(gem["rect"]):
                gem["collected"] = True
                self.gems += 1