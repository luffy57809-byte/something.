PATTERN_EXPLANATIONS = {
    "hanging_piece": (
        "This move left a piece undefended where your opponent could capture it "
        "for free (or win material). Before moving, always check: after this move, "
        "can any of my pieces be captured without recapture?"
    ),
    "missed_fork": (
        "There was a stronger move available that would attack two of your "
        "opponent's pieces at once with a single piece - a fork. Forks are powerful "
        "because the opponent usually can't save both pieces."
    ),
    "missed_pin": (
        "There was a stronger move available that would pin one of your opponent's "
        "pieces - attacking it in a way that it cannot move without exposing a more "
        "valuable piece behind it. Pins restrict your opponent's options and often "
        "win material."
    ),
    "back_rank_weakness": (
        "Your king was left vulnerable on the back rank with pawns blocking its "
        "escape. This is a common way to lose to a back rank checkmate or heavy "
        "piece invasion. Consider making a 'luft' move (h3, g3, etc.) to give "
        "your king an escape square."
    ),
}

CLASSIFICATION_INTROS = {
    "blunder": "This was a serious blunder - it significantly worsened your position.",
    "mistake": "This was a mistake that gave your opponent a meaningful advantage.",
    "inaccuracy": "This was a slight inaccuracy - not terrible, but not the best choice.",
}


def _fmt_eval(cp):
    if cp is None:
        return "?"
    if abs(cp) >= 9000:
        return "mate for you" if cp > 0 else "mate against you"
    return f"{cp / 100:+.1f}"


def generate_explanation(move_analysis) -> str:
    """Generate a template-based explanation for a flagged move."""
    parts = []

    intro = CLASSIFICATION_INTROS.get(move_analysis.classification)
    if intro:
        parts.append(intro)

    for tag in move_analysis.pattern_tags:
        explanation = PATTERN_EXPLANATIONS.get(tag)
        if explanation:
            parts.append(explanation)

    if move_analysis.eval_before is not None and move_analysis.eval_after is not None:
        parts.append(
            f"You played {move_analysis.move_san}, which changed the engine's evaluation "
            f"from {_fmt_eval(move_analysis.eval_before)} to {_fmt_eval(move_analysis.eval_after)} "
            f"(positive numbers favor you)."
        )

    if move_analysis.best_move_san:
        parts.append(f"A stronger move here was {move_analysis.best_move_san}.")

    if not move_analysis.pattern_tags:
        parts.append(
            "This move worsened your position, though the exact tactical or "
            "strategic reason is more subtle - try comparing the position before "
            "and after with the suggested move to spot the difference."
        )

    return " ".join(parts)
