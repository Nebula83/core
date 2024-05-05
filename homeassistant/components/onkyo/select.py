"""Support for Onkyo Receivers."""

from __future__ import annotations

import logging

import eiscp

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import OPTION_EISCP
from .entity import OnkyoEntity
from .helpers import onkyo_command, parse_onkyo_payload

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Onkyo Platform from config_flow."""

    commands: list[EiscpCommandEntity] = []

    host = entry.data[CONF_HOST]
    try:
        receiver = eiscp.eISCP(host)

        if OPTION_EISCP in entry.options:
            commands = [
                EiscpCommandEntity(
                    entry,
                    receiver,
                    command,
                    entry.options[OPTION_EISCP][command],
                )
                for command in entry.options[OPTION_EISCP]
            ]
    except OSError:
        _LOGGER.error("Unable to connect to receiver at %s", host)
        raise

    entity_registry = er.async_get(hass)
    all_entities = entity_registry.entities.get_entries_for_config_entry_id(
        entry.entry_id
    )
    current_ids = [
        entity.unique_id
        for entity in all_entities
        if entity.entity_id.startswith("select.")
    ]
    configured_ids = [command.unique_id for command in commands]

    for removed_id in set(current_ids) - set(configured_ids):
        entity_id = entity_registry.async_get_entity_id(
            Platform.SELECT, "onkyo", removed_id
        )
        if entity_id is not None:
            entity_registry.async_remove(entity_id)

    async_add_entities(commands, update_before_add=True)


class EiscpCommandEntity(OnkyoEntity, SelectEntity):
    """Representation of an Onkyo eiscp command."""

    _attr_has_entity_name = True
    _attr_current_option = ""

    def __init__(
        self,
        entry: ConfigEntry,
        receiver: eiscp.eISCP,
        command: str,
        options: list[str],
    ) -> None:
        """Initialize the Onkyo Receiver."""
        super().__init__(entry.data)

        self._command = command
        self._receiver = receiver
        self._entry_id = entry.entry_id
        self._attr_options = options

        self._attr_unique_id = f"{self._attr_unique_id}_{command}"

    @property
    def name(self):
        """Name of the entity."""
        return self._command

    def update(self) -> None:
        """Get the latest state from the device."""
        response_raw = self._receiver.command(f"{self._command} query")
        response = parse_onkyo_payload(response_raw)
        self._attr_current_option = response[0]

    def select_option(self, option: str) -> None:
        """Change the selected option."""
        onkyo_command(self._receiver, f"{self._command} {option}")
