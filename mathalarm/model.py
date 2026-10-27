from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Alarm:
    hour: int
    minute: int
    days_mask: int
    difficulty: int = 1
    example_count: int = 3
    enabled: bool = True
    id: Optional[int] = None

    def __post_init__(self) -> None:
        if type(self.hour) is not int or not 0 <= self.hour <= 23:
            raise ValueError("hour must be from 0 to 23")
        if type(self.minute) is not int or not 0 <= self.minute <= 59:
            raise ValueError("minute must be from 0 to 59")
        if type(self.days_mask) is not int or not 1 <= self.days_mask <= 127:
            raise ValueError("days_mask must select at least one weekday")
        if type(self.difficulty) is not int or not 1 <= self.difficulty <= 3:
            raise ValueError("difficulty must be from 1 to 3")
        if type(self.example_count) is not int or not 1 <= self.example_count <= 10:
            raise ValueError("example_count must be from 1 to 10")
        if type(self.enabled) is not bool:
            raise ValueError("enabled must be boolean")
        if self.id is not None and (type(self.id) is not int or self.id < 1):
            raise ValueError("id must be a positive integer")

    def repeats_on(self, weekday: int) -> bool:
        """Monday is 0, Sunday is 6."""
        if type(weekday) is not int or not 0 <= weekday <= 6:
            raise ValueError("weekday must be from 0 to 6")
        return bool(self.days_mask & (1 << weekday))
