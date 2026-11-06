"""Pydantic-модели: входная конфигурация и выходная схема расписания."""

from __future__ import annotations

from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Weekday(StrEnum):
    monday = "monday"
    tuesday = "tuesday"
    wednesday = "wednesday"
    thursday = "thursday"
    friday = "friday"
    saturday = "saturday"
    sunday = "sunday"


class Parity(StrEnum):
    even = "even"
    odd = "odd"
    all = "all"


class LessonType(StrEnum):
    lecture = "lecture"
    seminar = "seminar"
    other = "other"


class ParserConfig(BaseModel):
    """Настройки парсера (data/meta.json)."""

    academic_year: str
    semester: str
    period_from: date
    period_to: date
    parity_anchor: date
    source_url: str


class Period(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    from_: date = Field(alias="from")
    to: date


class SourceFile(BaseModel):
    file: str
    hash: str
    parsedAt: str


class Meta(BaseModel):
    generatedAt: str
    academicYear: str
    semester: str
    period: Period
    sourceUrl: str
    sourceFiles: list[SourceFile] = Field(default_factory=list)


class Event(BaseModel):
    id: str
    weekday: Weekday
    start: str
    end: str
    parity: Parity
    dateFrom: date | None = None
    dateTo: date | None = None
    explicitDates: list[date] = Field(default_factory=list)
    lessonType: LessonType
    discipline: str | None = None
    teacher: str | None = None
    room: str | None = None
    onlineLink: str | None = None
    source: str
    raw: str
    warnings: list[str] = Field(default_factory=list)


class Group(BaseModel):
    id: str
    program: str | None = None
    course: int | None = None
    events: list[Event] = Field(default_factory=list)


class Occurrence(BaseModel):
    groupId: str
    date: date
    start: str
    end: str
    eventId: str


class Schedule(BaseModel):
    meta: Meta
    groups: list[Group] = Field(default_factory=list)
    occurrences: list[Occurrence] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
