from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class OutputFile:
    path: str      # relative path from project root
    content: str
    executable: bool = False


class BuildTarget(ABC):
    name: str
    output_dir: str

    @abstractmethod
    def render(self, skills: list[dict], org: dict, templates_env: Any) -> list[OutputFile]:
        ...
