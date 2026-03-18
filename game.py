"""
game.py
=======
The top-level Game class that owns everything and runs the main loop.

FINITE STATE MACHINE (FSM)
──────────────────────────
The game flow is modelled as a simple FSM with five states:

    ┌─────────┐   any key    ┌─────────┐   both at door  ┌──────────┐
    │  MENU   │ ──────────▶  │ PLAYING │ ──────────────▶  │  WIN     │
    └─────────┘              └─────────┘                  └──────────┘
                                  │                            │ any key
                             death │                           ▼
                                  ▼                       next level or MENU
                             ┌──────────┐
                             │   DEAD   │
                             └──────────┘
                                  │ 2 s timer
                                  ▼
                              PLAYING (reset)

    QUIT  is handled at any state (closes the window).

PARTICLE SYSTEM
───────────────
A lightweight particle system adds visual feedback for deaths and door entries.
Particles are plain dicts with position, velocity, color, and a lifespan
counter.  They're updated and drawn each frame then removed when they expire.

HUD (Heads-Up Display)
──────────────────────
The HUD overlays on top of the game world:
  • Level name (top center)
  • Gem counts for both characters (top left / right)
  • Control reminders (bottom, shown on the menu screen)
"""

import pygame
import random
import math
import sys

from constants import *
from player   import Player
from level    import Level, LEVELS


class Game:
    """
    Owns the pygame window, all game objects, and the event / render loop.

    Usage
    ─────
        game = Game()
        game.run()        # blocks until the window is closed
    """

    # How long (in frames at 60 fps) to show the "DEAD — respawning" screen
    DEAD_TIMER_FRAMES = 120   # 2 seconds

    def __init__(self):
        """
        Initialize pygame, create the window, fonts, clock, and starting state.
        """
        # ── Pygame setup ─────────────────────────────────────────────────────
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption(TITLE)
        self.clock  = pygame.time.Clock()

        # ── Fonts ─────────────────────────────────────────────────────────────
        pygame.font.init()
        self.font_lg  = pygame.font.SysFont("arial", 48, bold=True)
        self.font_md  = pygame.font.SysFont("arial", 28, bold=True)
        self.font_sm  = pygame.font.SysFont("arial", 18)

        # ── Create the two players ────────────────────────────────────────────
        # Players are created once and reused across levels.  set_spawn() and
        # reset() update their position and state for each new level.
        self.fireboy = Player(
            spawn_x     = 55,
            spawn_y     = 460,
            color       = FIREBOY_COLOR,
            lethal_pools= ["water", "poison"],
            left_key    = pygame.K_LEFT,
            right_key   = pygame.K_RIGHT,
            jump_key    = pygame.K_UP,
            gem_type    = "red",
            door_key    = "fire",
            label       = "Fireboy",
        )
        self.watergirl = Player(
            spawn_x     = 120,
            spawn_y     = 460,
            color       = WATERGIRL_COLOR,
            lethal_pools= ["lava", "poison"],
            left_key    = pygame.K_a,
            right_key   = pygame.K_d,
            jump_key    = pygame.K_w,
            gem_type    = "blue",
            door_key    = "water",
            label       = "Watergirl",
        )

        # ── Level management ──────────────────────────────────────────────────
        self.level_index = 0                 # current level (index into LEVELS)
        self.level       = self._load_level(self.level_index)

        # ── FSM state ─────────────────────────────────────────────────────────
        # Valid values: "menu" | "playing" | "dead" | "win" | "game_complete"
        self.state      = "menu"
        self.dead_timer = 0    # counts down from DEAD_TIMER_FRAMES

        # ── Particle system ───────────────────────────────────────────────────
        # Each particle: {"x","y","vx","vy","color","life","max_life"}
        self.particles: list[dict] = []

        # ── Total gem score (persists across levels) ──────────────────────────
        self.total_gems_fire  = 0
        self.total_gems_water = 0

    # ═══════════════════════════════════════════════════════════════════════════
    # PUBLIC: MAIN LOOP
    # ═══════════════════════════════════════════════════════════════════════════

    def run(self):
        """
        Enter the main game loop.  Runs until the player closes the window.

        Each iteration:
          1. Handle OS / pygame events.
          2. Update game logic for the current FSM state.
          3. Render the current FSM state.
          4. Flip the display buffer.
          5. Tick the clock (caps at FPS).
        """
        running = True
        while running:
            # ── 1. Events ─────────────────────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    self._handle_keydown(event.key)

            # ── 2. Update ─────────────────────────────────────────────────────
            self._update()

            # ── 3. Render ─────────────────────────────────────────────────────
            self._draw()

            # ── 4. Display flip ───────────────────────────────────────────────
            pygame.display.flip()

            # ── 5. Clock tick ─────────────────────────────────────────────────
            self.clock.tick(FPS)

    # ═══════════════════════════════════════════════════════════════════════════
    # PRIVATE: EVENT HANDLING
    # ═══════════════════════════════════════════════════════════════════════════

    def _handle_keydown(self, key):
        """
        Dispatch key-press events based on the current FSM state.

        Parameters
        ----------
        key : int
            A pygame.K_* constant from the KEYDOWN event.
        """
        if self.state == "menu":
            # Any key starts the game from level 1
            self.state = "playing"

        elif self.state == "win":
            # Any key advances to the next level (or shows the end screen)
            self._advance_level()

        elif self.state == "game_complete":
            # Any key returns to the menu
            self._reset_game()

        elif self.state == "dead":
            # Skip the countdown — respawn immediately on any key
            self._respawn()

        # In "playing" state, key-down events aren't needed here because
        # continuous movement uses pygame.key.get_pressed() in Player.update().

    # ═══════════════════════════════════════════════════════════════════════════
    # PRIVATE: UPDATE LOGIC
    # ═══════════════════════════════════════════════════════════════════════════

    def _update(self):
        """Route per-frame update logic to the appropriate state handler."""
        if self.state == "playing":
            self._update_playing()
        elif self.state == "dead":
            self._update_dead()
        # menu / win / game_complete states are static — no per-frame logic

    def _update_playing(self):
        """
        Core gameplay update — called every frame while state == "playing".

        Order of operations:
          1. Level tick  (reset button/gate state before players interact)
          2. Player updates  (movement, collisions, interactions)
          3. Particle update
          4. Death check  → transition to "dead"
          5. Win check    → transition to "win"
        """
        players = [self.fireboy, self.watergirl]

        # ── 1. Level tick ─────────────────────────────────────────────────────
        self.level.update(players)

        # ── 2. Player updates ─────────────────────────────────────────────────
        for player in players:
            player.update(
                platforms = self.level.platforms,
                pools     = self.level.pools,
                gems      = self.level.gems,
                doors     = self.level.doors,
                buttons   = self.level.buttons,
                gates     = self.level.gates,
            )

        # ── 3. Particles ──────────────────────────────────────────────────────
        self._update_particles()

        # ── 4. Death check ────────────────────────────────────────────────────
        if not self.fireboy.alive or not self.watergirl.alive:
            # Emit death particles for the dead player(s)
            for p in players:
                if not p.alive:
                    self._emit_death_particles(p.rect.centerx, p.rect.centery, p.color)
            self.state      = "dead"
            self.dead_timer = self.DEAD_TIMER_FRAMES
            return

        # ── 5. Win check ──────────────────────────────────────────────────────
        if self.fireboy.at_door and self.watergirl.at_door:
            # Bank gem counts before transitioning
            self.total_gems_fire  += self.fireboy.gems
            self.total_gems_water += self.watergirl.gems
            # Emit celebration particles for both doors
            for door_rect in self.level.doors.values():
                for _ in range(40):
                    self._emit_confetti(door_rect.centerx, door_rect.centery)
            self.state = "win"

    def _update_dead(self):
        """
        Countdown timer while the death screen is shown.
        Auto-respawns when the timer reaches zero.
        """
        self.dead_timer -= 1
        self._update_particles()
        if self.dead_timer <= 0:
            self._respawn()

    # ═══════════════════════════════════════════════════════════════════════════
    # PRIVATE: DRAW LOGIC
    # ═══════════════════════════════════════════════════════════════════════════

    def _draw(self):
        """Route per-frame rendering to the appropriate state renderer."""
        # Background is always drawn first
        self.screen.fill(BG_COLOR)

        if self.state == "menu":
            self._draw_menu()
        elif self.state in ("playing", "dead"):
            self._draw_world()
            if self.state == "dead":
                self._draw_dead_overlay()
        elif self.state == "win":
            self._draw_world()
            self._draw_win_overlay()
        elif self.state == "game_complete":
            self._draw_complete_screen()

    def _draw_world(self):
        """
        Draw the full game world: level geometry, players, particles, HUD.
        Used by both "playing" and "dead" states.
        """
        self.level.draw(self.screen)
        self.fireboy.draw(self.screen)
        self.watergirl.draw(self.screen)
        self.level.draw_doors_active(self.screen, self.fireboy, self.watergirl)
        self._draw_particles()
        self._draw_hud()

    # ─────────────────────────────────────────────────────────────────────────
    # HUD
    # ─────────────────────────────────────────────────────────────────────────

    def _draw_hud(self):
        """
        Draw the Heads-Up Display overlay:
          • Level name — centered at the top
          • Fireboy gem count — top left  (red gem icon + number)
          • Watergirl gem count — top right (blue gem icon + number)
          • Controls reminder — bottom center (small, semi-transparent)
        """
        # Level name
        name_surf = self.font_sm.render(
            f"Level {self.level_index + 1}: {self.level.name}",
            True, HUD_TEXT_COL
        )
        self.screen.blit(name_surf, (SCREEN_W // 2 - name_surf.get_width() // 2, 6))

        # Fireboy gem count (top-left)
        self._draw_gem_count(20, 8, RED_GEM_COL, self.fireboy.gems, "Fireboy ↑←→")

        # Watergirl gem count (top-right)
        wg_text = f"Watergirl W A D"
        wg_surf = self.font_sm.render(
            f"{self.watergirl.gems} gems  {wg_text}", True, WATERGIRL_COLOR
        )
        self.screen.blit(wg_surf, (SCREEN_W - wg_surf.get_width() - 12, 8))
        # Draw blue gem dot
        pygame.draw.circle(self.screen, BLUE_GEM_COL,
                           (SCREEN_W - wg_surf.get_width() - 22, 16), GEM_R - 2)

    def _draw_gem_count(self, x, y, gem_color, count, controls):
        """Helper: draw a gem icon + count + controls hint at (x, y)."""
        pygame.draw.circle(self.screen, gem_color, (x + 6, y + 8), GEM_R - 2)
        text = self.font_sm.render(f"{count} gems   {controls}", True, FIREBOY_COLOR)
        self.screen.blit(text, (x + 18, y))

    # ─────────────────────────────────────────────────────────────────────────
    # OVERLAY SCREENS
    # ─────────────────────────────────────────────────────────────────────────

    def _draw_menu(self):
        """
        Title / menu screen drawn over the background.
        Shows the game title, character previews, and control instructions.
        """
        # Title
        title = self.font_lg.render("FIREBOY & WATERGIRL", True, WHITE)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 80))

        subtitle = self.font_md.render("The Crystal Temple", True, (180, 180, 180))
        self.screen.blit(subtitle, (SCREEN_W // 2 - subtitle.get_width() // 2, 145))

        # Character color blocks + labels
        pygame.draw.rect(self.screen, FIREBOY_COLOR,   (260, 220, 60, 90), border_radius=8)
        pygame.draw.rect(self.screen, WATERGIRL_COLOR, (580, 220, 60, 90), border_radius=8)
        fb_lbl = self.font_sm.render("FIREBOY",   True, FIREBOY_COLOR)
        wg_lbl = self.font_sm.render("WATERGIRL", True, WATERGIRL_COLOR)
        self.screen.blit(fb_lbl, (255, 320))
        self.screen.blit(wg_lbl, (570, 320))

        # Controls
        controls = [
            ("Fireboy",   "Arrow Keys to move, ↑ to jump", FIREBOY_COLOR),
            ("Watergirl", "A / D to move,  W to jump",     WATERGIRL_COLOR),
            ("Goal",      "Both reach their coloured doors to win!", WHITE),
            ("Warning",   "Fireboy dies in water/poison.  Watergirl dies in lava/poison.", (200,200,200)),
        ]
        for i, (who, desc, col) in enumerate(controls):
            line = self.font_sm.render(f"{who}: {desc}", True, col)
            self.screen.blit(line, (SCREEN_W // 2 - line.get_width() // 2, 380 + i * 28))

        # Prompt
        prompt = self.font_md.render("Press any key to start", True, WIN_COL)
        # Pulse opacity using a sine wave
        alpha = int(180 + 75 * math.sin(pygame.time.get_ticks() / 400))
        prompt.set_alpha(alpha)
        self.screen.blit(prompt, (SCREEN_W // 2 - prompt.get_width() // 2, 520))

    def _draw_dead_overlay(self):
        """
        Semi-transparent red overlay shown after a death.
        Displays which player died and a countdown to respawn.
        """
        # Dark tinted overlay
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((180, 20, 20, 140))
        self.screen.blit(overlay, (0, 0))

        # Who died
        dead_who = []
        if not self.fireboy.alive:
            dead_who.append(("Fireboy died!", FIREBOY_COLOR))
        if not self.watergirl.alive:
            dead_who.append(("Watergirl died!", WATERGIRL_COLOR))

        for i, (msg, col) in enumerate(dead_who):
            surf = self.font_lg.render(msg, True, col)
            self.screen.blit(surf, (SCREEN_W // 2 - surf.get_width() // 2,
                                     180 + i * 70))

        # Countdown
        secs_left = math.ceil(self.dead_timer / FPS)
        cnt = self.font_md.render(f"Respawning in {secs_left}...  (press any key)", True, WHITE)
        self.screen.blit(cnt, (SCREEN_W // 2 - cnt.get_width() // 2, 340))

    def _draw_win_overlay(self):
        """
        Golden victory overlay shown when both players reach their doors.
        Shows per-level gem tallies and a prompt to continue.
        """
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 130))
        self.screen.blit(overlay, (0, 0))

        # Victory text
        win_surf = self.font_lg.render("LEVEL COMPLETE!", True, WIN_COL)
        self.screen.blit(win_surf, (SCREEN_W // 2 - win_surf.get_width() // 2, 160))

        # Gem summary
        fb_gems = self.font_md.render(
            f"Fireboy gems:   {self.fireboy.gems}", True, FIREBOY_COLOR)
        wg_gems = self.font_md.render(
            f"Watergirl gems: {self.watergirl.gems}", True, WATERGIRL_COLOR)
        self.screen.blit(fb_gems, (SCREEN_W // 2 - fb_gems.get_width() // 2, 270))
        self.screen.blit(wg_gems, (SCREEN_W // 2 - wg_gems.get_width() // 2, 315))

        # Next-level prompt
        is_last = (self.level_index >= len(LEVELS) - 1)
        prompt_text = "Press any key to see your final score!" if is_last else "Press any key for the next level"
        prompt = self.font_sm.render(prompt_text, True, WHITE)
        self.screen.blit(prompt, (SCREEN_W // 2 - prompt.get_width() // 2, 400))

        self._draw_particles()

    def _draw_complete_screen(self):
        """
        Final screen shown after completing all levels.
        Summarises total gems collected by both characters.
        """
        title = self.font_lg.render("YOU WIN!", True, WIN_COL)
        self.screen.blit(title, (SCREEN_W // 2 - title.get_width() // 2, 120))

        sub = self.font_md.render("All levels completed!", True, WHITE)
        self.screen.blit(sub, (SCREEN_W // 2 - sub.get_width() // 2, 200))

        fb_total = self.font_md.render(
            f"Fireboy total gems:   {self.total_gems_fire}", True, FIREBOY_COLOR)
        wg_total = self.font_md.render(
            f"Watergirl total gems: {self.total_gems_water}", True, WATERGIRL_COLOR)
        total = self.font_md.render(
            f"Combined score: {self.total_gems_fire + self.total_gems_water}",
            True, WIN_COL)

        self.screen.blit(fb_total, (SCREEN_W // 2 - fb_total.get_width() // 2, 280))
        self.screen.blit(wg_total, (SCREEN_W // 2 - wg_total.get_width() // 2, 325))
        self.screen.blit(total,    (SCREEN_W // 2 - total.get_width()   // 2, 385))

        restart = self.font_sm.render("Press any key to return to the main menu", True, (180, 180, 180))
        self.screen.blit(restart, (SCREEN_W // 2 - restart.get_width() // 2, 480))

    # ═══════════════════════════════════════════════════════════════════════════
    # PRIVATE: PARTICLE SYSTEM
    # ═══════════════════════════════════════════════════════════════════════════

    def _emit_death_particles(self, cx, cy, color):
        """
        Spawn a burst of particles at the given position when a player dies.

        Particles fly outward in random directions, fade over their lifespan,
        and are automatically removed when life reaches 0.

        Parameters
        ----------
        cx, cy : int  — center of the burst
        color  : tuple — starting color of the particles
        """
        for _ in range(30):
            angle  = random.uniform(0, 2 * math.pi)
            speed  = random.uniform(2, 7)
            life   = random.randint(25, 50)
            self.particles.append({
                "x":        float(cx),
                "y":        float(cy),
                "vx":       math.cos(angle) * speed,
                "vy":       math.sin(angle) * speed - 2,   # slight upward bias
                "color":    color,
                "life":     life,
                "max_life": life,
            })

    def _emit_confetti(self, cx, cy):
        """
        Spawn a single confetti particle in a random bright color.
        Used for the win celebration burst.
        """
        colors = [WIN_COL, FIREBOY_COLOR, WATERGIRL_COLOR, WHITE,
                  RED_GEM_COL, BLUE_GEM_COL]
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(3, 9)
        life  = random.randint(40, 80)
        self.particles.append({
            "x":        float(cx),
            "y":        float(cy),
            "vx":       math.cos(angle) * speed,
            "vy":       math.sin(angle) * speed - 4,
            "color":    random.choice(colors),
            "life":     life,
            "max_life": life,
        })

    def _update_particles(self):
        """
        Advance all particles by one frame.

        Each particle:
          • moves by (vx, vy)
          • has gravity applied to vy
          • loses 1 life

        Expired particles (life ≤ 0) are removed from the list.
        """
        gravity = 0.3
        keep    = []
        for p in self.particles:
            p["x"]   += p["vx"]
            p["y"]   += p["vy"]
            p["vy"]  += gravity
            p["life"] -= 1
            if p["life"] > 0:
                keep.append(p)
        self.particles = keep

    def _draw_particles(self):
        """
        Render all particles as small circles whose alpha fades with their life.

        We approximate fading by computing a radius that shrinks as the particle
        ages (max_radius → 0 over the particle's lifespan).
        """
        for p in self.particles:
            life_frac = p["life"] / p["max_life"]   # 1.0 → 0.0 over lifetime
            radius    = max(1, int(5 * life_frac))
            x, y      = int(p["x"]), int(p["y"])
            # Skip particles that have left the screen
            if 0 <= x <= SCREEN_W and 0 <= y <= SCREEN_H:
                pygame.draw.circle(self.screen, p["color"], (x, y), radius)

    # ═══════════════════════════════════════════════════════════════════════════
    # PRIVATE: LEVEL MANAGEMENT
    # ═══════════════════════════════════════════════════════════════════════════

    def _load_level(self, index: int) -> Level:
        """
        Construct a Level object from LEVELS[index] and configure player spawns.

        Parameters
        ----------
        index : int  — index into the LEVELS list

        Returns
        -------
        Level  — ready-to-use level instance
        """
        data  = LEVELS[index]
        level = Level(data)

        # Update player spawns from level data
        sx, sy = data["spawn_fire"]
        self.fireboy.set_spawn(sx, sy)

        wx, wy = data["spawn_water"]
        self.watergirl.set_spawn(wx, wy)

        # Reset both players to their new spawn positions
        self.fireboy.reset()
        self.watergirl.reset()

        return level

    def _advance_level(self):
        """
        Move to the next level, or go to the game-complete screen if done.
        Called when the player presses a key on the win overlay.
        """
        self.level_index += 1
        if self.level_index >= len(LEVELS):
            # All levels done
            self.state = "game_complete"
        else:
            self.level = self._load_level(self.level_index)
            self.particles.clear()
            self.state = "playing"

    def _respawn(self):
        """
        Reset both players and the level to their starting state.
        Called after the dead timer expires (or player skips it with a key press).
        """
        # Gem counts reset on death (no banking — must redo the level cleanly)
        self.fireboy.reset()
        self.watergirl.reset()

        # Reload level so gems, buttons, gates return to their initial state
        self.level = self._load_level(self.level_index)

        self.particles.clear()
        self.state = "playing"

    def _reset_game(self):
        """
        Full game reset: return to level 1, clear all scores, go to menu.
        Called from the game-complete screen.
        """
        self.level_index      = 0
        self.total_gems_fire  = 0
        self.total_gems_water = 0
        self.level            = self._load_level(0)
        self.particles.clear()
        self.state            = "menu"