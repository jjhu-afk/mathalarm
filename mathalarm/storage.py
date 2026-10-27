import sqlite3
from dataclasses import replace
from pathlib import Path
from typing import List, Optional, Union

from .model import Alarm


class AlarmStore:
    def __init__(self, path: Union[str, Path]) -> None:
        self.connection = sqlite3.connect(str(path))
        self.connection.row_factory = sqlite3.Row
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS alarms (
                id INTEGER PRIMARY KEY,
                hour INTEGER NOT NULL CHECK (hour BETWEEN 0 AND 23),
                minute INTEGER NOT NULL CHECK (minute BETWEEN 0 AND 59),
                days_mask INTEGER NOT NULL CHECK (days_mask BETWEEN 1 AND 127),
                difficulty INTEGER NOT NULL CHECK (difficulty BETWEEN 1 AND 3),
                example_count INTEGER NOT NULL CHECK (example_count BETWEEN 1 AND 10),
                enabled INTEGER NOT NULL CHECK (enabled IN (0, 1))
            )
            """
        )
        self.connection.commit()

    @staticmethod
    def _from_row(row: sqlite3.Row) -> Alarm:
        return Alarm(
            id=row["id"],
            hour=row["hour"],
            minute=row["minute"],
            days_mask=row["days_mask"],
            difficulty=row["difficulty"],
            example_count=row["example_count"],
            enabled=bool(row["enabled"]),
        )

    def add(self, alarm: Alarm) -> Alarm:
        if alarm.id is not None:
            raise ValueError("new alarm must not have an id")
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO alarms
                    (hour, minute, days_mask, difficulty, example_count, enabled)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    alarm.hour,
                    alarm.minute,
                    alarm.days_mask,
                    alarm.difficulty,
                    alarm.example_count,
                    int(alarm.enabled),
                ),
            )
        return replace(alarm, id=cursor.lastrowid)

    def list_all(self) -> List[Alarm]:
        rows = self.connection.execute(
            "SELECT * FROM alarms ORDER BY hour, minute, id"
        ).fetchall()
        return [self._from_row(row) for row in rows]

    def get(self, alarm_id: int) -> Optional[Alarm]:
        row = self.connection.execute(
            "SELECT * FROM alarms WHERE id = ?", (alarm_id,)
        ).fetchone()
        return None if row is None else self._from_row(row)

    def update(self, alarm: Alarm) -> None:
        if alarm.id is None:
            raise ValueError("alarm must have an id")
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE alarms
                SET hour=?, minute=?, days_mask=?, difficulty=?, example_count=?,
                    enabled=?
                WHERE id=?
                """,
                (
                    alarm.hour,
                    alarm.minute,
                    alarm.days_mask,
                    alarm.difficulty,
                    alarm.example_count,
                    int(alarm.enabled),
                    alarm.id,
                ),
            )
        if cursor.rowcount != 1:
            raise KeyError(alarm.id)

    def delete(self, alarm_id: int) -> None:
        with self.connection:
            self.connection.execute("DELETE FROM alarms WHERE id = ?", (alarm_id,))

    def close(self) -> None:
        self.connection.close()
