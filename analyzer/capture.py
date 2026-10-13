"""Hardware-neutral capture events and CSV export."""

from __future__ import annotations

from dataclasses import dataclass
import csv
from pathlib import Path


@dataclass(frozen=True, slots=True)
class CaptureEvent:
    timestamp_us: int
    channel: int
    level: bool


class Capture:
    def __init__(self, events: list[CaptureEvent] | None = None):
        self.events = events or []
        self.dropped_samples = 0

    def append(self, event: CaptureEvent) -> None:
        if event.timestamp_us < 0 or event.channel < 0:
            raise ValueError("capture event timestamp and channel must be non-negative")
        self.events.append(event)

    def export_csv(self, path: str | Path) -> None:
        with Path(path).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.writer(stream)
            writer.writerow(("timestamp_us", "channel", "level"))
            writer.writerows((event.timestamp_us, event.channel, int(event.level)) for event in self.events)
