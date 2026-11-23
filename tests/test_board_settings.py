import unittest

from chess_coach.board_settings import DEFAULTS, normalize_settings


class SettingsTests(unittest.TestCase):
    def test_empty_gives_defaults(self):
        self.assertEqual(normalize_settings({}), DEFAULTS)
        self.assertEqual(normalize_settings(None), DEFAULTS)
        self.assertEqual(normalize_settings("x"), DEFAULTS)

    def test_valid_values_are_kept(self):
        out = normalize_settings({"theme": "slate", "highlight": "rose", "size": "large", "animation": "off"})
        self.assertEqual(out["theme"], "slate")
        self.assertEqual(out["highlight"], "rose")
        self.assertEqual(out["size"], "large")
        self.assertEqual(out["animation"], "off")

    def test_bad_values_fall_back_to_defaults(self):
        self.assertEqual(normalize_settings({"theme": "nope"})["theme"], "walnut")
        self.assertEqual(normalize_settings({"theme": ["green"]})["theme"], "walnut")
        self.assertIs(normalize_settings({"coordinates": "yes"})["coordinates"], True)
        self.assertIs(normalize_settings({"legalMoves": 0})["legalMoves"], True)

    def test_booleans_can_be_turned_off(self):
        out = normalize_settings({"coordinates": False, "legalMoves": False})
        self.assertIs(out["coordinates"], False)
        self.assertIs(out["legalMoves"], False)

    def test_unknown_keys_are_dropped(self):
        self.assertNotIn("junk", normalize_settings({"junk": "x" * 100000}))


if __name__ == "__main__":
    unittest.main()
