from datetime import date
from pathlib import Path

import pytest

from schedule_parser.cli import build_schedule
from schedule_parser.models import ParserConfig

FIXTURES = Path(__file__).parent / "fixtures"

HEADER = (
    "Группа,День недели,Начало,Конец,Чётность,Действует с,Действует по,"
    "Отдельные даты,Тип занятия,Дисциплина,Преподаватель,Аудитория,Онлайн-ссылка\n"
)


def make_config() -> ParserConfig:
    return ParserConfig(
        academic_year="2026/2027",
        semester="1",
        period_from=date(2026, 9, 1),
        period_to=date(2026, 11, 28),
        parity_anchor=date(2026, 8, 31),
        source_url="https://example.com",
    )


def test_build_schedule():
    schedule, files_count, errors = build_schedule(FIXTURES, make_config())
    assert errors == []
    assert files_count == 1
    assert len(schedule.groups) == 1

    group = schedule.groups[0]
    assert group.id == "345К1"
    assert group.course == 3
    assert len(group.events) == 3
    assert len(schedule.occurrences) == 20

    assert group.events[0].teacher == "Кукина А.С."
    assert group.events[1].teacher == "Порядина Р.Н."
    assert group.events[1].explicitDates == [date(2026, 9, 1), date(2026, 9, 29)]
    assert group.events[2].teacher == "Барышева Т.А."

    assert schedule.meta.academicYear == "2026/2027"
    assert schedule.meta.period.from_ == date(2026, 9, 1)
    assert schedule.meta.sourceUrl == "https://example.com"


def test_bad_header(tmp_path):
    (tmp_path / "bad.csv").write_text("неправильный,заголовок\n", encoding="utf-8")
    schedule, files_count, errors = build_schedule(tmp_path, make_config())
    assert errors == ["bad.csv: неожиданный заголовок: ['неправильный', 'заголовок']"]
    assert schedule.groups == []


def test_bad_weekday(tmp_path):
    (tmp_path / "bad.csv").write_text(
        HEADER
        + "345К1,Субботаx,12:00,13:30,каждую неделю,,,,семинар,Тест,преп. Иванов И.И.,,\n",
        encoding="utf-8",
    )
    schedule, files_count, errors = build_schedule(tmp_path, make_config())
    assert len(errors) == 1
    assert "неизвестный день недели" in errors[0]
    assert schedule.groups == []


def test_empty_input_dir(tmp_path):
    with pytest.raises(FileNotFoundError):
        build_schedule(tmp_path, make_config())
