"""Due-source scheduling logic shared by GET /sources/due.

`sources.schedule` is a validated 5-field cron expression (see api/app/schemas.py).
A source is due when its next scheduled run, computed from its cron expression and
`last_harvest_at`, is not after `now`. A source never harvested is always due.

An unparsable schedule is treated as always due (fail-open) rather than raising, so
a bad row can never silently stop a source from ever being scheduled again; this
should not happen in practice since `POST /sources` already validates the cron
expression.
"""
from datetime import datetime

from croniter import CroniterBadCronError, croniter


def is_due(schedule: str, last_harvest_at: datetime | None, now: datetime) -> bool:
    if last_harvest_at is None:
        return True
    try:
        next_run = croniter(schedule, last_harvest_at).get_next(datetime)
    except (CroniterBadCronError, ValueError):
        return True
    return next_run <= now
