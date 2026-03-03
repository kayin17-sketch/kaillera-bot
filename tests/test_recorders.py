"""Tests de ejemplo para Kaillera Bot."""

import pytest
from pathlib import Path
from src.kaillera_bot.recorders import InputRecorder, NetworkRecorder


def test_input_recorder_init():
    """Test de inicialización del grabador de inputs."""
    recorder = InputRecorder(Path("/tmp/test_inputs"))
    assert recorder.player_name == "Player1"
    assert not recorder.recording
    assert recorder.get_input_count() == 0


def test_network_recorder_init():
    """Test de inicialización del grabador de red."""
    recorder = NetworkRecorder(Path("/tmp/test_network"))
    assert not recorder.recording
    assert recorder.get_packet_count() == 0


def test_network_recorder_start_stop():
    """Test de inicio y parada de grabación de red."""
    recorder = NetworkRecorder(Path("/tmp/test_network"))
    
    recorder.start_recording()
    assert recorder.recording
    
    recorder.record_packet(
        packet_type="test",
        source="127.0.0.1",
        destination="127.0.0.1",
        data={"test": "data"}
    )
    assert recorder.get_packet_count() == 1
    
    output_path = recorder.stop_recording("test_session")
    assert not recorder.recording
    assert output_path.exists()
