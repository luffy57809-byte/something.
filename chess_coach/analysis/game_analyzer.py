import io
import chess
import chess.pgn

from chess_coach.models import GameRecord, MoveAnalysis
from chess_coach.analysis.engine import ChessEngine
from chess_coach.analysis.patterns import tag_patterns


def classify(eval_drop: int) -> str:
    """Classify a move based on how much the evaluation dropped (in cp)."""
    if eval_drop >= 300:
        return "blunder"
    elif eval_drop >= 100:
        return "mistake"
    elif eval_drop >= 50:
        return "inaccuracy"
    else:
        return "good"


def analyze_pgn(pgn_text: str, depth: int = 12) -> GameRecord:
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
    board = game.board()

    move_number = 1
    for node in game.mainline():
        move = node.move
        color = "white" if board.turn == chess.WHITE else "black"

        fen_before = board.fen()
        eval_before, best_move_san = engine.evaluate(board)

        move_san = board.san(move)
        board.push(move)

        fen_after = board.fen()
        # eval_after is from perspective of the side to move AFTER this move
        # we need it from the perspective of the player who JUST moved,
        # so we negate it
        eval_after_raw, _ = engine.evaluate(board)
        eval_after = -eval_after_raw

        eval_drop = max(0, eval_before - eval_after)

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
            classification=classify(eval_drop),
        )
        analysis.pattern_tags = tag_patterns(analysis, fen_before)
        record.moves.append(analysis)

        if color == "black":
            move_number += 1

    engine.close()
    return record
