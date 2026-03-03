"""Grabador de video de la partida."""

import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple

import cv2
import mss
import numpy as np


class VideoRecorder:
    """Graba video de la ventana del emulador."""

    def __init__(
        self,
        output_dir: Path,
        fps: int = 60,
        codec: str = "mp4v",
        quality: str = "high"
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.fps = fps
        self.codec = codec
        self.quality = quality
        self.logger = logging.getLogger(__name__)

        self.recording = False
        self.writer: Optional[cv2.VideoWriter] = None
        self.capture_area: Optional[dict] = None
        self.sct = mss.mss()
        self.start_time: Optional[float] = None

    def set_capture_area(
        self,
        left: int,
        top: int,
        width: int,
        height: int
    ) -> None:
        """Define el área de captura de video."""
        self.capture_area = {
            'left': left,
            'top': top,
            'width': width,
            'height': height
        }
        self.logger.info(
            f"Área de captura configurada: {width}x{height} en ({left}, {top})"
        )

    def auto_detect_emulator_window(self, window_title: str = "Rosalie's Mupen GUI") -> bool:
        """Detecta automáticamente la ventana del emulador."""
        try:
            import pyautogui
            
            windows = pyautogui.getWindowsWithTitle(window_title)  # type: ignore
            if not windows:
                self.logger.error(f"No se encontró ventana con título: {window_title}")
                return False

            window = windows[0]
            if window.isMinimized:
                window.restore()
                time.sleep(0.5)

            self.set_capture_area(
                left=window.left,
                top=window.top,
                width=window.width,
                height=window.height
            )
            return True

        except AttributeError:
            self.logger.warning("pyautogui.getWindowsWithTitle no disponible en esta plataforma")
            return False
        except Exception as e:
            self.logger.error(f"Error detectando ventana del emulador: {e}")
            return False

    def start_recording(self, game_name: str = "game") -> Path:
        """Inicia la grabación de video."""
        if self.recording:
            self.logger.warning("La grabación ya está en curso")
            return Path("")

        if not self.capture_area:
            self.logger.error("Área de captura no configurada")
            raise ValueError("Debe configurar el área de captura primero")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{game_name}_{timestamp}.mp4"
        output_path = self.output_dir / filename

        fourcc = cv2.VideoWriter_fourcc(*self.codec)
        
        quality_map = {
            'low': 30,
            'medium': 50,
            'high': 100
        }
        
        self.writer = cv2.VideoWriter(
            str(output_path),
            fourcc,
            self.fps,
            (self.capture_area['width'], self.capture_area['height'])
        )

        if self.writer is None or not self.writer.isOpened():
            self.logger.error("No se pudo inicializar el VideoWriter")
            raise RuntimeError("Error inicializando VideoWriter")

        self.recording = True
        self.start_time = time.time()
        self.logger.info(f"Grabación de video iniciada: {output_path}")
        
        return output_path

    def capture_frame(self) -> None:
        """Captura un frame y lo añade al video."""
        if not self.recording or not self.writer or not self.capture_area:
            return

        try:
            screenshot = self.sct.grab(self.capture_area)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            
            self.writer.write(frame)

        except Exception as e:
            self.logger.error(f"Error capturando frame: {e}")

    def stop_recording(self) -> Path:
        """Detiene la grabación y guarda el video."""
        if not self.recording:
            self.logger.warning("No hay grabación en curso")
            return Path("")

        self.recording = False

        if self.writer:
            output_path = Path(self.writer.getBackendName())
            self.writer.release()
            self.writer = None

        duration = time.time() - self.start_time if self.start_time else 0
        self.logger.info(f"Grabación detenida. Duración: {duration:.2f} segundos")
        
        return Path("")

    def get_recording_duration(self) -> float:
        """Retorna la duración actual de la grabación en segundos."""
        if not self.start_time:
            return 0.0
        return time.time() - self.start_time
