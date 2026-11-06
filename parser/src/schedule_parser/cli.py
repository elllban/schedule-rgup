"""CLI парсера: `python -m schedule_parser parse ...`."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from .csv_reader import EXPECTED_HEADER, read_rows
from .models import (
    Event,
    Group,
    Meta,
    Occurrence,
    Parity,
    ParserConfig,
    Period,
    Schedule,
    SourceFile,
)
from .normalize import (
    clean_teacher,
    normalize_lesson_type,
    normalize_parity,
    normalize_weekday,
    parse_date,
    parse_explicit_dates,
    parse_time,
)
from .occurrences import build_occurrences, parity_of
from .report import print_report


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_config(path: Path) -> ParserConfig:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    return ParserConfig.model_validate(data)


def record_to_event(
    record: dict[str, str],
    source: str,
    anchor,
) -> Event:
    group_id = record["Группа"]
    if not group_id:
        raise ValueError("пустое значение в колонке «Группа»")

    warnings: list[str] = []
    weekday = normalize_weekday(record["День недели"])
    start = parse_time(record["Начало"])
    end = parse_time(record["Конец"])
    parity = normalize_parity(record["Чётность"])
    date_from = parse_date(record["Действует с"])
    date_to = parse_date(record["Действует по"])
    explicit = parse_explicit_dates(record["Отдельные даты"])
    lesson_type = normalize_lesson_type(record["Тип занятия"])

    discipline = record["Дисциплина"] or None
    if not discipline:
        warnings.append("пустая дисциплина")

    teacher_raw = record["Преподаватель"]
    teacher = clean_teacher(teacher_raw) if teacher_raw else None
    if not teacher_raw:
        warnings.append("пустой преподаватель")

    room = record["Аудитория"] or None
    online = record["Онлайн-ссылка"] or None

    if date_from and date_to and date_from > date_to:
        warnings.append(f"«Действует с» ({date_from}) позже «Действует по» ({date_to})")

    if explicit and parity is not Parity.all:
        for value in explicit:
            if parity_of(value, anchor) != parity:
                warnings.append(
                    f"дата {value} не соответствует чётности «{parity.value}»"
                )

    return Event(
        id=str(uuid4()),
        weekday=weekday,
        start=start,
        end=end,
        parity=parity,
        dateFrom=date_from,
        dateTo=date_to,
        explicitDates=explicit,
        lessonType=lesson_type,
        discipline=discipline,
        teacher=teacher,
        room=room,
        onlineLink=online,
        source=source,
        raw=",".join(record[name] for name in EXPECTED_HEADER),
        warnings=warnings,
    )


def _derive_course(group_id: str) -> int | None:
    if group_id and group_id[0].isdigit():
        return int(group_id[0])
    return None


def build_schedule(
    input_dir: Path,
    config: ParserConfig,
) -> tuple[Schedule, int, list[str]]:
    files = sorted(input_dir.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"в {input_dir} нет файлов *.csv")

    errors: list[str] = []
    groups_map: dict[str, list[Event]] = {}
    source_files: list[SourceFile] = []
    now = datetime.now(UTC).isoformat()

    for path in files:
        try:
            rows = read_rows(path)
        except ValueError as exc:
            errors.append(f"{path.name}: {exc}")
            continue

        source_files.append(
            SourceFile(file=path.name, hash=_sha256(path), parsedAt=now)
        )
        for line_no, record in enumerate(rows, start=2):
            try:
                event = record_to_event(record, path.name, config.parity_anchor)
            except ValueError as exc:
                errors.append(f"{path.name}:{line_no}: {exc}")
                continue
            groups_map.setdefault(record["Группа"], []).append(event)

    groups: list[Group] = []
    occurrences: list[Occurrence] = []
    global_warnings: list[str] = []

    for group_id in sorted(groups_map):
        events = groups_map[group_id]
        occurrences.extend(
            build_occurrences(
                group_id,
                events,
                config.period_from,
                config.period_to,
                config.parity_anchor,
            )
        )
        groups.append(
            Group(id=group_id, course=_derive_course(group_id), events=events)
        )

    global_warnings.extend(_detect_duplicates(groups_map))

    schedule = Schedule(
        meta=Meta(
            generatedAt=now,
            academicYear=config.academic_year,
            semester=config.semester,
            period=Period(from_=config.period_from, to=config.period_to),
            sourceUrl=config.source_url,
            sourceFiles=source_files,
        ),
        groups=groups,
        occurrences=occurrences,
        warnings=global_warnings,
    )
    return schedule, len(files), errors


def _detect_duplicates(groups_map: dict[str, list[Event]]) -> list[str]:
    warnings: list[str] = []
    for group_id, events in groups_map.items():
        seen: dict[tuple, str] = {}
        for event in events:
            key = (
                event.weekday,
                event.start,
                event.end,
                event.parity,
                event.discipline,
                tuple(event.explicitDates),
                event.dateFrom,
                event.dateTo,
            )
            if key in seen:
                warnings.append(
                    f"{group_id}: дублирующее правило (совпадает с событием "
                    f"{seen[key]}) — {event.discipline}, {event.weekday.value} "
                    f"{event.start}–{event.end}"
                )
            else:
                seen[key] = event.id
    return warnings


def cmd_parse(args: argparse.Namespace) -> int:
    input_dir = Path(args.input)
    meta_path = Path(args.meta)
    output_path = Path(args.output)

    config = load_config(meta_path)
    try:
        schedule, files_count, errors = build_schedule(input_dir, config)
    except FileNotFoundError as exc:
        print(f"Ошибка: {exc}")
        return 1

    if errors and not args.force:
        print_report(schedule, files_count, errors, str(output_path))
        print(
            "\nЕсть ошибки. schedule.json НЕ записан. "
            "Повторите с --force, чтобы записать частичный результат."
        )
        return 1

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(
            schedule.model_dump(mode="json", by_alias=True),
            handle,
            ensure_ascii=False,
            indent=2,
        )
        handle.write("\n")

    print_report(schedule, files_count, errors, str(output_path))
    return 0


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="schedule-parser",
        description="Парсер расписания ЗСФ РГУП из CSV в JSON",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_parser = subparsers.add_parser("parse", help="собрать schedule.json из CSV")
    parse_parser.add_argument(
        "--input", default="data/raw", help="папка с CSV (по умолчанию data/raw)"
    )
    parse_parser.add_argument(
        "--meta", default="data/meta.json", help="настройки (по умолчанию data/meta.json)"
    )
    parse_parser.add_argument(
        "--output",
        default="web/src/data/schedule.json",
        help="куда писать результат",
    )
    parse_parser.add_argument(
        "--force",
        action="store_true",
        help="записать schedule.json даже при наличии ошибок",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    if args.command == "parse":
        return cmd_parse(args)
    print("неизвестная команда", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
