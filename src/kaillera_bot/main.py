"""Punto de entrada principal del bot."""

import argparse
import logging
import signal
import sys
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import yaml

from .emulator import EmulatorController
from .network import KailleraClient, ServerScanner
from .recorders import InputRecorder, NetworkRecorder, VideoRecorder


class KailleraBot:
    """Bot principal para grabar partidas de Kaillera."""

    def __init__(self, config_path: Path):
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        self.running = False

        self.emulator: Optional[EmulatorController] = None
        self.scanner: Optional[ServerScanner] = None
        self.client: Optional[KailleraClient] = None

        self.video_recorder: Optional[VideoRecorder] = None
        self.input_recorder: Optional[InputRecorder] = None
        self.network_recorder: Optional[NetworkRecorder] = None

        self.current_session: Optional[str] = None

    def _load_config(self, config_path: Path) -> dict:
        """Carga la configuración desde archivo YAML."""
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def _setup_logging(self) -> logging.Logger:
        """Configura el sistema de logging."""
        log_config = self.config.get('logging', {})
        log_level = getattr(logging, log_config.get('level', 'INFO'))
        log_file = log_config.get('file', 'logs/kaillera_bot.log')

        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )

        return logging.getLogger(__name__)

    def start(self) -> None:
        """Inicia el bot."""
        self.logger.info("=== Iniciando Kaillera Bot ===")
        self.running = True

        self._setup_signal_handlers()
        self._initialize_components()
        self._start_automation()

        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Interrupción recibida")
        finally:
            self.stop()

    def stop(self) -> None:
        """Detiene el bot."""
        self.logger.info("Deteniendo Kaillera Bot...")
        self.running = False

        if self.scanner:
            self.scanner.stop_continuous_scan()

        self._stop_recording()

        if self.client and self.client.is_connected():
            self.client.disconnect()

        if self.emulator and self.emulator.is_running():
            self.emulator.stop_emulator()

        self.logger.info("Kaillera Bot detenido")

    def _setup_signal_handlers(self) -> None:
        """Configura manejadores de señales."""
        def signal_handler(signum, frame):
            self.logger.info(f"Señal {signum} recibida")
            self.stop()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def _initialize_components(self) -> None:
        """Inicializa todos los componentes del bot."""
        self.logger.info("Inicializando componentes...")

        emu_config = self.config['emulator']
        self.emulator = EmulatorController(
            executable_path=emu_config['executable_path'],
            roms_directory=emu_config['roms_directory'],
            startup_delay=emu_config.get('startup_delay', 5)
        )

        self.scanner = ServerScanner()
        self.scanner.on_game_found = self._on_game_found

        self.client = KailleraClient(username="KailleraBot")
        self.client.on_game_start = self._on_game_start
        self.client.on_player_join = self._on_player_join
        self.client.on_player_leave = self._on_player_leave

        output_dir = Path(self.config['recording']['output_directory'])
        self.video_recorder = VideoRecorder(
            output_dir=output_dir / "videos",
            fps=self.config['recording']['video'].get('fps', 60),
            codec=self.config['recording']['video'].get('codec', 'mp4v')
        )

        self.input_recorder = InputRecorder(
            output_dir=output_dir / "inputs",
            player_name="KailleraBot"
        )

        self.network_recorder = NetworkRecorder(
            output_dir=output_dir / "network"
        )

        self.logger.info("Componentes inicializados")

    def _start_automation(self) -> None:
        """Inicia la automatización."""
        automation_config = self.config['automation']

        if not automation_config.get('auto_join', True):
            self.logger.info("Modo manual activado")
            return

        if not self.scanner:
            self.logger.error("Scanner no inicializado")
            return

        self.logger.info("Iniciando automatización...")

        kaillera_config = self.config['kaillera']
        scan_interval = kaillera_config.get('scan_interval', 30)
        filters = kaillera_config.get('filters', {})

        self.scanner.start_continuous_scan(
            interval=scan_interval,
            game_filter=filters.get('games', []),
            min_players=filters.get('min_players', 2)
        )

    def _on_game_found(self, session) -> None:
        """Callback cuando se encuentra una partida."""
        self.logger.info(
            f"Partida encontrada: {session.game_name} "
            f"({len(session.players)}/{session.max_players} jugadores) "
            f"en {session.server.name}"
        )

        if not self.running or not self.config['automation'].get('auto_join', True):
            return

        if self.current_session:
            self.logger.info("Ya hay una sesión activa, ignorando")
            return

        self._join_game(session)

    def _join_game(self, session) -> None:
        """Se une a una partida."""
        if not self.emulator:
            self.logger.error("Emulador no inicializado")
            return

        if not self.client:
            self.logger.error("Cliente no inicializado")
            return

        self.logger.info(f"Uniéndose a partida: {session.game_name}")

        if not self.emulator.start_emulator():
            self.logger.error("No se pudo iniciar el emulador")
            return

        time.sleep(2)

        if not self.client.connect(session.server.address, session.server.port):
            self.logger.error("No se pudo conectar al servidor")
            return

        time.sleep(1)

        if not self.client.join_game(session.game_name):
            self.logger.error("No se pudo unir a la partida")
            return

        self.current_session = f"{session.game_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    def _on_game_start(self, game_name: str) -> None:
        """Callback cuando inicia una partida."""
        self.logger.info(f"Partida iniciada: {game_name}")

        if self.config['automation'].get('auto_record', True):
            self._start_recording(game_name)

    def _on_player_join(self, player_name: str, player_number: int) -> None:
        """Callback cuando un jugador se une."""
        self.logger.info(f"Jugador unido: {player_name} (#{player_number})")

        if self.network_recorder and self.network_recorder.recording:
            self.network_recorder.record_player_event(
                event_type='join',
                player_name=player_name,
                player_number=player_number
            )

    def _on_player_leave(self, player_name: str, player_number: int) -> None:
        """Callback cuando un jugador se va."""
        self.logger.info(f"Jugador salió: {player_name} (#{player_number})")

        if self.network_recorder and self.network_recorder.recording:
            self.network_recorder.record_player_event(
                event_type='leave',
                player_name=player_name,
                player_number=player_number
            )

    def _start_recording(self, game_name: str) -> None:
        """Inicia la grabación."""
        self.logger.info(f"Iniciando grabación de: {game_name}")

        recording_config = self.config['recording']

        if recording_config['video']['enabled'] and self.video_recorder and self.emulator:
            geometry = self.emulator.get_window_geometry()
            if geometry:
                self.video_recorder.set_capture_area(**geometry)
                self.video_recorder.start_recording(game_name)

        if recording_config['inputs']['enabled'] and self.input_recorder:
            self.input_recorder.start_recording()

        if recording_config['network']['enabled'] and self.network_recorder:
            self.network_recorder.start_recording()
            self.network_recorder.record_game_event(
                event_type='start',
                game_name=game_name
            )

        self.logger.info("Grabación iniciada")

    def _stop_recording(self) -> None:
        """Detiene la grabación."""
        self.logger.info("Deteniendo grabación...")

        if self.video_recorder and self.video_recorder.recording:
            self.video_recorder.stop_recording()

        if self.input_recorder and self.input_recorder.recording:
            self.input_recorder.stop_recording()

        if self.network_recorder and self.network_recorder.recording:
            self.network_recorder.stop_recording(self.current_session or "")

        self.current_session = None
        self.logger.info("Grabación detenida")


def main() -> None:
    """Función principal."""
    parser = argparse.ArgumentParser(
        description="Bot para grabar partidas de N64 desde servidores Kaillera"
    )
    parser.add_argument(
        '--config',
        type=Path,
        default=Path('config/settings.yaml'),
        help='Ruta al archivo de configuración'
    )
    parser.add_argument(
        '--version',
        action='version',
        version='%(prog)s 0.1.0'
    )

    args = parser.parse_args()

    if not args.config.exists():
        print(f"Error: Archivo de configuración no encontrado: {args.config}")
        print("Por favor, crea un archivo de configuración en config/settings.yaml")
        sys.exit(1)

    bot = KailleraBot(args.config)
    bot.start()


if __name__ == '__main__':
    main()
