import chess
import chess.engine
import os
import shutil

def find_stockfish() -> str:
    """Find stockfish binary - checks multiple locations."""
    # Check local bin directory first (for Render)
    local = os.path.join(os.path.dirname(__file__), "..", "..", "bin", "stockfish")
    local = os.path.abspath(local)
    if os.path.exists(local):
        return local

    # Check system path
    system = shutil.which("stockfish")
    if system:
        return system

    # Common locations
    for path in ["/usr/games/stockfish", "/usr/bin/stockfish", "/usr/local/bin/stockfish"]:
        if os.path.exists(path):
            return path

    raise FileNotFoundError("Stockfish not found. Please install it.")


class ChessEngine:
    def __init__(self, depth: int = 15):
        self.path = find_stockfish()
        self.engine = chess.engine.SimpleEngine.popen_uci(self.path)
        self.depth = depth

    def evaluate(self, board: chess.Board):
        info = self.engine.analyse(board, chess.engine.Limit(depth=self.depth))
        score = info["score"].pov(board.turn)

        if score.is_mate():
            mate_in = score.mate()
            cp = 10000 - abs(mate_in) * 10
            cp = cp if mate_in > 0 else -cp
        else:
            cp = score.score()

        best_move = info.get("pv", [None])[0]
        best_move_san = board.san(best_move) if best_move else None

        return cp, best_move_san

    def close(self):
        self.engine.quit()
