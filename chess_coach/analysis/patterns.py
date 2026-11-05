import chess

PIECE_VALUES = {
    chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
    chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 100,
}


def _cheapest_attacker_value(board, color, square) -> int:
    return min(PIECE_VALUES[board.piece_type_at(s)] for s in board.attackers(color, square))


def detect_hanging_piece(fen_after: str, mover_color: str) -> bool:
    """True if the mover left a piece (not a pawn) that the opponent can win material from."""
    board = chess.Board(fen_after)
    color = (mover_color == "white")
    enemy = not color

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None or piece.color != color:
            continue
        if piece.piece_type in (chess.PAWN, chess.KING):
            continue
        if not board.attackers(enemy, square):
            continue
        if not board.attackers(color, square):
            return True  # attacked and undefended
        if _cheapest_attacker_value(board, enemy, square) < PIECE_VALUES[piece.piece_type]:
            return True  # attacked by a cheaper piece
    return False


def detect_missed_fork(fen_before: str, best_move_san: str, mover_color: str) -> bool:
    """True if the engine's best move forks two enemy targets and the forking piece is safe."""
    if not best_move_san:
        return False

    board = chess.Board(fen_before)
    try:
        move = board.parse_san(best_move_san)
    except ValueError:
        return False

    mover = board.turn
    enemy = not mover
    board.push(move)

    to_sq = move.to_square
    forker_value = PIECE_VALUES[board.piece_type_at(to_sq)]

    # the forking piece must not just be lost for free
    if board.attackers(enemy, to_sq):
        if not board.attackers(mover, to_sq):
            return False
        if _cheapest_attacker_value(board, enemy, to_sq) < forker_value:
            return False

    targets = 0
    for sq in board.attacks(to_sq):
        target = board.piece_at(sq)
        if target is None or target.color != enemy or target.piece_type == chess.PAWN:
            continue
        if target.piece_type == chess.KING:
            targets += 1  # a check counts
            continue
        undefended = not board.attackers(enemy, sq)
        worth_more = PIECE_VALUES[target.piece_type] > forker_value
        if undefended or worth_more:
            targets += 1

    return targets >= 2


def _pinned_squares(board, color):
    pinned = set()
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if piece is None or piece.color != color:
            continue
        if piece.piece_type in (chess.KING, chess.PAWN):
            continue
        if board.is_pinned(color, sq):
            pinned.add(sq)
    return pinned


def detect_missed_pin(fen_before: str, best_move_san: str, mover_color: str) -> bool:
    """True if the engine's best move creates a NEW pin against the opponent."""
    if not best_move_san:
        return False

    board = chess.Board(fen_before)
    try:
        move = board.parse_san(best_move_san)
    except ValueError:
        return False

    enemy = not board.turn
    pins_before = _pinned_squares(board, enemy)
    board.push(move)
    pins_after = _pinned_squares(board, enemy)
    return bool(pins_after - pins_before)


def detect_back_rank_weakness(fen_after: str, mover_color: str) -> bool:
    """King on its back rank, every square in front blocked or covered, enemy has a rook/queen."""
    board = chess.Board(fen_after)
    color = (mover_color == "white")
    enemy = not color

    king_sq = board.king(color)
    if king_sq is None:
        return False

    king_rank = chess.square_rank(king_sq)
    if king_rank != (0 if color else 7):
        return False

    if not (board.pieces(chess.ROOK, enemy) or board.pieces(chess.QUEEN, enemy)):
        return False

    forward_rank = king_rank + (1 if color else -1)
    king_file = chess.square_file(king_sq)
    for f in range(max(0, king_file - 1), min(8, king_file + 2)):
        sq = chess.square(f, forward_rank)
        piece = board.piece_at(sq)
        if piece and piece.color == color:
            continue  # blocked by our own piece
        if board.is_attacked_by(enemy, sq):
            continue  # covered by the enemy
        return False  # the king has a way out
    return True


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

        # only when the move actually allowed a forced mate
        if (move_analysis.eval_after is not None and move_analysis.eval_after <= -9000
                and detect_back_rank_weakness(move_analysis.fen_after, move_analysis.color)):
            tags.append("back_rank_weakness")

    return tags
