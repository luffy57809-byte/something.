import chess
from chess_coach.analysis.engine import ChessEngine

if __name__ == "__main__":
    board = chess.Board()  # starting position
    engine = ChessEngine(depth=12)

    cp, best = engine.evaluate(board)
    print(f"Starting position eval: {cp} cp, best move: {best}")

    engine.close()
