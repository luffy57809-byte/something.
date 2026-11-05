import io
import math
import chess
import chess.pgn

from chess_coach.models import GameRecord, MoveAnalysis
from chess_coach.analysis.engine import ChessEngine
from chess_coach.analysis.patterns import tag_patterns

DEFAULT_DEPTH = 12

# Tunable: how many points of win chance (0-100) a move must lose to be flagged
INACCURACY_PTS = 6
MISTAKE_PTS = 12
BLUNDER_PTS = 20


def classify(eval_drop: int) -> str:
    """Old centipawn-based classifier, kept for compatibility."""
    if eval_drop >= 300:
        return "blunder"
    elif eval_drop >= 100:
        return "mistake"
    elif eval_drop >= 50:
        return "inaccuracy"
    return "good"


def win_pct(cp: int) -> float:
    """Win chance (0-100) for a centipawn score, using Lichess's published curve."""
    return 50 + 50 * (2 / (1 + math.exp(-0.00368208 * cp)) - 1)


def classify_by_win_chance(eval_before: int, eval_after: int) -> str:
    drop = win_pct(eval_before) - win_pct(eval_after)
    if drop >= BLUNDER_PTS:
        return "blunder"
    if drop >= MISTAKE_PTS:
        return "mistake"
    if drop >= INACCURACY_PTS:
        return "inaccuracy"
    return "good"


def analyze_pgn(pgn_text: str, depth: int = DEFAULT_DEPTH) -> GameRecord:
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    headers = game.headers

    record = GameRecord(
        game_id=headers.get("Link", "unknown"),
        pgn=pgn_text,
        white=headers.get("White", "?"),
        black=headers.get("Black", "?"),
        result=headers.get("Result", "?"),
        time_control=headers.get("TimeControl"),
        date=headers.get("Date"),
    )

    engine = ChessEngine(depth=depth)
    try:
        board = game.board()
        # Each position is evaluated exactly once and reused for the next move
        eval_here, best_here = engine.evaluate(board)

        move_number = 1
        for node in game.mainline():
            move = node.move
            color = "white" if board.turn == chess.WHITE else "black"

            fen_before = board.fen()
            only_move = board.legal_moves.count() == 1
            eval_before, best_move_san = eval_here, best_here

            move_san = board.san(move)
            board.push(move)
            fen_after = board.fen()

            eval_next, best_next = engine.evaluate(board)
            eval_after = -eval_next  # from the view of the player who just moved
            eval_here, best_here = eval_next, best_next

            if move_san == best_move_san or only_move:
                eval_drop = 0
                classification = "good"
            else:
                eval_drop = max(0, eval_before - eval_after)
                classification = classify_by_win_chance(eval_before, eval_after)

            analysis = MoveAnalysis(
                move_number=move_number,
                color=color,
                move_san=move_san,
                fen_before=fen_before,
                fen_after=fen_after,
                eval_before=eval_before,
                eval_after=eval_after,
                best_move_san=best_move_san,
                eval_drop=eval_drop,
                classification=classification,
            )
            analysis.pattern_tags = tag_patterns(analysis, fen_before)
            record.moves.append(analysis)

            if color == "black":
                move_number += 1
    finally:
        engine.close()

    return record
