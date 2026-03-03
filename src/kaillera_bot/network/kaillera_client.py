"""Cliente para conectar a servidores Kaillera usando protocolo UDP v086."""

import logging
import socket
import struct
import threading
import time
from typing import Any, Callable, Dict, List, Optional


class KailleraClient:
    """Cliente para conectarse a servidores Kaillera via UDP."""

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
        self.game_id: int = 0
        self.players: Dict[int, Dict[str, Any]] = {}
        self.player_number: int = 0
        self.message_number: int = 0

        self.receive_thread: Optional[threading.Thread] = None
        self.ack_thread: Optional[threading.Thread] = None
        self.running = False

        self.on_player_join: Optional[Callable] = None
        self.on_player_leave: Optional[Callable] = None
        self.on_game_start: Optional[Callable] = None
        self.on_game_data: Optional[Callable] = None

    def connect(self, server_address: str, port: int = KAILLERA_PORT) -> bool:
        """Conecta al servidor Kaillera usando UDP."""
        try:
            self.server_address = server_address
            self.server_port = port
            self.message_number = 0

            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.settimeout(10)

            hello_msg = b"HELLO0.83\x00"
            self._socket.sendto(hello_msg, (server_address, port))

            data, _ = self._socket.recvfrom(1024)
            
            if not data.startswith(b"HELLOD00D"):
                self.logger.error(f"Respuesta invalida del servidor: {data[:20]}")
                return False

            port_str = data[9:].rstrip(b'\x00').decode('latin-1')
            self.logger.debug(f"Servidor asigno puerto: {port_str}")

            login_msg = self._build_user_information()
            self._socket.sendto(login_msg, (server_address, port))

            self.connected = True
            self.running = True

            self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.receive_thread.start()

            self.ack_thread = threading.Thread(target=self._ack_loop, daemon=True)
            self.ack_thread.start()

            self.logger.info(f"Conectado a {server_address}:{port}")
            return True

        except socket.timeout:
            self.logger.error(f"Timeout conectando a {server_address}:{port}")
            return False
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
        
        if self.ack_thread and self.ack_thread.is_alive():
            self.ack_thread.join(timeout=2)

        self.logger.info("Desconectado del servidor")

    def join_game(self, game_name: str) -> bool:
        """Se une a una partida específica."""
        if not self.connected:
            self.logger.error("No está conectado al servidor")
            return False

        try:
            join_msg = self._build_join_game(self.game_id)
            self._socket.sendto(join_msg, (self.server_address, self.server_port))
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
            leave_msg = self._build_leave_game()
            self._socket.sendto(leave_msg, (self.server_address, self.server_port))
            self.current_game = None
            self.game_id = 0
            self.players.clear()
            self.logger.info("Partida abandonada")

        except Exception as e:
            self.logger.error(f"Error abandonando partida: {e}")

    def send_game_data(self, data: bytes) -> None:
        """Envía datos del juego al servidor."""
        if not self.connected or not self.current_game:
            return

        try:
            packet = self._build_game_data(data)
            self._socket.sendto(packet, (self.server_address, self.server_port))

        except Exception as e:
            self.logger.error(f"Error enviando datos de juego: {e}")

    def _next_message_number(self) -> int:
        """Obtiene el siguiente número de mensaje."""
        num = self.message_number
        self.message_number = (self.message_number + 1) & 0xFFFF
        return num

    def _build_user_information(self) -> bytes:
        """Construye mensaje UserInformation (0x03)."""
        msg_num = self._next_message_number()
        
        username_bytes = self.username.encode('latin-1') + b'\x00'
        client_type = b"Mupen64Plus 2.0\x00"
        connection_type = b'\x02'
        
        body = username_bytes + client_type + connection_type
        msg_length = 1 + len(body)
        
        bundle = b'\x01'
        bundle += msg_num.to_bytes(2, 'little')
        bundle += msg_length.to_bytes(2, 'little')
        bundle += b'\x03'
        bundle += body
        
        return bundle

    def _build_client_ack(self, msg_num: int) -> bytes:
        """Construye mensaje ClientAck (0x06)."""
        bundle = b'\x01'
        bundle += msg_num.to_bytes(2, 'little')
        bundle += (17).to_bytes(2, 'little')
        bundle += b'\x06'
        bundle += (0).to_bytes(4, 'little')
        bundle += (1).to_bytes(4, 'little')
        bundle += (2).to_bytes(4, 'little')
        bundle += (3).to_bytes(4, 'little')
        
        return bundle

    def _build_join_game(self, game_id: int) -> bytes:
        """Construye mensaje JoinGame (0x0C)."""
        msg_num = self._next_message_number()
        
        body = b'\x00'
        body += game_id.to_bytes(2, 'little')
        body += b'\x00\x00'
        body += b'\x00'
        body += (0).to_bytes(4, 'little')
        body += (0xFFFF).to_bytes(2, 'little')
        body += b'\x02'
        
        msg_length = 5 + len(body)
        
        bundle = b'\x01'
        bundle += msg_num.to_bytes(2, 'little')
        bundle += msg_length.to_bytes(2, 'little')
        bundle += b'\x0C'
        bundle += body
        
        return bundle

    def _build_leave_game(self) -> bytes:
        """Construye mensaje para abandonar partida."""
        msg_num = self._next_message_number()
        
        body = b'\x00'
        body += self.game_id.to_bytes(2, 'little')
        
        msg_length = 5 + len(body)
        
        bundle = b'\x01'
        bundle += msg_num.to_bytes(2, 'little')
        bundle += msg_length.to_bytes(2, 'little')
        bundle += b'\x0D'
        bundle += body
        
        return bundle

    def _build_game_data(self, data: bytes) -> bytes:
        """Construye mensaje GameData (0x12)."""
        msg_num = self._next_message_number()
        
        body = b'\x00'
        body += len(data).to_bytes(2, 'little')
        body += data
        
        msg_length = 5 + len(body)
        
        bundle = b'\x01'
        bundle += msg_num.to_bytes(2, 'little')
        bundle += msg_length.to_bytes(2, 'little')
        bundle += b'\x12'
        bundle += body
        
        return bundle

    def _receive_loop(self) -> None:
        """Loop de recepción de mensajes del servidor."""
        while self.running and self.connected:
            try:
                if not self._socket:
                    break
                
                self._socket.settimeout(1.0)
                data, _ = self._socket.recvfrom(self.BUFFER_SIZE)
                
                if not data:
                    continue

                self._process_bundle(data)

            except socket.timeout:
                continue

            except Exception as e:
                if self.running:
                    self.logger.debug(f"Error recibiendo datos: {e}")

    def _ack_loop(self) -> None:
        """Loop para enviar ACKs periódicos y mantener conexion."""
        while self.running and self.connected:
            try:
                time.sleep(5)
                if self.connected and self._socket:
                    ack = self._build_client_ack(self.message_number)
                    self._socket.sendto(ack, (self.server_address, self.server_port))
            except Exception as e:
                if self.running:
                    self.logger.debug(f"Error enviando ACK: {e}")

    def _process_bundle(self, data: bytes) -> None:
        """Procesa un bundle de mensajes v086."""
        try:
            if len(data) < 1:
                return
            
            msg_count = data[0]
            pos = 1
            
            for _ in range(msg_count):
                if pos + 5 > len(data):
                    break
                
                msg_number = int.from_bytes(data[pos:pos+2], 'little')
                pos += 2
                msg_length = int.from_bytes(data[pos:pos+2], 'little')
                pos += 2
                msg_type = data[pos]
                pos += 1
                
                msg_data = data[pos:pos + msg_length - 5]
                pos += msg_length - 5
                
                self._process_message(msg_type, msg_number, msg_data)

        except Exception as e:
            self.logger.error(f"Error procesando bundle: {e}")

    def _process_message(self, msg_type: int, msg_number: int, data: bytes) -> None:
        """Procesa un mensaje individual."""
        try:
            if msg_type == 0x04:
                self._handle_server_status(data)
            elif msg_type == 0x05:
                pass
            elif msg_type == 0x0A:
                self._handle_create_game(data)
            elif msg_type == 0x0C:
                self._handle_join_game_notification(data)
            elif msg_type == 0x0D:
                self._handle_leave_game_notification(data)
            elif msg_type == 0x11:
                pass
            elif msg_type == 0x12:
                self._handle_game_data(data)
            elif msg_type == 0x13:
                self._handle_game_data(data)

        except Exception as e:
            self.logger.error(f"Error procesando mensaje tipo {msg_type}: {e}")

    def _handle_server_status(self, data: bytes) -> None:
        """Maneja mensaje ServerStatus con lista de usuarios y juegos."""
        try:
            if len(data) < 9:
                return
            
            pos = 1
            num_users = int.from_bytes(data[pos:pos+4], 'little')
            pos += 4
            num_games = int.from_bytes(data[pos:pos+4], 'little')
            pos += 4
            
            for _ in range(num_users):
                while pos < len(data) and data[pos] != 0:
                    pos += 1
                pos += 1
                pos += 7
            
            for i in range(num_games):
                game_name_start = pos
                while pos < len(data) and data[pos] != 0:
                    pos += 1
                game_name = data[game_name_start:pos].decode('latin-1', errors='ignore')
                pos += 1
                
                game_id = int.from_bytes(data[pos:pos+4], 'little')
                pos += 4
                
                if self.current_game and game_name == self.current_game:
                    self.game_id = game_id
                
                while pos < len(data) and data[pos] != 0:
                    pos += 1
                pos += 1
                while pos < len(data) and data[pos] != 0:
                    pos += 1
                pos += 1
                while pos < len(data) and data[pos] != 0:
                    pos += 1
                pos += 1
                pos += 1

        except Exception as e:
            self.logger.error(f"Error procesando ServerStatus: {e}")

    def _handle_create_game(self, data: bytes) -> None:
        """Maneja notificación de creación de partida."""
        try:
            pos = 1
            while pos < len(data) and data[pos] != 0:
                pos += 1
            username = data[1:pos].decode('latin-1', errors='ignore')
            pos += 1
            
            game_name_start = pos
            while pos < len(data) and data[pos] != 0:
                pos += 1
            game_name = data[game_name_start:pos].decode('latin-1', errors='ignore')
            
            self.logger.info(f"Partida creada: {game_name} por {username}")

        except Exception as e:
            self.logger.error(f"Error procesando CreateGame: {e}")

    def _handle_join_game_notification(self, data: bytes) -> None:
        """Maneja notificación de jugador uniéndose."""
        try:
            pos = 1
            game_id = int.from_bytes(data[pos:pos+4], 'little')
            pos += 8
            
            while pos < len(data) and data[pos] != 0:
                pos += 1
            username = data[8:pos].decode('latin-1', errors='ignore')
            pos += 1
            
            ping = int.from_bytes(data[pos:pos+4], 'little')
            pos += 4
            user_id = int.from_bytes(data[pos:pos+2], 'little')
            pos += 2
            connection_type = data[pos] if pos < len(data) else 0
            
            self.players[user_id] = {
                'name': username,
                'number': user_id,
                'ping': ping
            }
            
            self.logger.info(f"Jugador unido: {username} (#{user_id})")

            if self.on_player_join:
                self.on_player_join(username, user_id)

        except Exception as e:
            self.logger.error(f"Error procesando JoinGame: {e}")

    def _handle_leave_game_notification(self, data: bytes) -> None:
        """Maneja notificación de jugador saliendo."""
        try:
            pos = 1
            game_id = int.from_bytes(data[pos:pos+4], 'little')
            pos += 4
            
            user_id = int.from_bytes(data[pos:pos+2], 'little')
            
            player = self.players.pop(user_id, None)
            if player:
                self.logger.info(f"Jugador salió: {player['name']}")

                if self.on_player_leave:
                    self.on_player_leave(player['name'], user_id)

        except Exception as e:
            self.logger.error(f"Error procesando LeaveGame: {e}")

    def _handle_game_data(self, data: bytes) -> None:
        """Maneja datos del juego recibidos."""
        try:
            if len(data) < 3:
                return
            
            pos = 1
            data_length = int.from_bytes(data[pos:pos+2], 'little')
            pos += 2
            
            game_data = data[pos:pos+data_length]
            
            if self.on_game_data:
                self.on_game_data(game_data)

        except Exception as e:
            self.logger.error(f"Error procesando GameData: {e}")

    def get_player_list(self) -> List[Dict[str, Any]]:
        """Retorna lista de jugadores en la partida."""
        return list(self.players.values())

    def is_connected(self) -> bool:
        """Verifica si está conectado al servidor."""
        return self.connected

    def get_current_game(self) -> Optional[str]:
        """Retorna el nombre de la partida actual."""
        return self.current_game
