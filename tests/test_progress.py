import unittest

from chess_coach.stats import _progress_from_rows


# row: game_id, classification, color, pattern_tags, eval_drop, eval_before, eval_after, date, white, black, result
def row(gid, cls, color, tags, drop, eb, ea, date, white, black, result):
    return (gid, cls, color, tags, drop, eb, ea, date, white, black, result)


ROWS = [
    row("g2", "good", "black", "[]", 0, 20, 15, "2026.11.05", "opp2", "me", "0-1"),
    row("g2", "blunder", "black", '["hanging_piece"]', 400, 100, -300, "2026.11.05", "opp2", "me", "0-1"),
    row("g1", "good", "white", "[]", 0, 30, 25, "2026.11.01", "me", "opp1", "0-1"),
    row("g1", "good", "white", "[]", 0, 25, 20, "2026.11.01", "me", "opp1", "0-1"),
    row("g3", "inaccuracy", "white", '["missed_fork"]', 80, 50, -20, "2026.11.05", "me", "opp3", "1/2-1/2"),
]


class ProgressTests(unittest.TestCase):
    def test_games_are_grouped_and_ordered_by_date(self):
        games = _progress_from_rows(ROWS)["games"]
        self.assertEqual([g["game_id"] for g in games], ["g1", "g2", "g3"])

    def test_results_are_from_the_users_side(self):
        g1, g2, g3 = _progress_from_rows(ROWS)["games"]
        self.assertEqual((g1["outcome"], g1["opponent"]), ("loss", "opp1"))
        self.assertEqual((g2["outcome"], g2["opponent"]), ("win", "opp2"))
        self.assertEqual(g3["outcome"], "draw")

    def test_counts_and_accuracy(self):
        g1, g2, g3 = _progress_from_rows(ROWS)["games"]
        self.assertEqual(g1["accuracy_pct"], 100.0)
        self.assertEqual(g2["blunders"], 1)
        self.assertLess(g2["accuracy_pct"], 80)
        self.assertEqual(g3["inaccuracies"], 1)

    def test_pattern_counts(self):
        self.assertEqual(_progress_from_rows(ROWS)["pattern_counts"],
                         {"hanging_piece": 1, "missed_fork": 1})

    def test_limit_keeps_the_newest_games_only(self):
        out = _progress_from_rows(ROWS, limit=1)
        self.assertEqual([g["game_id"] for g in out["games"]], ["g3"])
        self.assertEqual(out["pattern_counts"], {"missed_fork": 1})

    def test_no_rows(self):
        self.assertEqual(_progress_from_rows([]), {"games": [], "pattern_counts": {}})


if __name__ == "__main__":
    unittest.main()
