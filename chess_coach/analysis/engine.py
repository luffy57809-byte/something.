import chess
import chess.engine

STOCKFISH_PATH = "/usr/games/stockfish"


class ChessEngine:
    def __init__(self, path: str = STOCKFISH_PATH, depth: int = 15):
        self.engine = chess.engine.SimpleEngine.popen_uci(path)
        self.depth = depth

    def evaluate(self, board: chess.Board):
        """
        Returns a tuple: (eval_centipawns, best_move_san)
        eval is from the perspective of the side to move.
        Mate scores are converted to large centipawn values.
        """
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
