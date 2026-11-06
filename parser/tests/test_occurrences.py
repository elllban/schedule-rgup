from datetime import date

from schedule_parser.models import Event, LessonType, Parity, Weekday
from schedule_parser.occurrences import expand_event, parity_of

ANCHOR = date(2026, 8, 31)
PERIOD_FROM = date(2026, 9, 1)
PERIOD_TO = date(2026, 11, 28)


def make_event(**kwargs) -> Event:
    defaults = dict(
        id="e1",
        weekday=Weekday.monday,
        start="12:00",
        end="13:30",
        parity=Parity.all,
        dateFrom=None,
        dateTo=None,
        explicitDates=[],
        lessonType=LessonType.lecture,
        discipline="Дисциплина",
        teacher=None,
        room=None,
        onlineLink=None,
        source="t.csv",
        raw="",
    )
    defaults.update(kwargs)
    return Event(**defaults)


def test_parity_of():
    assert parity_of(date(2026, 8, 31), ANCHOR) == Parity.even
    assert parity_of(date(2026, 9, 7), ANCHOR) == Parity.odd
    assert parity_of(date(2026, 9, 14), ANCHOR) == Parity.even


def test_explicit_dates_win():
    event = make_event(
        explicitDates=[date(2026, 9, 1), date(2026, 9, 29)],
        parity=Parity.even,
    )
    result = expand_event(event, PERIOD_FROM, PERIOD_TO, ANCHOR)
    assert result == [date(2026, 9, 1), date(2026, 9, 29)]


def test_every_week_range():
    event = make_event(weekday=Weekday.monday, dateFrom=date(2026, 9, 7))
    result = expand_event(event, PERIOD_FROM, PERIOD_TO, ANCHOR)
    assert result[0] == date(2026, 9, 7)
    assert date(2026, 11, 23) in result
    assert len(result) == 12


def test_odd_week_full_period():
    event = make_event(weekday=Weekday.wednesday, parity=Parity.odd)
    result = expand_event(event, PERIOD_FROM, PERIOD_TO, ANCHOR)
    assert result == [
        date(2026, 9, 9),
        date(2026, 9, 23),
        date(2026, 10, 7),
        date(2026, 10, 21),
        date(2026, 11, 4),
        date(2026, 11, 18),
    ]
