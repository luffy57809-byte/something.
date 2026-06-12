import os
import chess
from anthropic import Anthropic

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

MODEL = "claude-sonnet-4-6"


def explain_move(move_analysis, white_name: str, black_name: str) -> str:
    """Generate a coaching-style explanation for a flagged move."""

    board = chess.Board(move_analysis.fen_before)
    player = white_name if move_analysis.color == "white" else black_name

    prompt = f"""You are a friendly, knowledgeable chess coach reviewing a game with a club-level player.

Position before the move (FEN): {move_analysis.fen_before}
Move played: {move_analysis.move_san} (by {player}, playing {move_analysis.color})
Engine's preferred move instead: {move_analysis.best_move_san}
Evaluation dropped by {move_analysis.eval_drop} centipawns as a result of this move.
Classification: {move_analysis.classification}

Explain in 2-3 short sentences, in plain language a club player (rated 800-1800) would understand:
1. What went wrong with the move played (the underlying idea/plan issue, not just "it loses material" unless that's the core point)
2. What the better move accomplishes instead
3. Avoid restating the engine numbers - explain the chess ideas.

Be encouraging but direct. Don't use phrases like "Move X" - just describe the position/idea."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )

    return response.content[0].text.strip()
