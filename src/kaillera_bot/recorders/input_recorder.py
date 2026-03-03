"""Grabador de inputs del juego."""

import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pynput import keyboard, mouse


class InputRecorder:
    """Graba inputs de teclado y mouse durante una partida."""

    def __init__(self, output_dir: Path, player_name: str = "Player1"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.player_name = player_name
        self.logger = logging.getLogger(__name__)

        self.inputs: List[Dict[str, Any]] = []
        self.start_time: float = 0.0
        self.recording = False

        self.keyboard_listener: Optional[keyboard.Listener] = None
        self.mouse_listener: Optional[mouse.Listener] = None

    def start_recording(self) -> None:
        """Inicia la grabación de inputs."""
        if self.recording:
            self.logger.warning("La grabación ya está en curso")
            return

        self.inputs = []
        self.start_time = time.time()
        self.recording = True

        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.mouse_listener = mouse.Listener(
            on_click=self._on_mouse_click,
            on_scroll=self._on_mouse_scroll
        )

        self.keyboard_listener.start()
        self.mouse_listener.start()

        self.logger.info(f"Grabación de inputs iniciada para {self.player_name}")

    def stop_recording(self) -> Path:
        """Detiene la grabación y guarda los inputs."""
        if not self.recording:
            self.logger.warning("No hay grabación en curso")
            return Path("")

        self.recording = False

        if self.keyboard_listener:
            self.keyboard_listener.stop()
        if self.mouse_listener:
            self.mouse_listener.stop()

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"inputs_{self.player_name}_{timestamp}.json"
        output_path = self.output_dir / filename

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump({
                'player': self.player_name,
                'start_time': datetime.fromtimestamp(self.start_time).isoformat(),
                'duration': time.time() - self.start_time,
                'inputs': self.inputs
            }, f, indent=2, ensure_ascii=False)

        self.logger.info(f"Inputs guardados en {output_path}")
        return output_path

    def _on_key_press(self, key: Any) -> None:
        """Callback para tecla presionada."""
        if not self.recording:
            return

        try:
            key_name = key.char if hasattr(key, 'char') and key.char else str(key)
            self.inputs.append({
                'type': 'keyboard',
                'action': 'press',
                'key': key_name,
                'timestamp': time.time() - self.start_time
            })
        except Exception as e:
            self.logger.error(f"Error registrando tecla: {e}")

    def _on_key_release(self, key: Any) -> None:
        """Callback para tecla liberada."""
        if not self.recording:
            return

        try:
            key_name = key.char if hasattr(key, 'char') and key.char else str(key)
            self.inputs.append({
                'type': 'keyboard',
                'action': 'release',
                'key': key_name,
                'timestamp': time.time() - self.start_time
            })
        except Exception as e:
            self.logger.error(f"Error registrando tecla: {e}")

    def _on_mouse_click(self, x: int, y: int, button: Any, pressed: bool) -> None:
        """Callback para click de mouse."""
        if not self.recording:
            return

        self.inputs.append({
            'type': 'mouse',
            'action': 'click' if pressed else 'release',
            'button': str(button),
            'x': x,
            'y': y,
            'timestamp': time.time() - self.start_time
        })

    def _on_mouse_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        """Callback para scroll de mouse."""
        if not self.recording:
            return

        self.inputs.append({
            'type': 'mouse',
            'action': 'scroll',
            'dx': dx,
            'dy': dy,
            'x': x,
            'y': y,
            'timestamp': time.time() - self.start_time
        })

    def get_input_count(self) -> int:
        """Retorna el número de inputs registrados."""
        return len(self.inputs)
