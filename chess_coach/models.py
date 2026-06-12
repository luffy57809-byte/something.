from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MoveAnalysis:
    move_number: int
    color: str
    move_san: str
    fen_before: str
    fen_after: str
    eval_before: Optional[int] = None
    eval_after: Optional[int] = None
    best_move_san: Optional[str] = None
    eval_drop: Optional[int] = None
    classification: Optional[str] = None
    pattern_tags: list[str] = field(default_factory=list)
    explanation: Optional[str] = None


@dataclass
class GameRecord:
    game_id: str
    pgn: str
    white: str
    black: str
    result: str
    time_control: Optional[str] = None
    date: Optional[str] = None
    moves: list[MoveAnalysis] = field(default_factory=list)
