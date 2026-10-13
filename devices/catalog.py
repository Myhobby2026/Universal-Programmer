"""Validated device profile catalog; protocol capability never implies target support."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
from typing import Iterable

from core.models import DeviceProfile, InterfaceType, SupportLevel


BUILTIN_PROFILES = (
    DeviceProfile(
        manufacturer="Winbond", family="SPI NOR", part_number="W25Q128JV",
        category="Serial flash", interface=InterfaceType.SPI, capacity_bytes=16 * 1024 * 1024,
        address_width=24, page_size=256, erase_size=4096, voltage_min=2.7, voltage_max=3.6,
        identification="JEDEC ID (0x9F)", algorithm="Not included; target algorithm is gated",
        operations=["identify"], support_level=SupportLevel.PROFILE_ONLY,
        validation_notes="Profile only; programming algorithm and hardware adapter require validation.",
        capabilities={"jedec-id"},
    ),
    DeviceProfile(
        manufacturer="Microchip", family="I²C EEPROM", part_number="24LC256",
        category="EEPROM", interface=InterfaceType.I2C, capacity_bytes=32768,
        address_width=16, page_size=64, voltage_min=2.5, voltage_max=5.5,
        identification="I²C ACK and configured address", algorithm="Not included; target algorithm is gated",
        operations=["identify"], support_level=SupportLevel.PROFILE_ONLY,
        validation_notes="Profile only; voltage and adapter wiring must be validated before use.",
        capabilities={"ack-polling"},
    ),
)


class DeviceCatalog:
    def __init__(self, profiles: Iterable[DeviceProfile] = BUILTIN_PROFILES):
        self._profiles: dict[str, DeviceProfile] = {}
        for profile in profiles:
            self.add(profile)

    def add(self, profile: DeviceProfile) -> None:
        errors = profile.validate()
        if errors:
            raise ValueError(f"invalid profile {profile.part_number}: {'; '.join(errors)}")
        self._profiles[profile.part_number.upper()] = profile

    def get(self, part_number: str) -> DeviceProfile | None:
        return self._profiles.get(part_number.upper())

    def search(self, query: str = "") -> list[DeviceProfile]:
        needle = query.casefold().strip()
        return [p for p in self._profiles.values() if not needle or needle in " ".join((p.manufacturer, p.family, p.part_number, p.category)).casefold()]

    def export_json(self, path: str | Path) -> None:
        payload = []
        for profile in self._profiles.values():
            item = asdict(profile)
            item["interface"] = profile.interface.value
            item["support_level"] = profile.support_level.value
            item["capabilities"] = sorted(profile.capabilities)
            payload.append(item)
        Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")

    @classmethod
    def import_json(cls, path: str | Path) -> "DeviceCatalog":
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
        if not isinstance(raw, list):
            raise ValueError("profile file must contain a JSON list")
        return cls(DeviceProfile.from_dict(item) for item in raw)
