from typing import Optional, cast

import pygame

M_WIDTH: int = 15
M_HEIGHT: int = 15
MARGIN: int = 15
FPS: int = 12
SPRITE_DIM: int = 31
ANIM_STEP_MS: int = 100  # time per animation frame
BOTTOM_BAR: int = 70  # extra space under the maze (for score, etc.)
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


class Maze:
    def __init__(self) -> None:
        # 15 = all four walls set (bitmask); unused until walls are drawn
        self.grid: list[list[int]] = [[15] * M_WIDTH for _ in range(M_HEIGHT)]

    @staticmethod
    def in_bounds(cell: pygame.Vector2) -> bool:
        return 0 <= cell.x < M_WIDTH and 0 <= cell.y < M_HEIGHT

    @staticmethod
    def build_maze_surface(cell_size: int) -> pygame.Surface:
        width = 2 * MARGIN + cell_size * M_WIDTH
        height = 2 * MARGIN + cell_size * M_HEIGHT
        surface = pygame.Surface((width, height))
        surface.fill((20, 20, 35))
        for row in range(M_HEIGHT):
            for col in range(M_WIDTH):
                rect = pygame.Rect(
                    MARGIN + col * cell_size,
                    MARGIN + row * cell_size,
                    cell_size,
                    cell_size,
                )
                pygame.draw.rect(surface, "blue", rect, 1)
        pygame.draw.rect(
            surface,
            "blue",
            pygame.Rect(
                MARGIN - 3,
                MARGIN - 3,
                cell_size * M_WIDTH + 6,
                cell_size * M_HEIGHT + 6,
            ),
            3,
        )
        return surface


class Entity:
    def __init__(self, cell_size: int) -> None:
        self.grid_position: pygame.Vector2 = pygame.Vector2(2, 2)
        self.cell_size: int = cell_size
        self.frames: list[pygame.Surface] = []
        self.active_anim: Optional[list[pygame.Surface]] = []
        self.alive: bool = True
        self.anim_name: Optional[str] = None

    @property
    def pixel_position(self) -> pygame.Vector2:
        return pygame.Vector2(
            MARGIN + (self.grid_position.x + 0.5) * self.cell_size,
            MARGIN + (self.grid_position.y + 0.5) * self.cell_size,
        )

    def current_frame(self, ticks: int) -> Optional[pygame.Surface]:
        if self.active_anim != None:
            index = (ticks // ANIM_STEP_MS) % len(self.active_anim)
            return self.active_anim[index]
        return None


class Ghost(Entity):
    def __init__(self, cell_size: int) -> None:
        super().__init__(cell_size)
        self.vulnerable: bool = False

    def set_animation(
        self, name: Optional[str], id: int, player_state: bool
    ) -> None:
        if player_state is False:
            self.active_anim = None
            return
        if name == self.anim_name and self.active_anim:
            return
        self.anim_name = name
        indices = GHOST_ANIMATIONS.get(name, IDLE)
        self.active_anim = [self.frames[i] for i in indices]

    def update(self, id: int, maze: Maze, player_state: bool) -> None:
        name = "right"
        self.set_animation(name, id, player_state)
        return


class Player(Entity):
    def set_animation(self, name: Optional[str]) -> None:
        if name == self.anim_name and self.active_anim:
            return
        self.anim_name = name
        indices = PLAYER_ANIMATIONS.get(name, IDLE)
        self.active_anim = [self.frames[i] for i in indices]

    def update(self, maze: Maze, held: list[int]) -> None:
        if 32 in held:
            held.remove(32)
        if self.alive is False:
            self.set_animation("dead")
            return
        name = KEY_TO_DIR[held[-1]] if held else None
        self.set_animation(name)
        if name is None:
            return
        target = self.grid_position + VECTORS[name]
        if maze.in_bounds(target):
            self.grid_position = target


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
        self.hover: bool = hover

    def draw(self, window: pygame.Surface) -> None:
        bg = (90, 90, 200) if self.hover else (40, 40, 120)
        pygame.draw.rect(window, bg, self.rect, border_radius=10)
        label = self.font.render(self.text, True, (255, 227, 0))
        window.blit(label, label.get_rect(center=self.rect.center))


def get_img(
    sheet: pygame.Surface, row: int, col: int, size: int, out_size: int
) -> pygame.Surface:
    image = pygame.Surface((size, size), pygame.SRCALPHA)
    image.blit(sheet, (0, 0), pygame.Rect(col * size, row * size, size, size))
    return pygame.transform.scale(image, (out_size // 1.3, out_size // 1.3))


def handle_events(held: list[int], gamemode: str) -> bool:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False
            if event.key in KEY_TO_DIR and event.key not in held:
                held.append(event.key)
            if event.key == pygame.K_SPACE:
                held.append(event.key)
        elif event.type == pygame.KEYUP and event.key in held:
            held.remove(event.key)
    return True


def draw_game(
    window: pygame.Surface,
    background: pygame.Surface,
    player: Player,
    ghosts: tuple[Ghost, ...],
) -> None:
    window.fill("black")
    window.blit(background, (0, 0))
    # the player's animation is never None, so the frame is always a Surface
    player_sprite = cast(
        pygame.Surface, player.current_frame(pygame.time.get_ticks())
    )
    window.blit(
        player_sprite, player_sprite.get_rect(center=player.pixel_position)
    )
    for ghost in ghosts:
        ghost_sprite = ghost.current_frame(pygame.time.get_ticks())
        if ghost_sprite != None:
            window.blit(
                ghost_sprite,
                ghost_sprite.get_rect(center=ghost.pixel_position),
            )


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
    ghost_1 = Ghost(cell_size)
    ghost_2 = Ghost(cell_size)
    ghost_3 = Ghost(cell_size)
    ghost_4 = Ghost(cell_size)

    return (
        load_ghost(ghost_1, cell_size, sheet, 0, pygame.Vector2(0, 0)),
        load_ghost(ghost_2, cell_size, sheet, 1, pygame.Vector2(m_w - 1, 0)),
        load_ghost(ghost_3, cell_size, sheet, 2, pygame.Vector2(0, m_h - 1)),
        load_ghost(
            ghost_4, cell_size, sheet, 3, pygame.Vector2(m_w - 1, m_h - 1)
        ),
    )


def game_loop(
    player: Player,
    maze: Maze,
    held: list[int],
    ghosts: tuple[Ghost, ...],
    window: pygame.Surface,
    background: pygame.Surface,
) -> None:
    player.update(maze, held)
    id = 0
    for ghost in ghosts:
        ghost.update(id, maze, player.alive)
        id += 1
        if (
            ghost.vulnerable is False
            and ghost.grid_position == player.grid_position
        ):
            player.alive = False
    draw_game(window, background, player, ghosts)


def main_menu(
    window: pygame.Surface,
    held: list[int],
    win_w: int,
    font: pygame.font.Font,
    buttons: list[Button],
) -> str:
    window.fill((0, 0, 0))
    title = font.render("PAC MAN", True, (255, 227, 0))
    window.blit(title, title.get_rect(center=(win_w // 2, 150)))

    next_mode = "main menu"
    if held:
        key = held[-1]
        if key == pygame.K_UP:
            buttons[0].hover, buttons[1].hover = True, False
        elif key == pygame.K_DOWN:
            buttons[0].hover, buttons[1].hover = False, True
        elif key == pygame.K_SPACE:
            next_mode = "game" if buttons[0].hover else "set name"

    for button in buttons:
        button.draw(window)
    return next_mode


def compute_cell_size(screen_w: int, screen_h: int) -> int:
    size = max(4, min(screen_h // M_HEIGHT, screen_w // M_WIDTH)) // 2
    return max(size, 10)


def main() -> None:
    pygame.init()
    pygame.display.set_caption("PAC-MAN")
    info = pygame.display.Info()
    cell_size = compute_cell_size(info.current_w, info.current_h)
    if (
        cell_size * M_WIDTH >= info.current_w
        or cell_size * M_HEIGHT >= info.current_h
    ):
        print("change Maze size")
        return

    window = pygame.display.set_mode(
        (
            2 * MARGIN + cell_size * M_WIDTH,
            2 * MARGIN + cell_size * M_HEIGHT + BOTTOM_BAR,
        )
    )
    clock = pygame.time.Clock()
    sheet = pygame.image.load("pac_sheet.png").convert_alpha()
    maze = Maze()
    player = load_player(cell_size, sheet)
    ghosts = load_ghosts(cell_size, sheet, M_WIDTH, M_HEIGHT)
    background = maze.build_maze_surface(cell_size)
    held: list[int] = []
    gamemode = "main menu"
    player_name = ""
    title_font = pygame.font.SysFont(None, 100)
    buttons = [
        Button(
            "Play", (window.get_width() // 2, 300), (250, 70), title_font, True
        ),
        Button(
            "Set Name",
            (window.get_width() // 2, 400),
            (400, 70),
            title_font,
            False,
        ),
    ]
    running = True
    while running:
        running = handle_events(held, gamemode)
        match gamemode:
            case "main menu":
                gamemode = main_menu(
                    window, held, window.get_width(), title_font, buttons
                )
            case "game":
                game_loop(player, maze, held, ghosts, window, background)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
