"""Нормализация русских значений CSV в enum и типы схемы."""

from __future__ import annotations

import re
from datetime import date, datetime

from .models import LessonType, Parity, Weekday

WEEKDAY_MAP: dict[str, Weekday] = {
    "понедельник": Weekday.monday,
    "вторник": Weekday.tuesday,
    "среда": Weekday.wednesday,
    "четверг": Weekday.thursday,
    "пятница": Weekday.friday,
    "суббота": Weekday.saturday,
    "воскресенье": Weekday.sunday,
}

PARITY_MAP: dict[str, Parity] = {
    "каждую неделю": Parity.all,
    "четная": Parity.even,
    "нечетная": Parity.odd,
}

LESSON_TYPE_MAP: dict[str, LessonType] = {
    "лекция": LessonType.lecture,
    "семинар": LessonType.seminar,
    "другое": LessonType.other,
}

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")

# Заголовки учёных званий и должностей, отделяемые от ФИО.
_TITLE_PATTERN = re.compile(
    r"^(?:"
    r"[кд]\.[а-яё]+\.[нп]\.|"
    r"доцент|профессор|проф\.|преп\.|преподаватель|"
    r"старший\s+преподаватель|ст\.\s*преп\.|ассистент|"
    r"зав\.\s*кафедрой|и\.о\."
    r")[\s,]+",
    re.IGNORECASE,
)


def normalize_weekday(raw: str) -> Weekday:
    key = raw.strip().lower().replace("ё", "е")
    try:
        return WEEKDAY_MAP[key]
    except KeyError as exc:
        raise ValueError(f"неизвестный день недели: {raw!r}") from exc


def normalize_parity(raw: str) -> Parity:
    key = raw.strip().lower().replace("ё", "е")
    try:
        return PARITY_MAP[key]
    except KeyError as exc:
        raise ValueError(f"неизвестная чётность: {raw!r}") from exc


def normalize_lesson_type(raw: str) -> LessonType:
    key = raw.strip().lower().replace("ё", "е")
    try:
        return LESSON_TYPE_MAP[key]
    except KeyError as exc:
        raise ValueError(f"неизвестный тип занятия: {raw!r}") from exc


def parse_date(raw: str | None) -> date | None:
    if not raw or not raw.strip():
        return None
    return datetime.strptime(raw.strip(), "%d.%m.%Y").date()


def parse_time(raw: str) -> str:
    value = raw.strip()
    if not _TIME_RE.match(value):
        raise ValueError(f"неверное время: {raw!r}")
    return value


def parse_explicit_dates(raw: str | None) -> list[date]:
    if not raw or not raw.strip():
        return []
    result: list[date] = []
    for part in raw.split(";"):
        part = part.strip()
        if part:
            result.append(parse_date(part))
    return result


def clean_teacher(raw: str) -> str:
    name = raw.strip()
    previous = None
    while previous != name:
        previous = name
        name = _TITLE_PATTERN.sub("", name).strip()
    return name
