"""Escáner de servidores Kaillera."""

import logging
import re
import socket
import threading
import time
from typing import Any, Callable, Dict, List, Optional
from xml.etree import ElementTree

import requests


class ServerInfo:
    """Información de un servidor Kaillera."""

    def __init__(
        self,
        name: str,
        address: str,
        port: int = 27888,
        players: int = 0,
        max_players: int = 0,
        games: Optional[List[str]] = None,
        country: str = "Unknown",
        ping: int = 0
    ):
        self.name = name
        self.address = address
        self.port = port
        self.players = players
        self.max_players = max_players
        self.games = games or []
        self.country = country
        self.ping = ping

    def __repr__(self) -> str:
        return f"ServerInfo({self.name}, {self.address}:{self.port}, {self.players}/{self.max_players} players)"


class GameSession:
    """Información de una sesión de juego en un servidor."""

    def __init__(
        self,
        game_name: str,
        server: ServerInfo,
        players: Optional[List[str]] = None,
        max_players: int = 4,
        status: str = "Waiting"
    ):
        self.game_name = game_name
        self.server = server
        self.players = players or []
        self.max_players = max_players
        self.status = status

    def __repr__(self) -> str:
        return f"GameSession({self.game_name}, {len(self.players)}/{self.max_players} players, {self.status})"


class ServerScanner:
    """Escanea servidores Kaillera en busca de partidas."""

    MASTER_SERVERS = [
        "master.kaillera.com",
        "kaillera.com",
    ]

    KAILLERA_PORT = 27888
    SCAN_TIMEOUT = 10

    def __init__(self, configured_servers: Optional[List[Dict]] = None):
        self.logger = logging.getLogger(__name__)
        self.servers: List[ServerInfo] = []
        self.sessions: List[GameSession] = []
        self.scanning = False
        self.configured_servers = configured_servers or []

        self.on_server_found: Optional[Callable[[ServerInfo], None]] = None
        self.on_game_found: Optional[Callable[[GameSession], None]] = None

    def scan_master_servers(self) -> List[ServerInfo]:
        """Escanea los servidores maestros de Kaillera y los servidores configurados."""
        self.servers = []

        for master in self.MASTER_SERVERS:
            try:
                servers = self._query_master_server(master)
                self.servers.extend(servers)

            except Exception as e:
                self.logger.error(f"Error escaneando {master}: {e}")

        for server_config in self.configured_servers:
            try:
                server = ServerInfo(
                    name=server_config.get('name', 'Unknown'),
                    address=server_config.get('address', ''),
                    port=server_config.get('port', self.KAILLERA_PORT)
                )
                
                self.servers.append(server)
                self.logger.info(f"Servidor configurado: {server.name} ({server.address}:{server.port})")
                    
            except Exception as e:
                self.logger.error(f"Error agregando servidor configurado: {e}")

        self.logger.info(f"Encontrados {len(self.servers)} servidores")
        return self.servers

    def _query_master_server(self, master_address: str) -> List[ServerInfo]:
        """Consulta un servidor maestro para obtener lista de servidores."""
        servers = []

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.SCAN_TIMEOUT)
            sock.connect((master_address, self.KAILLERA_PORT))

            request = b"\x00\x00\x00\x00"
            sock.send(request)

            data = sock.recv(8192)
            sock.close()

            servers = self._parse_server_list(data)

        except Exception as e:
            self.logger.debug(f"No se pudo conectar a {master_address}: {e}")

        return servers

    def _parse_server_list(self, data: bytes) -> List[ServerInfo]:
        """Parsea la lista de servidores recibida."""
        servers = []

        try:
            xml_data = data.decode('utf-8', errors='ignore')
            root = ElementTree.fromstring(xml_data)

            for server_elem in root.findall('.//server'):
                name = server_elem.get('name', 'Unknown')
                address = server_elem.get('address', '')
                port = int(server_elem.get('port', self.KAILLERA_PORT))
                players = int(server_elem.get('users', '0'))
                max_players = int(server_elem.get('maxusers', '100'))

                server = ServerInfo(
                    name=name,
                    address=address,
                    port=port,
                    players=players,
                    max_players=max_players
                )
                servers.append(server)

        except Exception as e:
            self.logger.error(f"Error parseando lista de servidores: {e}")

        return servers

    def start_continuous_scan(
        self,
        interval: int = 60,
        game_filter: Optional[List[str]] = None,
        min_players: int = 2
    ) -> None:
        """Inicia escaneo continuo de servidores."""
        self.scanning = True

        def scan_loop():
            while self.scanning:
                try:
                    self.scan_master_servers()
                    self.logger.info(f"Escaneando {len(self.servers)} servidores...")

                    for server in self.servers:
                        self.logger.debug(f"Escaneando servidor: {server.name}")
                        sessions = self.scan_server_games(server)
                        self.logger.info(f"Encontradas {len(sessions)} partidas en {server.name}")

                        if self.on_game_found:
                            for session in sessions:
                                if game_filter:
                                    if any(g.lower() in session.game_name.lower() for g in game_filter):
                                        self.logger.info(f"Partida coincide con filtro: {session.game_name}")
                                        self.on_game_found(session)
                                else:
                                    self.logger.info(f"Partida encontrada: {session.game_name}")
                                    self.on_game_found(session)

                    time.sleep(interval)

                except Exception as e:
                    self.logger.error(f"Error en escaneo continuo: {e}")
                    time.sleep(5)

        thread = threading.Thread(target=scan_loop, daemon=True)
        thread.start()
        self.logger.info("Escaneo continuo iniciado")

    def stop_continuous_scan(self) -> None:
        """Detiene el escaneo continuo."""
        self.scanning = False
        self.logger.info("Escaneo continuo detenido")

    def get_servers(self) -> List[ServerInfo]:
        """Retorna la lista de servidores encontrados."""
        return self.servers

    def get_sessions(self) -> List[GameSession]:
        """Retorna la lista de sesiones de juego encontradas."""
        return self.sessions

    def ping_server(self, server: ServerInfo) -> int:
        """Calcula el ping a un servidor usando protocolo Kaillera (UDP)."""
        try:
            start = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(self.SCAN_TIMEOUT)
            
            hello_msg = b"HELLO0.83\x00"
            sock.sendto(hello_msg, (server.address, server.port))
            
            data, _ = sock.recvfrom(1024)
            sock.close()
            
            if data.startswith(b"HELLOD00D"):
                return int((time.time() - start) * 1000)
            
            return -1

        except socket.timeout:
            self.logger.debug(f"Timeout UDP para {server.address}:{server.port}")
            return -1
        except Exception as e:
            self.logger.debug(f"Error ping UDP a {server.address}:{server.port}: {e}")
            return -1
    
    def scan_server_games(self, server: ServerInfo) -> List[GameSession]:
        """Escanea las partidas en un servidor específico manteniendo conexion."""
        sessions = []
        self.logger.info(f"[SCAN] Iniciando escaneo de {server.name}...")

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1)
            
            hello_msg = b"HELLO0.83\x00"
            self.logger.info(f"[SCAN] Enviando HELLO a {server.address}")
            sock.sendto(hello_msg, (server.address, server.port))
            
            data, _ = sock.recvfrom(8192)
            self.logger.info(f"[SCAN] Recibido: {data.hex()}")
            
            if not data.startswith(b"HELLOD00D"):
                self.logger.warning(f"[SCAN] Respuesta HELLO invalida de {server.address}")
                sock.close()
                return sessions
            
            login_msg = self._build_login_message("Bot")
            self.logger.info(f"[SCAN] Enviando login: {login_msg.hex()}")
            sock.sendto(login_msg, (server.address, server.port))
            
            data, _ = sock.recvfrom(8192)
            self.logger.info(f"[SCAN] Respuesta login: {data.hex()}")
            
            if len(data) > 5 and data[5] == 0x05:
                msg_num = int.from_bytes(data[1:3], 'little')
                self.logger.info(f"[SCAN] ServerAck recibido, msg_num={msg_num}")
                
                for i in range(4):
                    ack_msg = self._build_client_ack(msg_num + i)
                    sock.sendto(ack_msg, (server.address, server.port))
                    self.logger.info(f"[SCAN] ACK {i+1} enviado")
                    time.sleep(0.5)
                
                for i in range(15):
                    try:
                        data, _ = sock.recvfrom(8192)
                        self.logger.info(f"[SCAN] Mensaje {i+1}: {data.hex()}")
                        
                        if len(data) > 0:
                            msg_count = data[0]
                            self.logger.info(f"[SCAN] Bundle con {msg_count} mensajes")
                            pos = 1
                            
                            for _ in range(msg_count):
                                if pos + 5 > len(data):
                                    break
                                
                                msg_num = int.from_bytes(data[pos:pos+2], 'little')
                                pos += 2
                                msg_len = int.from_bytes(data[pos:pos+2], 'little')
                                pos += 2
                                msg_type = data[pos]
                                pos += 1
                                
                                self.logger.info(f"[SCAN]   - msg_type: {msg_type:#x}")
                                
                                if msg_type == 0x04:
                                    self.logger.info(f"[SCAN] ServerStatus encontrado!")
                                    sessions = self._parse_game_list_v086(data, server)
                                    self.logger.info(f"[SCAN] {len(sessions)} partidas encontradas")
                                    sock.close()
                                    for session in sessions:
                                        self.sessions.append(session)
                                        if self.on_game_found:
                                            self.on_game_found(session)
                                    return sessions
                                elif msg_type == 0x05:
                                    msg_num = int.from_bytes(data[pos-5:pos-3], 'little')
                                    ack_msg = self._build_client_ack(msg_num)
                                    sock.sendto(ack_msg, (server.address, server.port))
                                
                                pos += msg_len - 5
                                
                    except socket.timeout:
                        continue
            
            sock.close()
            
        except Exception as e:
            self.logger.error(f"[SCAN] Error escaneando {server.address}: {type(e).__name__}: {e}")

        return sessions
    
    def _build_client_ack(self, msg_num: int) -> bytes:
        """Construye mensaje ClientAck (0x06)."""
        ack_msg = b"\x01"
        ack_msg += msg_num.to_bytes(2, 'little')
        ack_msg += (17).to_bytes(2, 'little')
        ack_msg += b"\x06"
        ack_msg += b"\x00"
        ack_msg += (0).to_bytes(4, 'little')
        ack_msg += (1).to_bytes(4, 'little')
        ack_msg += (2).to_bytes(4, 'little')
        ack_msg += (3).to_bytes(4, 'little')
        return ack_msg
    
    def _build_login_message(self, username: str) -> bytes:
        """Construye mensaje de login v086."""
        username_bytes = username.encode('latin-1') + b'\x00'
        client_type = b"RMG-K v0.8.21\x00"
        connection_type = b'\x01'
        
        body = username_bytes + client_type + connection_type
        msg_length = 1 + len(body)
        
        bundle = b'\x01'
        bundle += (0).to_bytes(2, 'little')
        bundle += msg_length.to_bytes(2, 'little')
        bundle += b'\x03'
        bundle += body
        
        self.logger.debug(f"Login bundle: {bundle.hex()}")
        return bundle
    
    def _parse_game_list_v086(self, data: bytes, server: ServerInfo) -> List[GameSession]:
        """Parsea la lista de partidas del mensaje ServerStatus (0x04)."""
        sessions = []
        
        try:
            if len(data) < 10:
                return sessions
            
            pos = 6
            pos += 1
            num_users = int.from_bytes(data[pos:pos+4], 'little')
            pos += 4
            num_games = int.from_bytes(data[pos:pos+4], 'little')
            pos += 4
            
            self.logger.debug(f"ServerStatus: {num_users} usuarios, {num_games} partidas")
            
            for _ in range(num_users):
                while pos < len(data) and data[pos] != 0:
                    pos += 1
                pos += 1
                pos += 7
            
            for _ in range(num_games):
                game_name_start = pos
                while pos < len(data) and data[pos] != 0:
                    pos += 1
                game_name = data[game_name_start:pos].decode('latin-1', errors='ignore')
                pos += 1
                
                game_id = int.from_bytes(data[pos:pos+4], 'little')
                pos += 4
                
                client_start = pos
                while pos < len(data) and data[pos] != 0:
                    pos += 1
                pos += 1
                
                username_start = pos
                while pos < len(data) and data[pos] != 0:
                    pos += 1
                pos += 1
                
                players_start = pos
                while pos < len(data) and data[pos] != 0:
                    pos += 1
                players_str = data[players_start:pos].decode('latin-1', errors='ignore')
                pos += 1
                
                status = data[pos] if pos < len(data) else 0
                pos += 1
                
                try:
                    current, max_p = map(int, players_str.split('/'))
                except:
                    current, max_p = 1, 4
                
                session = GameSession(
                    game_name=game_name,
                    server=server,
                    players=[],
                    max_players=max_p,
                    status="Waiting" if status == 0 else "Playing"
                )
                sessions.append(session)
                self.logger.debug(f"Partida encontrada: {game_name} ({players_str})")
            
        except Exception as e:
            self.logger.error(f"Error parseando ServerStatus: {e}")
        
        return sessions
