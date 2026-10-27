from datetime import datetime, timedelta

from .model import Alarm


def next_occurrence(alarm: Alarm, now: datetime) -> datetime:
    """Return the next selected local calendar time after *now*.

    Android must still schedule this time with AlarmManager. This function
    does not run in the background or handle device-specific clock changes.
    """
    if not alarm.enabled:
        raise ValueError("cannot schedule a disabled alarm")

    for offset in range(8):
        day = now + timedelta(days=offset)
        if not alarm.repeats_on(day.weekday()):
            continue
        candidate = day.replace(
            hour=alarm.hour, minute=alarm.minute, second=0, microsecond=0
        )
        if candidate > now:
            return candidate
    raise RuntimeError("no future occurrence found")
