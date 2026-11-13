import unittest

from chess_coach.throttle import LoginThrottle

T0 = 1_000_000.0


class ThrottleTests(unittest.TestCase):
    def locked_alice(self):
        t = LoginThrottle()
        for i in range(8):
            self.assertEqual(t.wait_seconds("Alice", "1.1.1.1", now=T0 + i), 0)
            t.record_failure("Alice", "1.1.1.1", now=T0 + i)
        return t

    def test_ninth_attempt_must_wait(self):
        t = self.locked_alice()
        wait = t.wait_seconds("alice", "1.1.1.1", now=T0 + 10)  # case-insensitive
        self.assertTrue(0 < wait <= 15 * 60)

    def test_other_users_are_not_locked(self):
        t = self.locked_alice()
        self.assertEqual(t.wait_seconds("bob", "1.1.1.1", now=T0 + 10), 0)

    def test_the_account_is_protected_from_any_address(self):
        t = self.locked_alice()
        self.assertGreater(t.wait_seconds("alice", "9.9.9.9", now=T0 + 10), 0)

    def test_lock_lifts_after_the_window(self):
        t = self.locked_alice()
        self.assertEqual(t.wait_seconds("alice", "1.1.1.1", now=T0 + 15 * 60 + 1), 0)

    def test_success_clears_the_account(self):
        t = self.locked_alice()
        t.record_success("alice")
        self.assertEqual(t.wait_seconds("alice", "1.1.1.1", now=T0 + 20), 0)

    def test_address_backstop(self):
        t = LoginThrottle(max_per_ip=5)
        for i in range(5):
            t.record_failure(f"user{i}", "2.2.2.2", now=T0)
        self.assertGreater(t.wait_seconds("new_user", "2.2.2.2", now=T0 + 1), 0)
        self.assertEqual(t.wait_seconds("new_user", "3.3.3.3", now=T0 + 1), 0)

    def test_memory_is_bounded(self):
        t = LoginThrottle(max_keys=10)
        for i in range(50):
            t.record_failure(f"u{i}", f"ip{i}", now=T0)
        self.assertLessEqual(len(t._failed), 22)


if __name__ == "__main__":
    unittest.main()
