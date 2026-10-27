from dataclasses import dataclass
from random import Random
from typing import Optional


@dataclass(frozen=True)
class Example:
    left: int
    symbol: str
    right: int
    answer: int

    @property
    def question(self) -> str:
        return f"{self.left} {self.symbol} {self.right} = ?"


def generate_example(difficulty: int, rng: Optional[Random] = None) -> Example:
    if type(difficulty) is not int or not 1 <= difficulty <= 3:
        raise ValueError("difficulty must be from 1 to 3")
    rng = rng or Random()
    operations = ("+", "-") if difficulty == 1 else ("+", "-", "×")
    symbol = rng.choice(operations)

    if symbol == "×":
        limit = 9 if difficulty == 2 else 12
        left, right = rng.randint(2, limit), rng.randint(2, limit)
        answer = left * right
    else:
        limit = (9, 20, 99)[difficulty - 1]
        left, right = rng.randint(1, limit), rng.randint(1, limit)
        if symbol == "-":
            left, right = max(left, right), min(left, right)
            answer = left - right
        else:
            answer = left + right
    return Example(left, symbol, right, answer)


class ChallengeSession:
    """The signal may stop only after the configured number of correct answers."""

    def __init__(
        self, difficulty: int, example_count: int, rng: Optional[Random] = None
    ) -> None:
        if type(example_count) is not int or not 1 <= example_count <= 10:
            raise ValueError("example_count must be from 1 to 10")
        self.difficulty = difficulty
        self.example_count = example_count
        self.rng = rng or Random()
        self.solved = 0
        self.current: Optional[Example] = generate_example(difficulty, self.rng)

    @property
    def finished(self) -> bool:
        return self.solved == self.example_count

    def submit(self, answer: int) -> bool:
        if self.finished or self.current is None:
            raise RuntimeError("challenge is already finished")
        if type(answer) is not int or answer != self.current.answer:
            return False
        self.solved += 1
        self.current = (
            None if self.finished else generate_example(self.difficulty, self.rng)
        )
        return True
