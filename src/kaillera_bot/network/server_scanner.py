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
    SCAN_TIMEOUT = 5

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
                
                ping = self.ping_server(server)
                server.ping = ping
                
                if ping >= 0:
                    self.servers.append(server)
                    self.logger.info(f"Servidor configurado accesible: {server.name} ({server.address}:{server.port})")
                else:
                    self.logger.warning(f"Servidor configurado no accesible: {server.name} ({server.address}:{server.port})")
                    
            except Exception as e:
                self.logger.error(f"Error verificando servidor configurado: {e}")

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

    def scan_server_games(self, server: ServerInfo) -> List[GameSession]:
        """Escanea las partidas en un servidor específico."""
        sessions = []

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.SCAN_TIMEOUT)
            sock.connect((server.address, server.port))

            request = b"LIST_GAMES\n"
            sock.send(request)

            data = sock.recv(8192)
            sock.close()

            sessions = self._parse_game_list(data, server)

            for session in sessions:
                self.sessions.append(session)
                if self.on_game_found:
                    self.on_game_found(session)

        except Exception as e:
            self.logger.debug(f"Error escaneando juegos en {server.address}: {e}")

        return sessions

    def _parse_game_list(self, data: bytes, server: ServerInfo) -> List[GameSession]:
        """Parsea la lista de partidas de un servidor."""
        sessions = []

        try:
            message = data.decode('utf-8', errors='ignore')
            lines = message.strip().split('\n')

            i = 0
            while i < len(lines):
                line = lines[i]

                if line.startswith("GAME:"):
                    game_name = line[5:].strip()
                    players = []
                    max_players = 4
                    status = "Waiting"

                    i += 1
                    while i < len(lines) and not lines[i].startswith("GAME:"):
                        if lines[i].startswith("PLAYERS:"):
                            players_str = lines[i][8:].strip()
                            players = [p.strip() for p in players_str.split(',') if p.strip()]

                        elif lines[i].startswith("MAX:"):
                            max_players = int(lines[i][4:].strip())

                        elif lines[i].startswith("STATUS:"):
                            status = lines[i][7:].strip()

                        i += 1

                    session = GameSession(
                        game_name=game_name,
                        server=server,
                        players=players,
                        max_players=max_players,
                        status=status
                    )
                    sessions.append(session)

                else:
                    i += 1

        except Exception as e:
            self.logger.error(f"Error parseando lista de juegos: {e}")

        return sessions

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

                    for server in self.servers:
                        if server.players >= min_players:
                            sessions = self.scan_server_games(server)

                            if self.on_game_found:
                                for session in sessions:
                                    if game_filter:
                                        if any(g.lower() in session.game_name.lower() for g in game_filter):
                                            self.on_game_found(session)
                                    else:
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
        """Calcula el ping a un servidor."""
        try:
            start = time.time()
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.SCAN_TIMEOUT)
            sock.connect((server.address, server.port))
            sock.close()
            return int((time.time() - start) * 1000)

        except Exception as e:
            self.logger.debug(f"Error haciendo ping a {server.address}: {e}")
            return -1
