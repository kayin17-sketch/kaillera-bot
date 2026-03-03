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
        
        self.recording_start_time: float = 0.0
        self.last_game_data_time: float = 0.0
        self.active_players_count: int = 0
        self.monitoring_thread: Optional[threading.Thread] = None
        self.session_lock = threading.Lock()

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

        try:
            self._setup_signal_handlers()
        except ValueError:
            self.logger.debug("Signal handlers no disponibles en este thread")
        
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

        kaillera_config = self.config['kaillera']
        configured_servers = kaillera_config.get('servers', [])
        
        self.scanner = ServerScanner(configured_servers=configured_servers)
        self.scanner.on_game_found = self._on_game_found

        self.client = KailleraClient(username="KailleraBot")
        self.client.on_game_start = self._on_game_start
        self.client.on_player_join = self._on_player_join
        self.client.on_player_leave = self._on_player_leave
        self.client.on_game_data = self._on_game_data_received

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

        configured_servers = kaillera_config.get('servers', [])
        if configured_servers and self.client:
            first_server = configured_servers[0]
            self.logger.info(f"Conectando a servidor configurado: {first_server.get('name')}")
            
            if self.client.connect(
                first_server.get('address'),
                first_server.get('port', 27888)
            ):
                self.logger.info("Conectado al servidor exitosamente")
            else:
                self.logger.warning("No se pudo conectar al servidor")

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
        
        with self.session_lock:
            self.active_players_count += 1

        if self.network_recorder and self.network_recorder.recording:
            self.network_recorder.record_player_event(
                event_type='join',
                player_name=player_name,
                player_number=player_number
            )

    def _on_player_leave(self, player_name: str, player_number: int) -> None:
        """Callback cuando un jugador se va."""
        self.logger.info(f"Jugador salió: {player_name} (#{player_number})")
        
        with self.session_lock:
            self.active_players_count = max(0, self.active_players_count - 1)

        if self.network_recorder and self.network_recorder.recording:
            self.network_recorder.record_player_event(
                event_type='leave',
                player_name=player_name,
                player_number=player_number
            )
    
    def _on_game_data_received(self, data: bytes) -> None:
        """Callback cuando se reciben datos del juego."""
        with self.session_lock:
            self.last_game_data_time = time.time()

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
        
        with self.session_lock:
            self.active_players_count = 1
        
        self._start_game_monitoring()
        self.logger.info("Grabación iniciada")

    def _stop_recording(self) -> None:
        """Detiene la grabación."""
        self.logger.info("Deteniendo grabación...")
        
        self._stop_game_monitoring()

        if self.video_recorder and self.video_recorder.recording:
            self.video_recorder.stop_recording()

        if self.input_recorder and self.input_recorder.recording:
            self.input_recorder.stop_recording()

        if self.network_recorder and self.network_recorder.recording:
            self.network_recorder.stop_recording(self.current_session or "")

        self._cleanup_session()
        self.logger.info("Grabación detenida")

    def _start_game_monitoring(self) -> None:
        """Inicia el thread de monitoreo de la partida."""
        self.recording_start_time = time.time()
        self.last_game_data_time = time.time()
        
        self.monitoring_thread = threading.Thread(target=self._monitor_game_loop, daemon=True)
        self.monitoring_thread.start()
        self.logger.info("Monitoreo de partida iniciado")

    def _stop_game_monitoring(self) -> None:
        """Detiene el thread de monitoreo."""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            self.monitoring_thread.join(timeout=2)
        self.monitoring_thread = None

    def _monitor_game_loop(self) -> None:
        """Loop de monitoreo que verifica condiciones de fin de partida."""
        check_interval = 5
        
        while self.running and self.current_session:
            try:
                if self._check_game_end_conditions():
                    self.logger.info("Condición de fin de partida detectada")
                    self._end_session()
                    break
                    
                time.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Error en monitoreo de partida: {e}")
                break

    def _check_game_end_conditions(self) -> bool:
        """Verifica si se cumplen las condiciones para terminar la partida."""
        automation_config = self.config['automation']
        
        with self.session_lock:
            if not self.current_session:
                return False
            
            current_time = time.time()
            
            if self.active_players_count == 0:
                self.logger.info("No hay jugadores activos, terminando partida")
                return True
            
            max_duration = automation_config.get('max_recording_duration', 3600)
            if current_time - self.recording_start_time > max_duration:
                self.logger.info(f"Tiempo máximo alcanzado ({max_duration}s), terminando partida")
                return True
            
            inactivity_timeout = automation_config.get('inactivity_timeout', 300)
            if current_time - self.last_game_data_time > inactivity_timeout:
                self.logger.info(f"Inactividad detectada ({inactivity_timeout}s), terminando partida")
                return True
        
        return False

    def _end_session(self) -> None:
        """Termina la sesión actual y se prepara para la siguiente."""
        self.logger.info("Finalizando sesión actual...")
        
        self._stop_recording()
        
        if self.client and self.client.is_connected():
            self.client.leave_game()
            self.client.disconnect()
        
        if self.emulator and self.emulator.is_running():
            self.emulator.stop_emulator()
        
        self.logger.info("Sesión finalizada, listo para la siguiente partida")

    def _cleanup_session(self) -> None:
        """Limpia las variables de sesión."""
        with self.session_lock:
            self.current_session = None
            self.recording_start_time = 0.0
            self.last_game_data_time = 0.0
            self.active_players_count = 0


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


def main_web() -> None:
    """Función principal con interfaz web."""
    parser = argparse.ArgumentParser(
        description="Bot para grabar partidas de N64 desde servidores Kaillera (con interfaz web)"
    )
    parser.add_argument(
        '--config',
        type=Path,
        default=Path('config/settings.yaml'),
        help='Ruta al archivo de configuración'
    )
    parser.add_argument(
        '--host',
        type=str,
        default='0.0.0.0',
        help='Host para la interfaz web (default: 0.0.0.0)'
    )
    parser.add_argument(
        '--port',
        type=int,
        default=5000,
        help='Puerto para la interfaz web (default: 5000)'
    )
    parser.add_argument(
        '--no-bot',
        action='store_true',
        help='No iniciar el bot automáticamente, solo la interfaz web'
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
    web_interface = None
    
    try:
        from .web import WebInterface
        
        web_interface = WebInterface(bot, host=args.host, port=args.port)
        web_interface.start_server()
        
        print("\n" + "=" * 60)
        print("🎮 KAILLERA BOT - INTERFAZ WEB")
        print("=" * 60)
        print(f"\n🌐 Interfaz web disponible en:")
        print(f"   http://localhost:{args.port}")
        print(f"   http://0.0.0.0:{args.port}")
        print(f"\n📍 Accesible desde cualquier dispositivo en tu red local")
        print(f"   http://<tu-ip-local>:{args.port}")
        print("\n" + "=" * 60)
        print("Presiona Ctrl+C para detener\n")
        
        if not args.no_bot:
            bot_thread = threading.Thread(target=bot.start, daemon=True)
            bot_thread.start()
        
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nDeteniendo...")
        if web_interface:
            web_interface.stop_server()
        bot.stop()
    except ImportError as e:
        print(f"\nError: Dependencias de interfaz web no instaladas")
        print(f"Detalles: {e}")
        print("\nPara usar la interfaz web, instala las dependencias:")
        print("  pip install -e .")
        sys.exit(1)


if __name__ == '__main__':
    main()
