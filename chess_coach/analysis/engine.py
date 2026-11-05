import chess
import chess.engine
import os
import shutil

MATE_CP = 10000


def find_stockfish() -> str:
    """Find stockfish binary - checks multiple locations."""
    local = os.path.join(os.path.dirname(__file__), "..", "..", "bin", "stockfish")
    local = os.path.abspath(local)
    if os.path.exists(local):
        return local

    system = shutil.which("stockfish")
    if system:
        return system

    for path in ["/usr/games/stockfish", "/usr/bin/stockfish", "/usr/local/bin/stockfish"]:
        if os.path.exists(path):
            return path

    raise FileNotFoundError("Stockfish not found. Please install it.")


class ChessEngine:
    def __init__(self, depth: int = 12):
        self.path = find_stockfish()
        self.engine = chess.engine.SimpleEngine.popen_uci(self.path)
        self.engine.configure({"Threads": 1, "Hash": 64})
        self.depth = depth

    def evaluate(self, board: chess.Board):
        """Return (centipawns from the side to move's view, best move in SAN)."""
        if board.is_game_over():
            outcome = board.outcome()
            if outcome is None or outcome.winner is None:
                return 0, None
            return -MATE_CP, None  # side to move has been checkmated

        info = self.engine.analyse(board, chess.engine.Limit(depth=self.depth))
        score = info["score"].pov(board.turn)
        cp = score.score(mate_score=MATE_CP)

        pv = info.get("pv") or []
        best_move_san = board.san(pv[0]) if pv else None
        return cp, best_move_san

    def close(self):
        try:
            self.engine.quit()
        except Exception:
            pass
