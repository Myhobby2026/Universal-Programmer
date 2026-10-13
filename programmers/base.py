"""Contracts and capability gates for hardware operations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from core.models import DeviceProfile, FirmwareInfo, OperationReport, SupportLevel


class CapabilityError(RuntimeError):
    pass


@dataclass(slots=True)
class ProgrammerContext:
    firmware: FirmwareInfo
    profile: DeviceProfile | None = None


def require_operation(context: ProgrammerContext, operation: str) -> None:
    if not context.firmware.connected:
        raise CapabilityError("Teensy hardware is not connected")
    if context.profile is None:
        raise CapabilityError("select a target profile before starting an operation")
    if context.profile.support_level in (SupportLevel.PROFILE_ONLY, SupportLevel.UNSUPPORTED):
        raise CapabilityError(f"{context.profile.part_number} has no validated programming algorithm")
    if operation not in context.profile.operations:
        raise CapabilityError(f"operation {operation!r} is not supported by {context.profile.part_number}")
    if context.profile.interface.value.lower() not in {cap.casefold() for cap in context.firmware.capabilities}:
        raise CapabilityError(f"firmware does not advertise the {context.profile.interface.value} interface")


class Programmer:
    def __init__(self, context: ProgrammerContext):
        self.context = context

    def execute(self, operation: str, action: Callable[[], int]) -> OperationReport:
        require_operation(self.context, operation)
        try:
            transferred = action()
        except Exception as exc:
            return OperationReport(operation, False, str(exc), errors=[str(exc)])
        return OperationReport(operation, True, f"{operation.capitalize()} completed", bytes_transferred=transferred)
