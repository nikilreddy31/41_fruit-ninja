import pygame
import random
from pathlib import Path
from .fruit import Fruit


WHITE = (255, 255, 255)
BOMB_BLACK = (30, 30, 30)
FRUIT_COLORS = [
    (220, 60, 60),
    (230, 140, 40),
    (230, 200, 40),
    (90, 180, 90),
]


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.fruits = []
        self.trail = []
        self.last_mouse_pos = None

        # Difficulty settings
        self.difficulties = {
            "Easy": {
                "spawn_interval": 75,
                "bomb_chance": 0.08,
            },
            "Medium": {
                "spawn_interval": 55,
                "bomb_chance": 0.15,
            },
            "Hard": {
                "spawn_interval": 40,
                "bomb_chance": 0.25,
            },
        }

        self.difficulty = "Medium"
        self.spawn_interval = 55
        self._spawn_timer = 0
        self.bomb_chance = 0.15
        self.speed_scale = 1.0

        self.lives = 3
        self.score = 0

        self.font = pygame.font.SysFont("Arial", 28)
        self.game_over_font = pygame.font.SysFont("Arial", 64)
        self.menu_font = pygame.font.SysFont("Arial", 32)

        self.game_over = False
        self.exit_requested = False

        # -------------------------
        # Sound effects
        # -------------------------
        self.sounds = {
            "fruit_slice": self._load_sound("fruit_slice.wav"),
            "bomb": self._load_sound("bomb.wav"),
            "game_over": self._load_sound("game_over.wav"),
        }

    # =========================================================
    # SOUND FUNCTIONS
    # =========================================================

    def _load_sound(self, filename):
        sound_path = (
            Path(__file__).resolve().parent.parent
            / "assets"
            / "sounds"
            / filename
        )

        try:
            return pygame.mixer.Sound(str(sound_path))
        except (pygame.error, FileNotFoundError, OSError):
            print(f"Warning: Could not load sound: {sound_path}")
            return None

    def _play_sound(self, sound_name):
        sound = self.sounds.get(sound_name)

        if sound is not None:
            try:
                sound.play()
            except pygame.error:
                pass

    def _trigger_game_over(self):
        if self.game_over:
            return

        self.game_over = True
        self._play_sound("game_over")

    # =========================================================
    # GAME RESET / DIFFICULTY
    # =========================================================

    def start_new_game(self, difficulty):
        if difficulty not in self.difficulties:
            difficulty = "Medium"

        settings = self.difficulties[difficulty]

        self.difficulty = difficulty
        self.spawn_interval = settings["spawn_interval"]
        self.bomb_chance = settings["bomb_chance"]

        self.fruits = []
        self.trail = []
        self.last_mouse_pos = None

        self._spawn_timer = 0

        self.score = 0
        self.lives = 3
        self.speed_scale = 1.0

        self.game_over = False
        self.exit_requested = False

    # =========================================================
    # FRUIT SPAWNING
    # =========================================================

    def spawn_fruit(self):
        x = random.randint(60, self.width - 60)

        vy = -random.uniform(13, 16) * self.speed_scale
        vx = random.uniform(-2, 2)
        gravity = 0.35

        kind = (
            "bomb"
            if random.random() < self.bomb_chance
            else "fruit"
        )

        fruit = Fruit(
            x,
            self.height + 30,
            vx,
            vy,
            gravity,
            kind=kind,
        )

        fruit.color = (
            BOMB_BLACK
            if kind == "bomb"
            else random.choice(FRUIT_COLORS)
        )

        self.fruits.append(fruit)

    # =========================================================
    # EVENT HANDLING
    # =========================================================

    def handle_event(self, event):
        # Normal gameplay
        if not self.game_over:
            if event.type == pygame.MOUSEMOTION:
                self._handle_motion(event.pos)

            return

        # Game-over keyboard controls
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_1, pygame.K_e):
                self.start_new_game("Easy")

            elif event.key in (pygame.K_2, pygame.K_m):
                self.start_new_game("Medium")

            elif event.key in (pygame.K_3, pygame.K_h):
                self.start_new_game("Hard")

            elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                self.exit_requested = True

        # Game-over mouse controls
        elif event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos

            easy_button, medium_button, hard_button, exit_button = (
                self._get_menu_buttons()
            )

            if easy_button.collidepoint(pos):
                self.start_new_game("Easy")

            elif medium_button.collidepoint(pos):
                self.start_new_game("Medium")

            elif hard_button.collidepoint(pos):
                self.start_new_game("Hard")

            elif exit_button.collidepoint(pos):
                self.exit_requested = True

    # =========================================================
    # TASK 1 - IMPROVED SLICE DETECTION
    # =========================================================

    def _handle_motion(self, pos):
        if self.last_mouse_pos is None:
            self.last_mouse_pos = pos

            # Check the first mouse position
            x, y = pos

            for fruit in self.fruits:
                if not fruit.sliced and fruit.contains_point(x, y):
                    self._slice(fruit)

        else:
            # Check the entire movement segment instead of
            # checking only the final mouse position.
            for fruit in self.fruits:
                if not fruit.sliced:
                    if fruit.segment_intersects(
                        self.last_mouse_pos,
                        pos,
                    ):
                        self._slice(fruit)

        # Add position to blade trail
        self.trail.append(pos)

        if len(self.trail) > 15:
            self.trail.pop(0)

        self.last_mouse_pos = pos

    # =========================================================
    # SLICE FRUIT / BOMB
    # =========================================================

    def _slice(self, fruit):
        fruit.sliced = True

        if fruit.kind == "bomb":
            # Bomb sound
            self._play_sound("bomb")

            # Game-over sound
            self._trigger_game_over()

        else:
            # Fruit score
            self.score += 1

            # Fruit slicing sound
            self._play_sound("fruit_slice")

    # =========================================================
    # INPUT
    # =========================================================

    def handle_input(self):
        # Game is mouse-driven.
        pass

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self):
        if self.game_over:
            return

        self._spawn_timer += 1

        if self._spawn_timer >= self.spawn_interval:
            self._spawn_timer = 0
            self.spawn_fruit()

        still_alive = []

        for fruit in self.fruits:
            fruit.update()

            if fruit.sliced:
                continue

            if fruit.off_screen(self.height):
                if fruit.kind == "fruit":
                    self.lives -= 1

                continue

            still_alive.append(fruit)

        self.fruits = still_alive

        # No lives remaining
        if self.lives <= 0:
            self._trigger_game_over()

    # =========================================================
    # GAME-OVER MENU BUTTONS
    # =========================================================

    def _get_menu_buttons(self):
        button_width = 180
        button_height = 50
        gap = 15

        total_width = (
            button_width * 3
            + gap * 2
        )

        start_x = (self.width - total_width) // 2
        y = self.height // 2 + 60

        easy_button = pygame.Rect(
            start_x,
            y,
            button_width,
            button_height,
        )

        medium_button = pygame.Rect(
            start_x + button_width + gap,
            y,
            button_width,
            button_height,
        )

        hard_button = pygame.Rect(
            start_x + (button_width + gap) * 2,
            y,
            button_width,
            button_height,
        )

        exit_button = pygame.Rect(
            (self.width - 180) // 2,
            y + 75,
            180,
            button_height,
        )

        return (
            easy_button,
            medium_button,
            hard_button,
            exit_button,
        )

    # =========================================================
    # RENDER
    # =========================================================

    def render(self, screen):
        # Draw fruits
        for fruit in self.fruits:
            color = getattr(fruit, "color", WHITE)

            pygame.draw.circle(
                screen,
                color,
                (int(fruit.x), int(fruit.y)),
                fruit.radius,
            )

        # Draw blade trail
        if len(self.trail) >= 2:
            pygame.draw.lines(
                screen,
                WHITE,
                False,
                self.trail,
                3,
            )

        # Score
        score_text = self.font.render(
            f"Score: {self.score}",
            True,
            WHITE,
        )

        screen.blit(
            score_text,
            (10, 10),
        )

        # Lives
        lives_text = self.font.render(
            f"Lives: {self.lives}",
            True,
            WHITE,
        )

        screen.blit(
            lives_text,
            (self.width - 130, 10),
        )

        # Game-over screen
        if self.game_over:
            self._render_game_over(screen)

    # =========================================================
    # GAME-OVER SCREEN
    # =========================================================

    def _render_game_over(self, screen):
        # Dark transparent overlay
        overlay = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )

        overlay.fill((0, 0, 0, 180))
        screen.blit(overlay, (0, 0))

        # GAME OVER
        title = self.game_over_font.render(
            "GAME OVER",
            True,
            WHITE,
        )

        title_rect = title.get_rect(
            center=(self.width // 2, 100)
        )

        screen.blit(title, title_rect)

        # Final score
        score_text = self.menu_font.render(
            f"Final Score: {self.score}",
            True,
            WHITE,
        )

        score_rect = score_text.get_rect(
            center=(self.width // 2, 175)
        )

        screen.blit(score_text, score_rect)

        # Difficulty text
        difficulty_text = self.font.render(
            f"Difficulty: {self.difficulty}",
            True,
            WHITE,
        )

        difficulty_rect = difficulty_text.get_rect(
            center=(self.width // 2, 215)
        )

        screen.blit(
            difficulty_text,
            difficulty_rect,
        )

        # Buttons
        (
            easy_button,
            medium_button,
            hard_button,
            exit_button,
        ) = self._get_menu_buttons()

        pygame.draw.rect(
            screen,
            (70, 150, 70),
            easy_button,
            border_radius=8,
        )

        pygame.draw.rect(
            screen,
            (70, 100, 180),
            medium_button,
            border_radius=8,
        )

        pygame.draw.rect(
            screen,
            (180, 70, 70),
            hard_button,
            border_radius=8,
        )

        pygame.draw.rect(
            screen,
            (100, 100, 100),
            exit_button,
            border_radius=8,
        )

        # Button text
        easy_text = self.font.render(
            "Easy",
            True,
            WHITE,
        )

        medium_text = self.font.render(
            "Medium",
            True,
            WHITE,
        )

        hard_text = self.font.render(
            "Hard",
            True,
            WHITE,
        )

        exit_text = self.font.render(
            "Exit",
            True,
            WHITE,
        )

        screen.blit(
            easy_text,
            easy_text.get_rect(
                center=easy_button.center
            ),
        )

        screen.blit(
            medium_text,
            medium_text.get_rect(
                center=medium_button.center
            ),
        )

        screen.blit(
            hard_text,
            hard_text.get_rect(
                center=hard_button.center
            ),
        )

        screen.blit(
            exit_text,
            exit_text.get_rect(
                center=exit_button.center
            ),
        )

        # Keyboard instructions
        hint = self.font.render(
            "Press 1/E, 2/M, 3/H or click a button",
            True,
            WHITE,
        )

        hint_rect = hint.get_rect(
            center=(self.width // 2, self.height - 35)
        )

        screen.blit(hint, hint_rect)