"""Разворот правил расписания в конкретные даты (occurrences)."""

from __future__ import annotations

from datetime import date, timedelta

from .models import Event, Occurrence, Parity, Weekday

_WEEKDAY_INDEX: dict[Weekday, int] = {
    Weekday.monday: 0,
    Weekday.tuesday: 1,
    Weekday.wednesday: 2,
    Weekday.thursday: 3,
    Weekday.friday: 4,
    Weekday.saturday: 5,
    Weekday.sunday: 6,
}


def parity_of(value: date, anchor: date) -> Parity:
    """Чётность недели по якорной дате (понедельник первой чётной недели)."""
    weeks = (value - anchor).days // 7
    return Parity.even if weeks % 2 == 0 else Parity.odd


def expand_event(
    event: Event,
    period_from: date,
    period_to: date,
    anchor: date,
) -> list[date]:
    if event.explicitDates:
        return list(event.explicitDates)

    start = event.dateFrom or period_from
    end = event.dateTo or period_to
    result: list[date] = []
    current = start
    while current <= end:
        if current.weekday() == _WEEKDAY_INDEX[event.weekday] and (
            event.parity == Parity.all or parity_of(current, anchor) == event.parity
        ):
            result.append(current)
        current += timedelta(days=1)
    return result


def build_occurrences(
    group_id: str,
    events: list[Event],
    period_from: date,
    period_to: date,
    anchor: date,
) -> list[Occurrence]:
    result: list[Occurrence] = []
    for event in events:
        for value in expand_event(event, period_from, period_to, anchor):
            result.append(
                Occurrence(
                    groupId=group_id,
                    date=value,
                    start=event.start,
                    end=event.end,
                    eventId=event.id,
                )
            )
    return result
