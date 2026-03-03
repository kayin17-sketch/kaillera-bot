"""Grabador de datos de red."""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class NetworkRecorder:
    """Graba paquetes y datos de red de la sesión Kaillera."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

        self.packets: List[Dict[str, Any]] = []
        self.recording = False
        self.start_time: float = 0.0

    def start_recording(self) -> None:
        """Inicia la grabación de datos de red."""
        if self.recording:
            self.logger.warning("La grabación ya está en curso")
            return

        self.packets = []
        self.start_time = time.time()
        self.recording = True

        self.logger.info("Grabación de datos de red iniciada")

    def record_packet(
        self,
        packet_type: str,
        source: str,
        destination: str,
        data: Any,
        size: int = 0
    ) -> None:
        """Registra un paquete de red."""
        if not self.recording:
            return

        packet = {
            'type': packet_type,
            'source': source,
            'destination': destination,
            'data': data,
            'size': size,
            'timestamp': time.time() - self.start_time,
            'datetime': datetime.now().isoformat()
        }

        self.packets.append(packet)

    def record_player_event(
        self,
        event_type: str,
        player_name: str,
        player_number: int,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Registra un evento relacionado con jugadores."""
        if not self.recording:
            return

        event = {
            'type': 'player_event',
            'event_type': event_type,
            'player_name': player_name,
            'player_number': player_number,
            'data': data or {},
            'timestamp': time.time() - self.start_time,
            'datetime': datetime.now().isoformat()
        }

        self.packets.append(event)
        self.logger.info(f"Evento de jugador: {event_type} - {player_name}")

    def record_game_event(
        self,
        event_type: str,
        game_name: str,
        data: Optional[Dict[str, Any]] = None
    ) -> None:
        """Registra un evento relacionado con el juego."""
        if not self.recording:
            return

        event = {
            'type': 'game_event',
            'event_type': event_type,
            'game_name': game_name,
            'data': data or {},
            'timestamp': time.time() - self.start_time,
            'datetime': datetime.now().isoformat()
        }

        self.packets.append(event)
        self.logger.info(f"Evento de juego: {event_type} - {game_name}")

    def stop_recording(self, session_id: str = "") -> Path:
        """Detiene la grabación y guarda los datos."""
        if not self.recording:
            self.logger.warning("No hay grabación en curso")
            return Path("")

        self.recording = False

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        session_suffix = f"_{session_id}" if session_id else ""
        filename = f"network_data{session_suffix}_{timestamp}.json"
        output_path = self.output_dir / filename

        summary = {
            'session_id': session_id,
            'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
            'duration': time.time() - self.start_time,
            'total_packets': len(self.packets),
            'packet_types': self._count_packet_types(),
            'packets': self.packets
        }

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Datos de red guardados en {output_path}")
        return output_path

    def _count_packet_types(self) -> Dict[str, int]:
        """Cuenta los tipos de paquetes."""
        counts: Dict[str, int] = {}
        for packet in self.packets:
            packet_type = packet.get('type', 'unknown')
            counts[packet_type] = counts.get(packet_type, 0) + 1
        return counts

    def get_packet_count(self) -> int:
        """Retorna el número de paquetes registrados."""
        return len(self.packets)

    def get_recording_duration(self) -> float:
        """Retorna la duración actual de la grabación en segundos."""
        if self.start_time == 0.0:
            return 0.0
        return time.time() - self.start_time
