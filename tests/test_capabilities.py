import pytest

from core.models import DeviceProfile, FirmwareInfo, InterfaceType, SupportLevel
from devices import DeviceCatalog
from programmers import CapabilityError, ProgrammerContext, require_operation


def test_catalog_profiles_are_explicitly_gated():
    profile = DeviceCatalog().get("W25Q128JV")
    assert profile is not None
    assert profile.support_level == SupportLevel.PROFILE_ONLY
    with pytest.raises(CapabilityError, match="algorithm"):
        require_operation(ProgrammerContext(FirmwareInfo(connected=True, capabilities={"SPI"}), profile), "program")


def test_profile_validation_rejects_tested_without_note():
    profile = DeviceProfile("A", "B", "C", "D", InterfaceType.SPI, operations=["identify"], support_level=SupportLevel.TESTED)
    assert any("hardware-verification" in error for error in profile.validate())
