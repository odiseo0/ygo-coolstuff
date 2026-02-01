from dataclasses import dataclass


@dataclass(frozen=True)
class ModeState:
    mode: str
    breadcrumb: str
    hints: str
