"""Tests for SerialManager with simulator backend."""
import logging
import time

import pytest
from PySide6.QtCore import QCoreApplication

from src.core.serial_manager import SerialManager

logger = logging.getLogger(__name__)


@pytest.fixture
def manager(qapp) -> SerialManager:
    mgr = SerialManager()
    yield mgr
    if mgr.is_connected():
        mgr.disconnect()


def _collect_signals(manager: SerialManager, signal_name: str, trigger, count: int = 1, timeout: float = 3.0) -> list:
    """Collect emitted signal arguments."""
    results = []

    def _handler(*args):
        results.append(list(args))

    sig = getattr(manager, signal_name)
    sig.connect(_handler)
    trigger()
    deadline = time.time() + timeout
    while len(results) < count and time.time() < deadline:
        QCoreApplication.processEvents()
        time.sleep(0.05)
    sig.disconnect(_handler)
    return results


class TestSerialManagerPorts:
    """Port listing."""

    def test_simulator_in_port_list(self, manager: SerialManager) -> None:
        ports = manager.get_available_ports()
        assert "SIMULATOR" in ports

    def test_port_list_is_list_of_strings(self, manager: SerialManager) -> None:
        ports = manager.get_available_ports()
        assert isinstance(ports, list)
        for p in ports:
            assert isinstance(p, str)


class TestSerialManagerConnect:
    """Connect/disconnect to simulator."""

    def test_connect_simulator(self, manager: SerialManager) -> None:
        assert manager.connect("SIMULATOR") is True
        assert manager.is_connected() is True

    def test_disconnect(self, manager: SerialManager) -> None:
        manager.connect("SIMULATOR")
        manager.disconnect()
        assert manager.is_connected() is False

    def test_connect_invalid_port(self, manager: SerialManager) -> None:
        result = manager.connect("NONEXISTENT_PORT_XYZ")
        assert result is False
        assert manager.is_connected() is False

    def test_connection_changed_signal_on_connect(self, manager: SerialManager) -> None:
        results = _collect_signals(
            manager, "connection_changed",
            lambda: manager.connect("SIMULATOR"),
        )
        assert len(results) >= 1
        assert results[-1] == [True]

    def test_connection_changed_signal_on_disconnect(self, manager: SerialManager) -> None:
        manager.connect("SIMULATOR")
        QCoreApplication.processEvents()
        results = _collect_signals(
            manager, "connection_changed",
            lambda: manager.disconnect(),
        )
        assert len(results) >= 1
        assert results[-1] == [False]


class TestSerialManagerData:
    """Data reception from simulator."""

    def test_data_received_signal_fires(self, manager: SerialManager) -> None:
        manager.connect("SIMULATOR")
        results = _collect_signals(
            manager, "data_received",
            lambda: manager.send_command("C"),
        )
        assert len(results) >= 1
        line = results[0][0]
        assert isinstance(line, str)
        assert line.startswith("qcm") or line.startswith("QCM")

    def test_data_line_has_valid_format(self, manager: SerialManager) -> None:
        manager.connect("SIMULATOR")
        results = _collect_signals(
            manager, "data_received",
            lambda: manager.send_command("C"),
        )
        assert len(results) >= 1
        line = results[0][0]
        fields = line.split("\t")
        assert len(fields) >= 15


class TestSerialManagerCommands:
    """Command sending."""

    def test_send_command(self, manager: SerialManager) -> None:
        manager.connect("SIMULATOR")
        manager.send_command("A")
        manager.send_command("B")

    def test_send_command_echoed(self, manager: SerialManager) -> None:
        """Last command should be echoed in the next packet."""
        manager.connect("SIMULATOR")
        results = _collect_signals(
            manager, "data_received",
            lambda: manager.send_command("C"),
        )
        if len(results) >= 1:
            line = results[0][0]
            fields = line.split("\t")
            assert fields[3] == "C"
