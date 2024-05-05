"""Helper functions for onkyo communication."""

import logging

import eiscp

_LOGGER = logging.getLogger(__name__)


def parse_onkyo_payload(payload):
    """Parse a payload returned from the eiscp library."""
    if isinstance(payload, bool):
        # command not supported by the device
        return False

    if len(payload) < 2:
        # no value
        return None

    if isinstance(payload[1], str):
        return payload[1].split(",")

    return payload[1]


def onkyo_command(receiver: eiscp.eISCP, command: str):
    """Run an eiscp command and catch connection errors."""
    try:
        result = receiver.command(command)
    except (ValueError, OSError, AttributeError, AssertionError):
        if receiver.command_socket:
            receiver.command_socket = None
            _LOGGER.debug("Resetting connection")
        else:
            _LOGGER.info("Receiver is disconnected. Attempting to reconnect")
        return False
    _LOGGER.debug("Result for %s: %s", command, result)
    return result
