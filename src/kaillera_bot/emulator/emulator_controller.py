"""Controlador del emulador RMG Kaillera Edition."""

import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pyautogui


class EmulatorController:
    """Controla el emulador RMG Kaillera Edition."""

    def __init__(
        self,
        executable_path: str,
        roms_directory: str,
        startup_delay: int = 5
    ):
        self.executable_path = Path(executable_path)
        self.roms_directory = Path(roms_directory)
        self.startup_delay = startup_delay
        self.logger = logging.getLogger(__name__)

        self.process: Optional[subprocess.Popen] = None
        self.running = False
        self.current_rom: Optional[str] = None

        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 0.1

    def is_executable_valid(self) -> bool:
        """Verifica si el ejecutable existe."""
        return self.executable_path.exists() and self.executable_path.is_file()

    def is_roms_directory_valid(self) -> bool:
        """Verifica si el directorio de ROMs existe."""
        return self.roms_directory.exists() and self.roms_directory.is_dir()

    def start_emulator(self) -> bool:
        """Inicia el emulador."""
        if self.running:
            self.logger.warning("El emulador ya está en ejecución")
            return True

        if not self.is_executable_valid():
            self.logger.error(f"Ejecutable no encontrado: {self.executable_path}")
            return False

        try:
            self.process = subprocess.Popen(
                [str(self.executable_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            time.sleep(self.startup_delay)

            if self.process.poll() is not None:
                self.logger.error("El emulador se cerró inmediatamente")
                return False

            self.running = True
            self.logger.info(f"Emulador iniciado: {self.executable_path}")
            return True

        except Exception as e:
            self.logger.error(f"Error iniciando emulador: {e}")
            return False

    def stop_emulator(self) -> None:
        """Detiene el emulador."""
        if not self.running or not self.process:
            return

        try:
            self.process.terminate()
            self.process.wait(timeout=10)

        except subprocess.TimeoutExpired:
            self.logger.warning("Emulador no respondió, forzando cierre")
            self.process.kill()

        except Exception as e:
            self.logger.error(f"Error deteniendo emulador: {e}")

        finally:
            self.running = False
            self.process = None
            self.current_rom = None
            self.logger.info("Emulador detenido")

    def load_rom(self, rom_name: str) -> bool:
        """Carga una ROM en el emulador."""
        if not self.running:
            self.logger.error("El emulador no está en ejecución")
            return False

        rom_path = self.roms_directory / rom_name
        if not rom_path.exists():
            self.logger.error(f"ROM no encontrada: {rom_path}")
            return False

        try:
            self._open_file_dialog()
            time.sleep(0.5)
            self._type_path(str(rom_path))
            time.sleep(0.3)
            self._press_enter()

            self.current_rom = rom_name
            self.logger.info(f"ROM cargada: {rom_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error cargando ROM: {e}")
            return False

    def connect_to_kaillera(self, server_address: str, username: str = "KailleraBot") -> bool:
        """Conecta a un servidor Kaillera desde el emulador."""
        if not self.running:
            self.logger.error("El emulador no está en ejecución")
            return False

        try:
            self._open_kaillera_menu()
            time.sleep(0.5)
            self._enter_server_address(server_address)
            time.sleep(0.3)
            self._enter_username(username)
            time.sleep(0.3)
            self._press_connect()

            self.logger.info(f"Conectando a Kaillera: {server_address}")
            return True

        except Exception as e:
            self.logger.error(f"Error conectando a Kaillera: {e}")
            return False

    def join_game(self, game_name: str) -> bool:
        """Se une a una partida en Kaillera."""
        if not self.running:
            self.logger.error("El emulador no está en ejecución")
            return False

        try:
            self._select_game_from_list(game_name)
            time.sleep(0.3)
            self._press_join()

            self.logger.info(f"Uniéndose a partida: {game_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error uniéndose a partida: {e}")
            return False

    def start_game(self) -> bool:
        """Inicia la partida."""
        if not self.running:
            self.logger.error("El emulador no está en ejecución")
            return False

        try:
            self._press_start()
            self.logger.info("Partida iniciada")
            return True

        except Exception as e:
            self.logger.error(f"Error iniciando partida: {e}")
            return False

    def set_window_focus(self) -> bool:
        """Pone el foco en la ventana del emulador."""
        try:
            windows = pyautogui.getWindowsWithTitle("Rosalie's Mupen GUI")  # type: ignore
            if windows:
                window = windows[0]
                if window.isMinimized:
                    window.restore()
                window.activate()
                time.sleep(0.2)
                return True
            return False

        except AttributeError:
            self.logger.warning("pyautogui.getWindowsWithTitle no disponible en esta plataforma")
            return False
        except Exception as e:
            self.logger.error(f"Error poniendo foco en ventana: {e}")
            return False

    def get_window_geometry(self) -> Optional[Dict[str, int]]:
        """Obtiene la geometría de la ventana del emulador."""
        try:
            windows = pyautogui.getWindowsWithTitle("Rosalie's Mupen GUI")  # type: ignore
            if windows:
                window = windows[0]
                return {
                    'left': window.left,
                    'top': window.top,
                    'width': window.width,
                    'height': window.height
                }
            return None

        except AttributeError:
            self.logger.warning("pyautogui.getWindowsWithTitle no disponible en esta plataforma")
            return None
        except Exception as e:
            self.logger.error(f"Error obteniendo geometría de ventana: {e}")
            return None

    def _open_file_dialog(self) -> None:
        """Abre el diálogo de archivo (Ctrl+O)."""
        self.set_window_focus()
        pyautogui.hotkey('ctrl', 'o')

    def _type_path(self, path: str) -> None:
        """Escribe una ruta."""
        pyautogui.write(path, interval=0.05)

    def _press_enter(self) -> None:
        """Presiona Enter."""
        pyautogui.press('enter')

    def _open_kaillera_menu(self) -> None:
        """Abre el menú de Kaillera."""
        self.set_window_focus()
        pyautogui.hotkey('ctrl', 'k')

    def _enter_server_address(self, address: str) -> None:
        """Escribe la dirección del servidor."""
        pyautogui.write(address, interval=0.05)

    def _enter_username(self, username: str) -> None:
        """Escribe el nombre de usuario."""
        pyautogui.press('tab')
        pyautogui.write(username, interval=0.05)

    def _press_connect(self) -> None:
        """Presiona el botón de conectar."""
        pyautogui.press('tab')
        pyautogui.press('enter')

    def _select_game_from_list(self, game_name: str) -> None:
        """Selecciona un juego de la lista."""
        pyautogui.press('tab')
        search_keys = list(game_name.lower())
        for key in search_keys:
            pyautogui.press(key)

    def _press_join(self) -> None:
        """Presiona el botón de unirse."""
        pyautogui.press('tab')
        pyautogui.press('enter')

    def _press_start(self) -> None:
        """Presiona Start para iniciar el juego."""
        pyautogui.press('f5')

    def is_running(self) -> bool:
        """Verifica si el emulador está en ejecución."""
        return self.running and (self.process is not None and self.process.poll() is None)

    def get_current_rom(self) -> Optional[str]:
        """Retorna la ROM actualmente cargada."""
        return self.current_rom
