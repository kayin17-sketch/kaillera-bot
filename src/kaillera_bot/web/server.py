"""Servidor web para interfaz gráfica del bot."""

import json
import logging
import os
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_socketio import SocketIO, emit
from flask_cors import CORS

from ..main import KailleraBot


class WebInterface:
    """Interfaz web para controlar el bot."""

    def __init__(self, bot: KailleraBot, host: str = "0.0.0.0", port: int = 5000):
        self.bot = bot
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__)

        self.app = Flask(
            __name__,
            template_folder=str(Path(__file__).parent / "templates"),
            static_folder=str(Path(__file__).parent / "static")
        )
        self.app.config['SECRET_KEY'] = 'kaillera-bot-secret-key-2026'
        
        CORS(self.app)
        self.socketio = SocketIO(self.app, cors_allowed_origins="*", async_mode='threading')

        self._setup_routes()
        self._setup_socketio()

        self.server_thread: Optional[threading.Thread] = None
        self.running = False

    def _setup_routes(self) -> None:
        """Configura las rutas de la API REST."""

        @self.app.route('/')
        def index():
            """Página principal."""
            return render_template('index.html')

        @self.app.route('/api/status', methods=['GET'])
        def get_status():
            """Obtiene el estado actual del bot."""
            return jsonify(self._get_bot_status())

        @self.app.route('/api/start', methods=['POST'])
        def start_bot():
            """Inicia el bot."""
            try:
                if not self.bot.running:
                    threading.Thread(target=self.bot.start, daemon=True).start()
                    return jsonify({'success': True, 'message': 'Bot iniciado'})
                return jsonify({'success': False, 'message': 'Bot ya está en ejecución'})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/stop', methods=['POST'])
        def stop_bot():
            """Detiene el bot."""
            try:
                if self.bot.running:
                    self.bot.stop()
                    return jsonify({'success': True, 'message': 'Bot detenido'})
                return jsonify({'success': False, 'message': 'Bot no está en ejecución'})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/config', methods=['GET'])
        def get_config():
            """Obtiene la configuración actual."""
            return jsonify(self.bot.config)

        @self.app.route('/api/config', methods=['POST'])
        def update_config():
            """Actualiza la configuración."""
            try:
                new_config = request.json
                self.bot.config.update(new_config)
                return jsonify({'success': True, 'message': 'Configuración actualizada'})
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/servers', methods=['GET'])
        def get_servers():
            """Obtiene lista de servidores encontrados."""
            if self.bot.scanner:
                servers = []
                for server in self.bot.scanner.get_servers():
                    servers.append({
                        'name': server.name,
                        'address': server.address,
                        'port': server.port,
                        'players': server.players,
                        'max_players': server.max_players,
                        'country': server.country,
                        'ping': server.ping
                    })
                return jsonify(servers)
            return jsonify([])

        @self.app.route('/api/sessions', methods=['GET'])
        def get_sessions():
            """Obtiene lista de sesiones de juego."""
            if self.bot.scanner:
                sessions = []
                for session in self.bot.scanner.get_sessions():
                    sessions.append({
                        'game_name': session.game_name,
                        'server_name': session.server.name,
                        'players': session.players,
                        'max_players': session.max_players,
                        'status': session.status
                    })
                return jsonify(sessions)
            return jsonify([])

        @self.app.route('/api/recordings', methods=['GET'])
        def get_recordings():
            """Obtiene lista de grabaciones."""
            recordings = {'videos': [], 'inputs': [], 'network': []}
            output_dir = Path(self.bot.config['recording']['output_directory'])

            for category in ['videos', 'inputs', 'network']:
                category_dir = output_dir / category
                if category_dir.exists():
                    for file in category_dir.glob('*'):
                        if file.is_file():
                            stat = file.stat()
                            recordings[category].append({
                                'name': file.name,
                                'size': stat.st_size,
                                'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                            })

            return jsonify(recordings)

        @self.app.route('/api/recordings/<category>/<filename>', methods=['GET'])
        def download_recording(category: str, filename: str):
            """Descarga una grabación."""
            output_dir = Path(self.bot.config['recording']['output_directory'])
            category_dir = output_dir / category
            
            if not category_dir.exists():
                return jsonify({'error': 'Categoría no encontrada'}), 404
            
            return send_from_directory(str(category_dir), filename, as_attachment=True)

        @self.app.route('/api/recordings/<category>/<filename>', methods=['DELETE'])
        def delete_recording(category: str, filename: str):
            """Elimina una grabación."""
            try:
                output_dir = Path(self.bot.config['recording']['output_directory'])
                file_path = output_dir / category / filename
                
                if file_path.exists() and file_path.is_file():
                    file_path.unlink()
                    return jsonify({'success': True, 'message': 'Grabación eliminada'})
                return jsonify({'success': False, 'message': 'Archivo no encontrado'}), 404
            except Exception as e:
                return jsonify({'success': False, 'message': str(e)}), 500

        @self.app.route('/api/logs', methods=['GET'])
        def get_logs():
            """Obtiene las últimas líneas del log."""
            log_file = self.bot.config.get('logging', {}).get('file', 'logs/kaillera_bot.log')
            lines = request.args.get('lines', 100, type=int)
            
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    return jsonify({'lines': [line.strip() for line in last_lines]})
            except FileNotFoundError:
                return jsonify({'lines': []})
            except Exception as e:
                return jsonify({'error': str(e)}), 500

    def _setup_socketio(self) -> None:
        """Configura los eventos de SocketIO."""

        @self.socketio.on('connect')
        def handle_connect():
            """Cliente conectado."""
            self.logger.info('Cliente conectado a la interfaz web')
            emit('status_update', self._get_bot_status())

        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Cliente desconectado."""
            self.logger.info('Cliente desconectado de la interfaz web')

        @self.socketio.on('request_status')
        def handle_request_status():
            """Solicitud de estado actualizado."""
            emit('status_update', self._get_bot_status())

    def _get_bot_status(self) -> Dict[str, Any]:
        """Obtiene el estado completo del bot."""
        status = {
            'running': self.bot.running,
            'current_session': self.bot.current_session,
            'active_players': self.bot.active_players_count if hasattr(self.bot, 'active_players_count') else 0,
            'recording_duration': 0.0,
            'connected': False,
            'current_game': None,
            'server': None,
            'scanning': False,
            'servers_found': 0,
            'sessions_found': 0,
            'recordings': {
                'video': self.bot.video_recorder.recording if self.bot.video_recorder else False,
                'inputs': self.bot.input_recorder.recording if self.bot.input_recorder else False,
                'network': self.bot.network_recorder.recording if self.bot.network_recorder else False
            }
        }

        if self.bot.client:
            status['connected'] = self.bot.client.is_connected()
            status['current_game'] = self.bot.client.get_current_game()
            if self.bot.client.server_address:
                status['server'] = f"{self.bot.client.server_address}:{self.bot.client.server_port}"

        if self.bot.scanner:
            status['scanning'] = self.bot.scanner.scanning
            status['servers_found'] = len(self.bot.scanner.get_servers())
            status['sessions_found'] = len(self.bot.scanner.get_sessions())

        if self.bot.current_session and self.bot.recording_start_time > 0:
            import time
            status['recording_duration'] = time.time() - self.bot.recording_start_time

        return status

    def broadcast_status(self) -> None:
        """Envía actualización de estado a todos los clientes conectados."""
        self.socketio.emit('status_update', self._get_bot_status())

    def broadcast_log(self, log_line: str) -> None:
        """Envía una línea de log a todos los clientes."""
        self.socketio.emit('log_update', {'line': log_line})

    def start_server(self) -> None:
        """Inicia el servidor web."""
        if self.running:
            self.logger.warning("El servidor web ya está en ejecución")
            return

        self.running = True
        self.logger.info(f"Iniciando interfaz web en http://{self.host}:{self.port}")
        
        def run_server():
            self.socketio.run(
                self.app,
                host=self.host,
                port=self.port,
                debug=False,
                use_reloader=False,
                log_output=False
            )

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

    def stop_server(self) -> None:
        """Detiene el servidor web."""
        if not self.running:
            return

        self.running = False
        self.logger.info("Deteniendo interfaz web...")
        self.socketio.stop()

    def is_running(self) -> bool:
        """Verifica si el servidor está en ejecución."""
        return self.running
