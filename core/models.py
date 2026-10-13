from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SupportLevel(str, Enum):
    TESTED = "Implemented and tested on hardware"
    IMPLEMENTED = "Implemented but not hardware-verified"
    PROFILE_ONLY = "Profile available; programming algorithm incomplete"
    UNSUPPORTED = "Unsupported"


class InterfaceType(str, Enum):
    SWD = "SWD"
    JTAG = "JTAG"
    UART = "UART"
    SPI = "SPI"
    I2C = "I²C"
    NAND = "Parallel NAND"


@dataclass(slots=True)
class DeviceProfile:
    manufacturer: str
    family: str
    part_number: str
    category: str
    interface: InterfaceType
    capacity_bytes: int | None = None
    address_width: int | None = None
    page_size: int | None = None
    erase_size: int | None = None
    voltage_min: float | None = None
    voltage_max: float | None = None
    pins: dict[str, str] = field(default_factory=dict)
    identification: str = ""
    algorithm: str = ""
    operations: list[str] = field(default_factory=list)
    datasheet_url: str = ""
    support_level: SupportLevel = SupportLevel.PROFILE_ONLY
    validation_notes: str = ""
    capabilities: set[str] = field(default_factory=set)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "DeviceProfile":
        return cls(
            manufacturer=str(value["manufacturer"]), family=str(value["family"]),
            part_number=str(value["part_number"]), category=str(value["category"]),
            interface=InterfaceType(value["interface"]),
            capacity_bytes=value.get("capacity_bytes"), address_width=value.get("address_width"),
            page_size=value.get("page_size"), erase_size=value.get("erase_size"),
            voltage_min=value.get("voltage_min"), voltage_max=value.get("voltage_max"),
            pins=dict(value.get("pins", {})), identification=str(value.get("identification", "")),
            algorithm=str(value.get("algorithm", "")), operations=list(value.get("operations", [])),
            datasheet_url=str(value.get("datasheet_url", "")),
            support_level=SupportLevel(value.get("support_level", SupportLevel.UNSUPPORTED.value)),
            validation_notes=str(value.get("validation_notes", "")),
            capabilities=set(value.get("capabilities", [])),
        )

    def validate(self) -> list[str]:
        errors: list[str] = []
        if not self.manufacturer or not self.part_number:
            errors.append("manufacturer and part_number are required")
        if self.capacity_bytes is not None and self.capacity_bytes <= 0:
            errors.append("capacity_bytes must be positive")
        if self.page_size is not None and self.page_size <= 0:
            errors.append("page_size must be positive")
        if self.voltage_min is not None and self.voltage_max is not None and self.voltage_min > self.voltage_max:
            errors.append("voltage_min cannot exceed voltage_max")
        if not self.operations and self.support_level != SupportLevel.UNSUPPORTED:
            errors.append("supported profiles must declare operations")
        if self.support_level == SupportLevel.TESTED and "hardware-verified" not in self.validation_notes.lower():
            errors.append("tested profiles must include a hardware-verification note")
        return errors


@dataclass(slots=True)
class FirmwareInfo:
    firmware_version: str = "unknown"
    protocol_version: int = 0
    capabilities: set[str] = field(default_factory=set)
    board: str = "unknown"
    connected: bool = False


@dataclass(slots=True)
class OperationReport:
    operation: str
    success: bool
    message: str
    bytes_transferred: int = 0
    elapsed_seconds: float = 0.0
    errors: list[str] = field(default_factory=list)
