import unittest

import chess

from chess_coach.analysis import patterns as p
from chess_coach.analysis.game_analyzer import win_pct, classify_by_win_chance
from chess_coach.auth import (
    create_access_token, decode_token,
    create_purpose_token, decode_purpose_token,
)

FORK = "r1bqk2r/pppp1ppp/2n2n2/2b1N3/2B1P3/8/PPPP1PPP/RNBQK2R w KQkq - 0 1"
HANG = "r1bqkbnr/pppppppp/2n5/8/3Q4/8/PPPP1PPP/RNB1KBNR w KQkq - 0 1"
PIN = "r1bqkbnr/ppp2ppp/2n5/3pp3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 0 1"
BACK_RANK = "4r1k1/5ppp/8/8/8/8/5PPP/6K1 w - - 0 1"


class PatternTests(unittest.TestCase):
    def test_fork_detected(self):
        self.assertTrue(p.detect_missed_fork(FORK, "Nxf7", "white"))

    def test_hanging_piece_detected(self):
        self.assertTrue(p.detect_hanging_piece(HANG, "white"))

    def test_start_position_has_nothing_hanging(self):
        self.assertFalse(p.detect_hanging_piece(chess.STARTING_FEN, "white"))

    def test_new_pin_detected(self):
        self.assertTrue(p.detect_missed_pin(PIN, "Bb5", "white"))

    def test_back_rank_weakness_detected(self):
        self.assertTrue(p.detect_back_rank_weakness(BACK_RANK, "white"))


class ClassifyTests(unittest.TestCase):
    def test_even_position_is_fifty_percent(self):
        self.assertAlmostEqual(win_pct(0), 50)

    def test_small_loss_is_good(self):
        self.assertEqual(classify_by_win_chance(0, -30), "good")

    def test_inaccuracy_mistake_blunder(self):
        self.assertEqual(classify_by_win_chance(0, -100), "inaccuracy")
        self.assertEqual(classify_by_win_chance(0, -200), "mistake")
        self.assertEqual(classify_by_win_chance(0, -400), "blunder")


class TokenTests(unittest.TestCase):
    def test_verify_token_round_trip(self):
        tok = create_purpose_token("alice", "verify", 5)
        self.assertEqual(decode_purpose_token(tok, "verify")["sub"], "alice")

    def test_wrong_purpose_is_rejected(self):
        tok = create_purpose_token("alice", "verify", 5)
        self.assertIsNone(decode_purpose_token(tok, "reset"))

    def test_emailed_links_cannot_log_in(self):
        tok = create_purpose_token("alice", "verify", 5)
        self.assertIsNone(decode_token(tok))

    def test_login_token_is_not_a_verify_token(self):
        tok = create_access_token({"sub": "alice"})
        self.assertIsNone(decode_purpose_token(tok, "verify"))


if __name__ == "__main__":
    unittest.main()
