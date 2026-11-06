from datetime import date

import pytest

from schedule_parser.models import LessonType, Parity, Weekday
from schedule_parser.normalize import (
    clean_teacher,
    normalize_lesson_type,
    normalize_parity,
    normalize_weekday,
    parse_date,
    parse_explicit_dates,
    parse_time,
)


def test_normalize_weekday():
    assert normalize_weekday("Понедельник") == Weekday.monday
    assert normalize_weekday("суббота") == Weekday.saturday
    assert normalize_weekday("Среда") == Weekday.wednesday


def test_normalize_weekday_unknown():
    with pytest.raises(ValueError):
        normalize_weekday("Субботаx")


def test_normalize_parity():
    assert normalize_parity("каждую неделю") == Parity.all
    assert normalize_parity("чётная") == Parity.even
    assert normalize_parity("нечётная") == Parity.odd
    assert normalize_parity("четная") == Parity.even


def test_normalize_lesson_type():
    assert normalize_lesson_type("лекция") == LessonType.lecture
    assert normalize_lesson_type("семинар") == LessonType.seminar
    assert normalize_lesson_type("другое") == LessonType.other


def test_parse_date():
    assert parse_date("07.09.2026") == date(2026, 9, 7)
    assert parse_date("") is None
    assert parse_date(None) is None


def test_parse_time():
    assert parse_time("15:30") == "15:30"
    assert parse_time("08:05") == "08:05"


def test_parse_time_invalid():
    with pytest.raises(ValueError):
        parse_time("25:00")


def test_parse_explicit_dates():
    assert parse_explicit_dates("01.09.2026; 29.09.2026") == [
        date(2026, 9, 1),
        date(2026, 9, 29),
    ]
    assert parse_explicit_dates("") == []


def test_clean_teacher():
    assert clean_teacher("доцент Кукина А.С.") == "Кукина А.С."
    assert clean_teacher("к.ф.н. доцент Порядина Р.Н.") == "Порядина Р.Н."
    assert clean_teacher("ст. преп. Шаклеин В.В.") == "Шаклеин В.В."
    assert clean_teacher("преп. Барышева Т.А.") == "Барышева Т.А."
    assert clean_teacher("Кукина А.С.") == "Кукина А.С."
