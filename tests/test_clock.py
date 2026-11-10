import unittest
from types import SimpleNamespace

from chess_detector.scorer import _convert_clocks_to_think_times


def mv(color, clock):
    return SimpleNamespace(color=color, think_time_ms=clock)


class ClockTests(unittest.TestCase):
    def test_remaining_clock_becomes_time_spent(self):
        a = SimpleNamespace(time_control="180", moves=[
            mv("white", 180000), mv("black", 180000), mv("white", 178700),
            mv("black", 178100), mv("white", 177400), mv("black", 177800)])
        _convert_clocks_to_think_times(a)
        self.assertEqual([m.think_time_ms for m in a.moves], [0, 0, 1300, 1900, 1300, 300])

    def test_running_it_twice_changes_nothing(self):
        a = SimpleNamespace(time_control="180", moves=[
            mv("white", 180000), mv("black", 180000), mv("white", 178700)])
        _convert_clocks_to_think_times(a)
        _convert_clocks_to_think_times(a)
        self.assertEqual([m.think_time_ms for m in a.moves], [0, 0, 1300])

    def test_increment_is_added_back(self):
        a = SimpleNamespace(time_control="180+2", moves=[
            mv("white", 180000), mv("black", 180000), mv("white", 178700)])
        _convert_clocks_to_think_times(a)
        self.assertEqual(a.moves[2].think_time_ms, 3300)

    def test_daily_games_have_no_usable_clock(self):
        a = SimpleNamespace(time_control="1/86400", moves=[mv("white", 5000)])
        _convert_clocks_to_think_times(a)
        self.assertIsNone(a.moves[0].think_time_ms)


if __name__ == "__main__":
    unittest.main()
