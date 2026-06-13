import chess
import json


def detect_hanging_piece(fen_after: str, mover_color: str) -> bool:
    """Check if the player who just moved left a piece hanging."""
    board = chess.Board(fen_after)
    mover_is_white = (mover_color == "white")
    opponent_color = chess.BLACK if mover_is_white else chess.WHITE

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None:
            continue
        if piece.color != mover_is_white:
            continue

        attackers = board.attackers(opponent_color, square)
        if not attackers:
            continue

        defenders = board.attackers(mover_is_white, square)

        if not defenders:
            return True

        if len(attackers) > len(defenders):
            return True

    return False


def detect_missed_fork(fen_before: str, best_move_san: str, mover_color: str) -> bool:
    """Check if the engine's best move creates a fork."""
    if not best_move_san:
        return False

    board = chess.Board(fen_before)
    try:
        move = board.parse_san(best_move_san)
    except ValueError:
        return False

    board.push(move)
    moved_piece_square = move.to_square
    opponent_color = not board.turn

    attacked_pieces = 0
    for square in board.attacks(moved_piece_square):
        target = board.piece_at(square)
        if target and target.color == opponent_color:
            if target.piece_type != chess.PAWN:
                attacked_pieces += 1

    return attacked_pieces >= 2


def detect_missed_pin(fen_before: str, best_move_san: str, mover_color: str) -> bool:
    """
    Check if the engine's best move creates a pin —
    a piece attacked that cannot move without exposing a more valuable piece.
    """
    if not best_move_san:
        return False

    board = chess.Board(fen_before)
    try:
        move = board.parse_san(best_move_san)
    except ValueError:
        return False

    board.push(move)
    opponent_color = board.turn  # now it's opponent's turn

    # Check if any opponent piece is now pinned
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None or piece.color != opponent_color:
            continue
        if board.is_pinned(opponent_color, square):
            return True

    return False


def detect_back_rank_weakness(fen_after: str, mover_color: str) -> bool:
    """
    Check if the player who just moved has a back rank weakness —
    king trapped on back rank with no escape squares.
    """
    board = chess.Board(fen_after)
    mover_is_white = (mover_color == "white")

    king_square = board.king(mover_is_white)
    if king_square is None:
        return False

    back_rank = chess.BB_RANK_1 if mover_is_white else chess.BB_RANK_8
    if not (chess.BB_SQUARES[king_square] & back_rank):
        return False  # king not on back rank

    # Check if king has friendly pawns blocking all escape squares
    king_rank = chess.square_rank(king_square)
    king_file = chess.square_file(king_square)

    escape_squares = 0
    for f in range(max(0, king_file - 1), min(8, king_file + 2)):
        forward_rank = king_rank + (1 if mover_is_white else -1)
        if 0 <= forward_rank <= 7:
            sq = chess.square(f, forward_rank)
            piece = board.piece_at(sq)
            if piece and piece.color == mover_is_white and piece.piece_type == chess.PAWN:
                escape_squares += 1

    # If all three forward squares blocked by own pawns, back rank is weak
    return escape_squares >= 2


def tag_patterns(move_analysis, fen_before: str) -> list[str]:
    """Run all pattern detectors and return a list of tags."""
    tags = []

    if move_analysis.classification in ("blunder", "mistake"):
        if detect_hanging_piece(move_analysis.fen_after, move_analysis.color):
            tags.append("hanging_piece")

        if detect_missed_fork(fen_before, move_analysis.best_move_san, move_analysis.color):
            tags.append("missed_fork")

        if detect_missed_pin(fen_before, move_analysis.best_move_san, move_analysis.color):
            tags.append("missed_pin")

        if detect_back_rank_weakness(move_analysis.fen_after, move_analysis.color):
            tags.append("back_rank_weakness")

    return tags
