from dataclasses import replace
from datetime import datetime
from pathlib import Path
from random import Random
from tempfile import TemporaryDirectory
import unittest
from mathalarm.model import Alarm
from mathalarm.storage import AlarmStore
from mathalarm.schedule import next_occurrence
from mathalarm.examples import ChallengeSession, generate_example

class QualityTests(unittest.TestCase):
    def test_sorted_list(self):
        with TemporaryDirectory(dir=Path(__file__).parent) as d:
            s = AlarmStore(Path(d) / "a.db")
            try:
                s.add(Alarm(18, 0, 1))
                s.add(Alarm(6, 30, 1))
                self.assertEqual([a.hour for a in s.list_all()], [6, 18])
            finally:
                s.close()

    def test_settings_survive_reopen(self):
        with TemporaryDirectory(dir=Path(__file__).parent) as d:
            p = Path(d) / "a.db"
            s = AlarmStore(p)
            a = s.add(Alarm(7, 0, 31))
            b = replace(a, hour=8, minute=15, days_mask=64,
                        difficulty=3, example_count=10, enabled=False)
            s.update(b)
            s.close()
            s = AlarmStore(p)
            try:
                self.assertEqual(s.get(a.id), b)
            finally:
                s.close()

    def test_invalid_minute(self):
        for n in (-1, 60):
            with self.subTest(n=n), self.assertRaises(ValueError):
                Alarm(7, n, 1)

    def test_invalid_days_mask(self):
        for n in (0, 128):
            with self.subTest(n=n), self.assertRaises(ValueError):
                Alarm(7, 0, n)

    def test_invalid_difficulty(self):
        for n in (0, 4):
            with self.subTest(n=n), self.assertRaises(ValueError):
                Alarm(7, 0, 1, difficulty=n)

    def test_invalid_example_count(self):
        for n in (0, 11):
            with self.subTest(n=n), self.assertRaises(ValueError):
                Alarm(7, 0, 1, example_count=n)

    def test_sunday_wrap(self):
        self.assertEqual(next_occurrence(Alarm(8, 0, 64),
            datetime(2026, 11, 22, 8, 0)), datetime(2026, 11, 29, 8, 0))

    def test_next_selected_day(self):
        self.assertEqual(next_occurrence(Alarm(7, 30, 3),
            datetime(2026, 11, 23, 8, 0)), datetime(2026, 11, 24, 7, 30))

    def test_one_answer_finishes(self):
        s = ChallengeSession(1, 1, Random(7))
        self.assertTrue(s.submit(s.current.answer))
        self.assertTrue(s.finished)
        with self.assertRaises(RuntimeError):
            s.submit(0)

    def test_invalid_example_level(self):
        for n in (0, 4):
            with self.subTest(n=n), self.assertRaises(ValueError):
                generate_example(n, Random(7))
