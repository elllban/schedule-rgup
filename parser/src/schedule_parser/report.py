"""Сводный отчёт о парсинге."""

from __future__ import annotations

from .models import Schedule


def print_report(
    schedule: Schedule,
    files_count: int,
    errors: list[str],
    output_path: str,
) -> None:
    events = sum(len(group.events) for group in schedule.groups)
    print("=" * 60)
    print("Отчёт о парсинге расписания")
    print("=" * 60)
    print(f"Файлов CSV обработано: {files_count}")
    print(f"Групп: {len(schedule.groups)}")
    print(f"Событий (правил): {events}")
    print(f"Занятий (occurrences): {len(schedule.occurrences)}")
    print(f"Предупреждений: {len(schedule.warnings)}")
    print(f"Ошибок: {len(errors)}")

    if schedule.groups:
        print()
        print("Группы:")
        for group in schedule.groups:
            print(f"  {group.id}: курс {group.course}, событий {len(group.events)}")

    if schedule.warnings:
        print()
        print("Предупреждения:")
        for warning in schedule.warnings:
            print(f"  - {warning}")

    if errors:
        print()
        print("Ошибки:")
        for error in errors:
            print(f"  - {error}")

    print()
    print(f"Результат записан в: {output_path}")
