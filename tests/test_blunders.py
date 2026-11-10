import unittest

from chess_detector.scorer import blunder_suspicion


class BlunderTests(unittest.TestCase):
    def test_strong_player_with_no_blunders_is_not_suspicious(self):
        self.assertEqual(blunder_suspicion(0, 28, 3300)[0], 0.0)

    def test_weak_player_with_no_blunders_in_a_long_game_is_notable(self):
        self.assertGreater(blunder_suspicion(0, 70, 1200)[0], 40)

    def test_a_blunder_removes_the_signal(self):
        self.assertEqual(blunder_suspicion(1, 40, 1200)[0], 0.0)

    def test_unknown_rating_or_short_game_is_not_scored(self):
        self.assertEqual(blunder_suspicion(0, 40, None)[0], 0.0)
        self.assertEqual(blunder_suspicion(0, 9, 1500)[0], 0.0)


if __name__ == "__main__":
    unittest.main()
