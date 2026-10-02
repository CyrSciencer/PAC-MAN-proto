from main import (
    MARGIN,
    ANIM_STEP_MS,
    GHOST_ANIMATIONS,
    PLAYER_ANIMATIONS,
    IDLE,
    KEY_TO_DIR,
    VECTORS,
)
from system_data import State
from typing import Optional
import pygame
import copy


class Maze:
    def __init__(self, state: State) -> None:
        # 15 = all four walls set (bitmask); unused until walls are drawn
        self.grid: list[list[int]] = [
            [15] * state.m_width for _ in range(state.m_height)
        ]

    @staticmethod
    def in_bounds(cell: pygame.Vector2, state: State) -> bool:
        return 0 <= cell.x < state.m_width and 0 <= cell.y < state.m_height

    @staticmethod
    def build_maze_surface(cell_size: int, state: State) -> pygame.Surface:
        width = 2 * MARGIN + cell_size * state.m_width
        height = 2 * MARGIN + cell_size * state.m_height
        surface = pygame.Surface((width, height))
        surface.fill((20, 20, 35))
        for row in range(state.m_height):
            for col in range(state.m_width):
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
                cell_size * state.m_width + 6,
                cell_size * state.m_height + 6,
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
        if self.active_anim is not None:
            index = (ticks // ANIM_STEP_MS) % len(self.active_anim)
            return self.active_anim[index]
        return None

    def clone(self):
        other = copy.copy(self)
        other.grid_position = self.grid_position.copy()
        return other


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


class Player(Entity):
    def __init__(self, cell_size: int) -> None:
        super().__init__(cell_size)
        self.name: str = ""

    def set_animation(self, name: Optional[str]) -> None:
        if name == self.anim_name and self.active_anim:
            return
        self.anim_name = name
        indices = PLAYER_ANIMATIONS.get(name, IDLE)
        self.active_anim = [self.frames[i] for i in indices]

    def update(self, maze: Maze, held: list[int], state: State) -> None:
        if self.alive is False:
            self.set_animation("dead")
            return
        name = KEY_TO_DIR[held[-1]] if held else None
        self.set_animation(name)
        if name is None:
            return
        target = self.grid_position + VECTORS[name]
        if maze.in_bounds(target, state):
            self.grid_position = target
