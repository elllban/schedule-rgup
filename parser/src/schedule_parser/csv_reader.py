"""Чтение и валидация CSV-файлов расписания."""

from __future__ import annotations

import csv
from pathlib import Path

EXPECTED_HEADER = [
    "Группа",
    "День недели",
    "Начало",
    "Конец",
    "Чётность",
    "Действует с",
    "Действует по",
    "Отдельные даты",
    "Тип занятия",
    "Дисциплина",
    "Преподаватель",
    "Аудитория",
    "Онлайн-ссылка",
]


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.reader(handle))

    if not rows:
        raise ValueError("файл пуст")

    header = [cell.strip() for cell in rows[0]]
    if header != EXPECTED_HEADER:
        raise ValueError(f"неожиданный заголовок: {header}")

    result: list[dict[str, str]] = []
    for line_no, line in enumerate(rows[1:], start=2):
        if not line or all(not cell.strip() for cell in line):
            continue
        if len(line) > len(EXPECTED_HEADER):
            raise ValueError(
                f"строка {line_no}: лишних колонок "
                f"{len(line) - len(EXPECTED_HEADER)}"
            )
        record = {
            name: (line[i].strip() if i < len(line) else "")
            for i, name in enumerate(EXPECTED_HEADER)
        }
        result.append(record)
    return result
