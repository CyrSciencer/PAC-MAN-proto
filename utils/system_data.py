from dataclasses import dataclass, field
import sys
import json
from .parser import json_parse
@dataclass
class Inputs:
    held: list[int] = field(default_factory=list)  # direction keys (game)
    pressed: list[int] = field(default_factory=list)  # new key presses
    typed: list[str] = field(default_factory=list)  # TEXTINPUT this frame
    dt: int = 0


@dataclass
class State:
    mode: str = "main menu"
    name: str = ""
    scores: dict[str, int] = field(default_factory=dict)
    current_score: int = 0
    m_width: int = 15
    m_height: int = 15


class SaveSystem:
    def __init__(self) -> None:
        self.scores = {}
        self.datas = {}
        self.file = ""

    def loading(self, state: State) -> bool:
        args = sys.argv[1:]
        if len(args) == 0:
            print("Usage: main.py <file.json>")
            return False
        try:
            self.file = args[0]
            with open(args[0], "r") as file:
                self.data = json_parse(file)
                self.scores = self.data["scores"]
                state.m_height, state.m_width = self.data["width-height"]
            return True
        except Exception as e:
            print(f"Error opening file '{args[0]}': {e}")
            return False

    def export(self, scores: dict[str, int]):
        self.data["scores"] = scores
        with open(self.file, "w") as file:
            file.write(json.dumps(self.data))