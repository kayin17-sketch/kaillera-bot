"""Cliente para conectar a servidores Kaillera."""

import logging
import socket
import struct
import threading
import time
from typing import Any, Callable, Dict, List, Optional


class KailleraClient:
    """Cliente para conectarse a servidores Kaillera."""

    KAILLERA_PORT = 27888
    BUFFER_SIZE = 4096

    def __init__(self, username: str = "KailleraBot"):
        self.username = username
        self.logger = logging.getLogger(__name__)

        self._socket: Optional[socket.socket] = None
        self.connected = False
        self.server_address: Optional[str] = None
        self.server_port: int = self.KAILLERA_PORT

        self.current_game: Optional[str] = None
        self.players: Dict[int, Dict[str, Any]] = {}
        self.player_number: int = 0

        self.receive_thread: Optional[threading.Thread] = None
        self.running = False

        self.on_player_join: Optional[Callable] = None
        self.on_player_leave: Optional[Callable] = None
        self.on_game_start: Optional[Callable] = None
        self.on_game_data: Optional[Callable] = None

    @property
    def socket(self) -> socket.socket:
        """Retorna el socket, lanzando error si no está disponible."""
        if self._socket is None:
            raise RuntimeError("Socket no inicializado")
        return self._socket

    def connect(self, server_address: str, port: int = KAILLERA_PORT) -> bool:
        """Conecta al servidor Kaillera."""
        try:
            self.server_address = server_address
            self.server_port = port

            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(10)
            self._socket.connect((server_address, port))

            self.connected = True
            self.running = True

            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()

            self._send_hello()
            self.logger.info(f"Conectado a {server_address}:{port}")

            return True

        except Exception as e:
            self.logger.error(f"Error conectando a {server_address}:{port}: {e}")
            self.connected = False
            return False

    def disconnect(self) -> None:
        """Desconecta del servidor."""
        if not self.connected:
            return

        self.running = False
        self.connected = False

        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join(timeout=2)

        self.logger.info("Desconectado del servidor")

    def join_game(self, game_name: str) -> bool:
        """Se une a una partida específica."""
        if not self.connected:
            self.logger.error("No está conectado al servidor")
            return False

        try:
            self._send_join_game(game_name)
            self.current_game = game_name
            self.logger.info(f"Uniéndose a partida: {game_name}")
            return True

        except Exception as e:
            self.logger.error(f"Error uniéndose a partida: {e}")
            return False

    def leave_game(self) -> None:
        """Abandona la partida actual."""
        if not self.connected or not self.current_game:
            return

        try:
            self._send_leave_game()
            self.current_game = None
            self.players.clear()
            self.logger.info("Partida abandonada")

        except Exception as e:
            self.logger.error(f"Error abandonando partida: {e}")

    def send_game_data(self, data: bytes) -> None:
        """Envía datos del juego al servidor."""
        if not self.connected or not self.current_game:
            return

        try:
            packet = self._build_game_data_packet(data)
            self.socket.send(packet)

        except Exception as e:
            self.logger.error(f"Error enviando datos de juego: {e}")

    def _send_hello(self) -> None:
        """Envía paquete de saludo al servidor."""
        hello_data = f"HELLO\n{self.username}\n".encode('utf-8')
        self.socket.send(hello_data)

    def _send_join_game(self, game_name: str) -> None:
        """Envía solicitud para unirse a una partida."""
        join_data = f"JOIN\n{game_name}\n".encode('utf-8')
        self.socket.send(join_data)

    def _send_leave_game(self) -> None:
        """Envía solicitud para abandonar partida."""
        leave_data = b"LEAVE\n"
        self.socket.send(leave_data)

    def _build_game_data_packet(self, data: bytes) -> bytes:
        """Construye un paquete de datos del juego."""
        length = len(data)
        header = struct.pack('<I', length)
        return header + data

    def _receive_loop(self) -> None:
        """Loop de recepción de mensajes del servidor."""
        while self.running and self.connected:
            try:
                if not self._socket:
                    break
                    
                data = self._socket.recv(self.BUFFER_SIZE)
                if not data:
                    self.logger.warning("Conexión cerrada por el servidor")
                    self.connected = False
                    break

                self._process_server_message(data)

            except socket.timeout:
                continue

            except RuntimeError:
                break

            except Exception as e:
                if self.running:
                    self.logger.error(f"Error recibiendo datos: {e}")
                break

    def _process_server_message(self, data: bytes) -> None:
        """Procesa mensajes recibidos del servidor."""
        try:
            message = data.decode('utf-8', errors='ignore')

            if message.startswith("PLAYER_JOIN"):
                self._handle_player_join(message)

            elif message.startswith("PLAYER_LEAVE"):
                self._handle_player_leave(message)

            elif message.startswith("GAME_START"):
                self._handle_game_start(message)

            elif message.startswith("GAME_DATA"):
                self._handle_game_data(data)

        except Exception as e:
            self.logger.error(f"Error procesando mensaje del servidor: {e}")

    def _handle_player_join(self, message: str) -> None:
        """Maneja evento de jugador uniéndose."""
        parts = message.strip().split('\n')
        if len(parts) >= 3:
            player_num = int(parts[1])
            player_name = parts[2]
            self.players[player_num] = {'name': player_name, 'number': player_num}
            self.logger.info(f"Jugador unido: {player_name} (#{player_num})")

            if self.on_player_join:
                self.on_player_join(player_name, player_num)

    def _handle_player_leave(self, message: str) -> None:
        """Maneja evento de jugador saliendo."""
        parts = message.strip().split('\n')
        if len(parts) >= 2:
            player_num = int(parts[1])
            player = self.players.pop(player_num, None)
            if player:
                self.logger.info(f"Jugador salió: {player['name']}")

                if self.on_player_leave:
                    self.on_player_leave(player['name'], player_num)

    def _handle_game_start(self, message: str) -> None:
        """Maneja evento de inicio de partida."""
        self.logger.info("Partida iniciada")

        if self.on_game_start:
            self.on_game_start(self.current_game)

    def _handle_game_data(self, data: bytes) -> None:
        """Maneja datos del juego recibidos."""
        if self.on_game_data:
            try:
                game_data = data[10:]
                self.on_game_data(game_data)
            except Exception as e:
                self.logger.error(f"Error procesando datos de juego: {e}")

    def get_player_list(self) -> List[Dict[str, Any]]:
        """Retorna lista de jugadores en la partida."""
        return list(self.players.values())

    def is_connected(self) -> bool:
        """Verifica si está conectado al servidor."""
        return self.connected

    def get_current_game(self) -> Optional[str]:
        """Retorna el nombre de la partida actual."""
        return self.current_game
