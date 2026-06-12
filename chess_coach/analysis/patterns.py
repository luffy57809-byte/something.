import chess


def detect_hanging_piece(fen_after: str, mover_color: str) -> bool:
    """
    Check if the player who just moved (mover_color) has left a piece
    hanging - i.e., the opponent can capture it and it's undefended
    (or under-defended relative to attackers).
    """
    board = chess.Board(fen_after)
    mover_is_white = (mover_color == "white")
    opponent_color = chess.BLACK if mover_is_white else chess.WHITE

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is None:
            continue
        if piece.color != mover_is_white:
            continue  # only check the mover's own pieces

        attackers = board.attackers(opponent_color, square)
        if not attackers:
            continue

        defenders = board.attackers(mover_is_white, square)

        # Find the cheapest attacker - if it can take for free or
        # win material, the piece is hanging
        if not defenders:
            return True

        # If attacker value < piece value and undefended (or defenders
        # don't fully cover), it's a likely hang - simple heuristic:
        # more attackers than defenders is a red flag
        if len(attackers) > len(defenders):
            return True

    return False


def detect_missed_fork(fen_before: str, best_move_san: str, mover_color: str) -> bool:
    """
    Check if the engine's recommended move (best_move_san) creates a fork -
    one piece attacking two or more enemy pieces simultaneously.
    """
    if not best_move_san:
        return False

    board = chess.Board(fen_before)
    try:
        move = board.parse_san(best_move_san)
    except ValueError:
        return False

    board.push(move)

    moved_piece_square = move.to_square
    opponent_color = not board.turn  # the side that just "would have" moved

    attacked_pieces = 0
    for square in board.attacks(moved_piece_square):
        target = board.piece_at(square)
        if target and target.color == opponent_color:
            # Count meaningful targets (not pawns, usually)
            if target.piece_type != chess.PAWN:
                attacked_pieces += 1

    return attacked_pieces >= 2


def tag_patterns(move_analysis, fen_before: str) -> list[str]:
    """Run all pattern detectors and return a list of tags."""
    tags = []

    if move_analysis.classification in ("blunder", "mistake"):
        if detect_hanging_piece(move_analysis.fen_after, move_analysis.color):
            tags.append("hanging_piece")

        if detect_missed_fork(fen_before, move_analysis.best_move_san, move_analysis.color):
            tags.append("missed_fork")

    return tags
