from typing import Optional, cast
import pygame
from utils import Inputs, State, SaveSystem, Player, Ghost, Maze

MARGIN: int = 15
FPS: int = 12
SPRITE_DIM: int = 31
ANIM_STEP_MS: int = 100  # time per animation frame
BOTTOM_BAR: int = 70  # extra space under the maze (for score, etc.)
MAX_NAME_LEN: int = 10
YELLOW = (255, 227, 0)
KEY_TO_DIR: dict[int, str] = {
    pygame.K_w: "up",
    pygame.K_UP: "up",
    pygame.K_s: "down",
    pygame.K_DOWN: "down",
    pygame.K_a: "left",
    pygame.K_LEFT: "left",
    pygame.K_d: "right",
    pygame.K_RIGHT: "right",
}
VECTORS: dict[str, pygame.Vector2] = {
    "up": pygame.Vector2(0, -1),
    "down": pygame.Vector2(0, 1),
    "left": pygame.Vector2(-1, 0),
    "right": pygame.Vector2(1, 0),
}
PLAYER_FRAMES: list[tuple[int, int]] = [
    (8, 1),
    (8, 2),
    (8, 3),
    (8, 4),
    (8, 5),
    (9, 2),
    (9, 3),
    (9, 4),
    (9, 5),
    (8, 0),
    (9, 0),
    (9, 1),
]
GHOST_FRAMES: list[list[tuple[int, int]]] = [
    [(0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0), (7, 0)],
    [(0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1), (6, 1), (7, 1)],
    [(0, 2), (1, 2), (2, 2), (3, 2), (4, 2), (5, 2), (6, 2), (7, 2)],
    [(0, 3), (1, 3), (2, 3), (3, 3), (4, 3), (5, 3), (6, 3), (7, 3)],
    [
        (0, 4),  # 0 right1
        (0, 5),  # 1 right3
        (1, 4),  # 2 right2
        (1, 5),  # 3 right4
        (2, 4),  # 4 down1
        (2, 5),  # 5 down3
        (3, 4),  # 6 down2
        (3, 5),  # 7 down4
        (4, 4),  # 8 left1
        (4, 5),  # 9 left3
        (5, 4),  # 10 left2
        (5, 5),  # 11 left4
        (6, 4),  # 12 up1
        (6, 5),  # 13 up3
        (7, 4),  # 14 up2
        (7, 5),  # 15 up4
    ],
]
IDLE: tuple[int, ...] = (0, 0, 0, 0)
# Keys are Optional[str] because set_animation() can be called with None
PLAYER_ANIMATIONS: dict[Optional[str], tuple[int, ...]] = {
    "up": (0, 5, 6, 5),
    "down": (0, 3, 4, 3),
    "left": (0, 7, 8, 7),
    "right": (0, 1, 2, 1),
    "dead": (0, 9, 10, 11),
}
GHOST_ANIMATIONS: dict[Optional[str], tuple[int, ...]] = {
    "up": (6, 7),
    "down": (2, 3),
    "left": (4, 5),
    "right": (0, 1),
    "d_up": (12, 14, 13, 15),
    "d_down": (4, 6, 5, 7),
    "d_left": (8, 10, 9, 11),
    "d_right": (0, 2, 1, 3),
}


class Button:
    def __init__(
        self,
        text: str,
        center: tuple[int, int],
        size: tuple[int, int],
        font: pygame.font.Font,
        hover: bool,
    ) -> None:
        self.text: str = text
        self.font: pygame.font.Font = font
        self.rect: pygame.Rect = pygame.Rect((0, 0), size)
        self.rect.center = center

    def draw(self, window: pygame.Surface, offset: int = 0) -> None:
        rect = self.rect.move(
            0, offset
        )  # a shifted copy; self.rect is unchanged
        pygame.draw.rect(window, "black", rect)
        label = self.font.render(self.text, True, "white")
        window.blit(label, label.get_rect(center=rect.center))


# --------------------------------------------------------------------------
# Loading helpers
# --------------------------------------------------------------------------
def compute_cell_size(screen_w: int, screen_h: int, state: State) -> int:
    size = (
        max(4, min(screen_h // state.m_height, screen_w // state.m_width)) // 2
    )
    return max(size, 10)


def get_img(
    sheet: pygame.Surface, row: int, col: int, size: int, out_size: int
) -> pygame.Surface:
    image = pygame.Surface((size, size), pygame.SRCALPHA)
    image.blit(sheet, (0, 0), pygame.Rect(col * size, row * size, size, size))
    scaled = int(out_size / 1.3)
    return pygame.transform.scale(image, (scaled, scaled))


def load_player(cell_size: int, sheet: pygame.Surface) -> Player:
    player = Player(cell_size)
    player.frames = [
        get_img(sheet, row, col, SPRITE_DIM, cell_size)
        for row, col in PLAYER_FRAMES
    ]
    player.set_animation(None)
    return player


def load_ghost(
    ghost: Ghost,
    cell_size: int,
    sheet: pygame.Surface,
    id: int,
    start_pos: pygame.Vector2,
) -> Ghost:
    ghost.frames = [
        get_img(sheet, row, col, SPRITE_DIM, cell_size)
        for row, col in GHOST_FRAMES[id]
    ]
    ghost.grid_position = start_pos
    ghost.set_animation(None, id, True)
    return ghost


def load_ghosts(
    cell_size: int, sheet: pygame.Surface, m_w: int, m_h: int
) -> tuple[Ghost, Ghost, Ghost, Ghost]:
    return (
        load_ghost(
            Ghost(cell_size), cell_size, sheet, 0, pygame.Vector2(0, 0)
        ),
        load_ghost(
            Ghost(cell_size), cell_size, sheet, 1, pygame.Vector2(m_w - 1, 0)
        ),
        load_ghost(
            Ghost(cell_size), cell_size, sheet, 2, pygame.Vector2(0, m_h - 1)
        ),
        load_ghost(
            Ghost(cell_size),
            cell_size,
            sheet,
            3,
            pygame.Vector2(m_w - 1, m_h - 1),
        ),
    )


# --------------------------------------------------------------------------
# Input and shared state
# --------------------------------------------------------------------------


def handle_events(
    inp: Inputs, scores: dict[str, int], savefile: SaveSystem
) -> bool:
    """The only place that calls pygame.event.get()."""
    inp.pressed.clear()
    inp.typed.clear()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.TEXTINPUT:
            inp.typed.append(event.text)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                savefile.export(scores)
                return False
            inp.pressed.append(event.key)
            if event.key in KEY_TO_DIR and event.key not in inp.held:
                inp.held.append(event.key)
        elif event.type == pygame.KEYUP and event.key in inp.held:
            inp.held.remove(event.key)
    return True


# --------------------------------------------------------------------------
# Screens
# --------------------------------------------------------------------------
class Screen:
    def on_enter(self, state: State) -> None:
        """Called once when this screen becomes active."""

    def update(
        self,
        inp: Inputs,
        state: State,
    ) -> Optional[str]:
        pass

    def draw(self, window: pygame.Surface, state: State) -> None:
        """Draw this screen."""


class MenuScreen(Screen):
    def __init__(
        self,
        title: str,
        items: list[tuple[str, str]],  # (label, target mode)
        title_font: pygame.font.Font,
        button_font: pygame.font.Font,
        win_w: int,
        show_name: bool = False,
    ) -> None:
        self.title = title
        self.title_font = title_font
        self.button_font = button_font
        self.score_font = pygame.font.SysFont(None, 36)
        self.win_w = win_w
        self.show_name = show_name
        self.targets = [target for _, target in items]
        self.selected = 0
        self.buttons = [
            Button(
                label,
                (win_w // 2, 220 + i * 100),
                (700, 70),
                button_font,
                i == 0,
            )
            for i, (label, _) in enumerate(items)
        ]

    def on_enter(self, state: State) -> None:
        self.selected = 0

    def update(self, inp: Inputs, state: State) -> Optional[str]:
        for key in inp.pressed:
            if key == pygame.K_SPACE:
                return self.targets[self.selected]
        return None

    def draw(self, window: pygame.Surface, state: State) -> None:
        offset = 0
        window.fill((0, 0, 0))
        title = self.title_font.render(self.title, True, YELLOW)
        window.blit(title, title.get_rect(center=(self.win_w // 2, 100)))
        scoring = self.score_font.render("highscores:", True, "white")
        window.blit(scoring, scoring.get_rect(center=(self.win_w // 2, 300)))

        for button in self.buttons:
            button.draw(window)
        i = 1
        for name, score in sorted(
            state.scores.items(), key=lambda item: item[1], reverse=True
        ):
            if i == 11:
                break
            name = self.score_font.render(
                f"{i}. {name} - {score}", True, "white"
            )
            window.blit(
                name, name.get_rect(center=(self.win_w // 2, 350 + offset))
            )

            offset += 35
            i += 1


class TypingScreen(Screen):
    def __init__(self, font: pygame.font.Font, win_w: int, score: int) -> None:
        self.font = font
        self.win_w = win_w

    def on_enter(self, state: State) -> None:
        pygame.key.start_text_input()

    def update(self, inp: Inputs, state: State) -> Optional[str]:
        for ch in inp.typed:
            if len(state.name) < MAX_NAME_LEN and (
                ch.isalpha() or ch.isnumeric() or ch == " "
            ):
                state.name += ch
        for key in inp.pressed:
            if key == pygame.K_BACKSPACE:
                state.name = state.name[:-1]
            elif key == pygame.K_RETURN:
                pygame.key.stop_text_input()
                state.scores[state.name] = 0
                if state.current_score > state.scores[state.name]:
                    state.scores[state.name] = state.current_score
                return "main menu"
        if pygame.key.get_pressed()[pygame.K_BACKSPACE]:
            state.name = state.name[:-1]
        return None

    def draw(self, window: pygame.Surface, state: State) -> None:
        window.fill((0, 0, 0))
        text = self.font.render(f"{state.name}_", True, (255, 255, 255))
        validate = self.font.render(
            "press enter to validate", True, (255, 255, 255)
        )
        window.blit(text, text.get_rect(center=(self.win_w // 2, 300)))
        window.blit(validate, validate.get_rect(center=(self.win_w // 2, 400)))


class GameScreen(Screen):
    def __init__(
        self,
        player_template: Player,
        maze: Maze,
        ghosts_template: tuple[Ghost, ...],
        background: pygame.Surface,
    ) -> None:
        self.player_template = player_template
        self.ghosts_template = ghosts_template
        self.player = player_template.clone()
        self.ghosts = tuple(g.clone() for g in ghosts_template)
        self.maze = maze
        self.background = background
        self.last_step = 0
        self.elapsed_ms = 0
        self.time_death = 0

    def on_enter(self, state: State) -> None:
        self.player = self.player_template.clone()
        self.ghosts = tuple(g.clone() for g in self.ghosts_template)
        self.last_step = pygame.time.get_ticks()
        self.elapsed_ms = 0

    def update(self, inp: Inputs, state: State) -> Optional[str]:
        self.player.update(self.maze, inp.held, state)
        self.elapsed_ms += min(inp.dt, 100)
        if self.player.alive is True:
            self.time_death = self.elapsed_ms
        for id, ghost in enumerate(self.ghosts):
            ghost.update(id, self.maze, self.player.alive)
            if (
                ghost.vulnerable is False
                and ghost.grid_position == self.player.grid_position
            ):
                self.player.alive = False
        if self.elapsed_ms - self.time_death > 1000:
            return "typing"
        return None

    def draw(self, window: pygame.Surface, state: State) -> None:
        window.fill("black")
        window.blit(self.background, (0, 0))
        now = pygame.time.get_ticks()
        sprite = cast(pygame.Surface, self.player.current_frame(now))
        window.blit(sprite, sprite.get_rect(center=self.player.pixel_position))
        score = pygame.font.SysFont(None, 70).render(
            f"score: {state.current_score}",
            True,
            (255, 255, 255),
        )
        for ghost in self.ghosts:
            ghost_sprite = ghost.current_frame(now)
            if ghost_sprite is not None:
                window.blit(
                    ghost_sprite,
                    ghost_sprite.get_rect(center=ghost.pixel_position),
                )
                window.blit(
                    score,
                    ghost_sprite.get_rect(
                        center=(
                            window.get_width() // 32,
                            window.get_height() - BOTTOM_BAR // 1.7,
                        )
                    ),
                )


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> None:
    state = State()
    savefile = SaveSystem()
    if savefile.loading(state) is False:
        return
    state.scores = savefile.scores
    pygame.init()
    pygame.display.set_caption("PAC-MAN")
    info = pygame.display.Info()
    cell_size = compute_cell_size(info.current_w, info.current_h, state)
    if (
        cell_size * state.m_width >= info.current_w
        or cell_size * state.m_height >= info.current_h
    ):
        print("change Maze size")
        return

    window = pygame.display.set_mode(
        (
            2 * MARGIN + cell_size * state.m_width,
            2 * MARGIN + cell_size * state.m_height + BOTTOM_BAR,
        )
    )
    # text input is tied to the window, so stop it after set_mode
    pygame.key.stop_text_input()
    clock = pygame.time.Clock()
    sheet = pygame.image.load("pac_sheet.png").convert_alpha()
    maze = Maze(state)
    player_template = load_player(cell_size, sheet)
    ghosts_template = load_ghosts(
        cell_size, sheet, state.m_width, state.m_height
    )
    background = maze.build_maze_surface(cell_size, state)

    title_font = pygame.font.SysFont(None, 100)
    button_font = pygame.font.SysFont(None, 48)
    win_w = window.get_width()
    inp = Inputs()
    screens: dict[str, Screen] = {
        "main menu": MenuScreen(
            "PAC MAN",
            [("Push SPACE to play", "game")],
            title_font,
            button_font,
            win_w,
        ),
        "typing": TypingScreen(button_font, win_w, state.current_score),
        "game": GameScreen(player_template, maze, ghosts_template, background),
    }
    running = True
    while running:
        print(f"\r{ state.current_score}", end="", flush=True)
        running = handle_events(inp, state.scores, savefile)
        screen = screens[state.mode]
        next_mode = screen.update(inp, state)
        screen.draw(window, state)
        if next_mode and next_mode != state.mode:
            state.mode = next_mode
            inp.held.clear()
            screens[next_mode].on_enter(state)
        pygame.display.flip()
        inp.dt = clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
