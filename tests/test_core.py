from dataclasses import replace
from datetime import datetime
from pathlib import Path
from random import Random
from tempfile import TemporaryDirectory
import unittest

from mathalarm.examples import ChallengeSession, generate_example
from mathalarm.model import Alarm
from mathalarm.schedule import next_occurrence
from mathalarm.storage import AlarmStore


class AlarmCoreTests(unittest.TestCase):
    def test_weekly_schedule_skips_past_time_and_wraps_week(self):
        monday_only = Alarm(hour=7, minute=30, days_mask=1)
        now = datetime(2026, 10, 26, 7, 30)
        self.assertEqual(
            next_occurrence(monday_only, now),
            datetime(2026, 11, 2, 7, 30),
        )

    def test_disabled_alarm_cannot_be_scheduled(self):
        with self.assertRaises(ValueError):
            next_occurrence(
                Alarm(hour=8, minute=0, days_mask=1, enabled=False),
                datetime(2026, 10, 26, 7, 0),
            )

    def test_generated_answers_match_operations_at_all_levels(self):
        rng = Random(42)
        for difficulty in (1, 2, 3):
            for _ in range(100):
                example = generate_example(difficulty, rng)
                actual = {
                    "+": example.left + example.right,
                    "-": example.left - example.right,
                    "×": example.left * example.right,
                }[example.symbol]
                self.assertEqual(example.answer, actual)
                self.assertGreaterEqual(example.answer, 0)

    def test_wrong_answer_does_not_advance_challenge(self):
        session = ChallengeSession(difficulty=2, example_count=2, rng=Random(7))
        first = session.current
        self.assertFalse(session.submit(first.answer + 1))
        self.assertEqual(session.current, first)
        self.assertEqual(session.solved, 0)
        self.assertTrue(session.submit(first.answer))
        self.assertEqual(session.solved, 1)
        self.assertTrue(session.submit(session.current.answer))
        self.assertTrue(session.finished)

    def test_storage_survives_reopen_and_supports_update_delete(self):
        with TemporaryDirectory(dir=Path(__file__).parent) as directory:
            db = Path(directory) / "alarms.sqlite3"
            first = AlarmStore(db)
            saved = first.add(Alarm(hour=6, minute=45, days_mask=31))
            first.close()

            second = AlarmStore(db)
            self.assertEqual(second.get(saved.id), saved)
            changed = replace(saved, hour=7, enabled=False)
            second.update(changed)
            self.assertEqual(second.get(saved.id), changed)
            second.delete(saved.id)
            self.assertEqual(second.list_all(), [])
            second.close()

    def test_invalid_alarm_values_are_rejected(self):
        with self.assertRaises(ValueError):
            Alarm(hour=24, minute=0, days_mask=1)
        with self.assertRaises(ValueError):
            Alarm(hour=7, minute=0, days_mask=0)


if __name__ == "__main__":
    unittest.main()
