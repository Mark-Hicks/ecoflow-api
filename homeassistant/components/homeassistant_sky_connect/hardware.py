"""The Home Assistant SkyConnect hardware platform."""

from __future__ import annotations

from homeassistant.components.hardware.models import HardwareInfo, USBInfo
from homeassistant.core import HomeAssistant, callback

from .const import DOMAIN

DOCUMENTATION_URL = "https://skyconnect.home-assistant.io/documentation/"
DONGLE_NAME = "Home Assistant SkyConnect"


@callback
def async_info(hass: HomeAssistant) -> list[HardwareInfo]:
    """Return board info."""
    entries = hass.config_entries.async_entries(DOMAIN)

    return [
        HardwareInfo(
            board=None,
            config_entries=[entry.entry_id],
            dongle=USBInfo(
                vid=entry.data["vid"],
                pid=entry.data["pid"],
                serial_number=entry.data["serial_number"],
                manufacturer=entry.data["manufacturer"],
                description=entry.data["description"],
            ),
            name=DONGLE_NAME,
            url=DOCUMENTATION_URL,
        )
        for entry in entries
    ]
