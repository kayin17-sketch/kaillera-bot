"""Servidor web seguro para interfaz gráfica del bot."""

import os
import re
import logging
import secrets
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from flask import Flask, jsonify, render_template, request, send_from_directory, abort
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from werkzeug.utils import secure_filename

from ..main import KailleraBot


class SecurityConfig:
    """Configuración de seguridad."""
    
    MAX_LOG_LINES = 1000
    MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1 GB
    ALLOWED_CATEGORIES = {'videos', 'inputs', 'network'}
    RATE_LIMIT_REQUESTS = 100
    RATE_LIMIT_WINDOW = 60  # segundos


class WebInterface:
    """Interfaz web segura para controlar el bot."""

    def __init__(self, bot: KailleraBot, host: str = "0.0.0.0", port: int = 5000):
        self.bot = bot
        self.host = host
        self.port = port
        self.logger = logging.getLogger(__name__)
        
        self.security = SecurityConfig()
        
        self._rate_limit_data: Dict[str, list] = {}
        self._rate_limit_lock = threading.Lock()
        
        self.app = Flask(
            __name__,
            template_folder=str(Path(__file__).parent / "templates"),
            static_folder=str(Path(__file__).parent / "static")
        )
        
        self._configure_security()
        
        CORS(self.app, origins=self._get_allowed_origins())
        self.socketio = SocketIO(
            self.app, 
            cors_allowed_origins=self._get_allowed_origins(),
            async_mode='threading'
        )

        self._setup_routes()
        self._setup_socketio()
        self._setup_error_handlers()

        self.server_thread: Optional[threading.Thread] = None
        self.running = False

    def _configure_security(self) -> None:
        """Configura parámetros de seguridad."""
        self.app.config['SECRET_KEY'] = self._get_or_create_secret_key()
        
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
        
        self.app.after_request(self._add_security_headers)

    def _get_or_create_secret_key(self) -> str:
        """Obtiene o crea una clave secreta segura."""
        secret_file = Path('config/.web_secret')
        
        if secret_file.exists():
            with open(secret_file, 'r') as f:
                return f.read().strip()
        
        secret_key = secrets.token_hex(32)
        secret_file.parent.mkdir(parents=True, exist_ok=True)
        with open(secret_file, 'w') as f:
            f.write(secret_key)
        
        os.chmod(secret_file, 0o600)
        
        return secret_key

    def _get_allowed_origins(self) -> list:
        """Obiene orígenes permitidos para CORS."""
        origins = ['http://localhost:5000']
        
        if self.host == '0.0.0.0':
            import socket
            try:
                hostname = socket.gethostname()
                local_ip = socket.gethostbyname(hostname)
                origins.append(f'http://{local_ip}:5000')
                origins.append(f'http://{hostname}:5000')
            except Exception:
                pass
        
        return origins

    def _add_security_headers(self, response):
        """Agrega headers de seguridad a todas las respuestas."""
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdn.socket.io; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; font-src https://cdn.jsdelivr.net"
        return response

    def _check_rate_limit(self, client_id: str) -> bool:
        """Verifica rate limiting de forma thread-safe."""
        current_time = time.time()
        
        with self._rate_limit_lock:
            if client_id not in self._rate_limit_data:
                self._rate_limit_data[client_id] = []
            
            requests = self._rate_limit_data[client_id]
            requests = [t for t in requests if current_time - t < self.security.RATE_LIMIT_WINDOW]
            
            if len(requests) >= self.security.RATE_LIMIT_REQUESTS:
                return False
            
            requests.append(current_time)
            self._rate_limit_data[client_id] = requests
            return True

    def _validate_category(self, category: str) -> bool:
        """Valida que la categoría sea permitida."""
        return category in self.security.ALLOWED_CATEGORIES

    def _validate_filename(self, filename: str) -> bool:
        """Valida que el nombre de archivo sea seguro."""
        if not filename:
            return False
        
        if '..' in filename:
            return False
        
        if filename.startswith('/'):
            return False
        
        if filename.startswith('\\'):
            return False
        
        safe_name = secure_filename(filename)
        return safe_name == filename and safe_name != ''

    def _sanitize_path(self, base_path: Path, user_path: str) -> Optional[Path]:
        """Sanitiza y valida una ruta de archivo."""
        try:
            full_path = (base_path / user_path).resolve()
            
            if not str(full_path).startswith(str(base_path.resolve())):
                self.logger.warning(f"Path traversal attempt detected: {user_path}")
                return None
            
            return full_path
        except Exception as e:
            self.logger.error(f"Error validating path: {e}")
            return None

    def _setup_error_handlers(self) -> None:
        """Configura manejadores de errores."""
        
        @self.app.errorhandler(400)
        def bad_request(error):
            return jsonify({'error': 'Solicitud inválida'}), 400

        @self.app.errorhandler(403)
        def forbidden(error):
            return jsonify({'error': 'Acceso denegado'}), 403

        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': 'Recurso no encontrado'}), 404

        @self.app.errorhandler(429)
        def rate_limit_exceeded(error):
            return jsonify({'error': 'Demasiadas solicitudes'}), 429

        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({'error': 'Error interno del servidor'}), 500

    def _setup_routes(self) -> None:
        """Configura las rutas de la API REST."""

        @self.app.before_request
        def check_rate_limit():
            """Verifica rate limiting antes de cada solicitud."""
            client_id = request.remote_addr
            
            if not self._check_rate_limit(client_id):
                abort(429)

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
                self.logger.error(f"Error iniciando bot: {e}")
                return jsonify({'success': False, 'message': 'Error interno'}), 500

        @self.app.route('/api/stop', methods=['POST'])
        def stop_bot():
            """Detiene el bot."""
            try:
                if self.bot.running:
                    self.bot.stop()
                    return jsonify({'success': True, 'message': 'Bot detenido'})
                return jsonify({'success': False, 'message': 'Bot no está en ejecución'})
            except Exception as e:
                self.logger.error(f"Error deteniendo bot: {e}")
                return jsonify({'success': False, 'message': 'Error interno'}), 500

        @self.app.route('/api/config', methods=['GET'])
        def get_config():
            """Obtiene la configuración actual (sanitizada)."""
            safe_config = self._sanitize_config(self.bot.config)
            return jsonify(safe_config)

        @self.app.route('/api/config', methods=['POST'])
        def update_config():
            """Actualiza la configuración."""
            try:
                new_config = request.json
                
                if not new_config or not isinstance(new_config, dict):
                    return jsonify({'success': False, 'message': 'Configuración inválida'}), 400
                
                if not self._validate_config(new_config):
                    return jsonify({'success': False, 'message': 'Configuración contiene valores no permitidos'}), 400
                
                self.bot.config.update(new_config)
                return jsonify({'success': True, 'message': 'Configuración actualizada'})
            except Exception as e:
                self.logger.error(f"Error actualizando configuración: {e}")
                return jsonify({'success': False, 'message': 'Error interno'}), 500

        @self.app.route('/api/servers', methods=['GET'])
        def get_servers():
            """Obtiene lista de servidores encontrados."""
            if self.bot.scanner:
                servers = []
                for server in self.bot.scanner.get_servers():
                    servers.append({
                        'name': self._sanitize_string(server.name),
                        'address': self._sanitize_string(server.address),
                        'port': server.port,
                        'players': server.players,
                        'max_players': server.max_players,
                        'country': self._sanitize_string(server.country),
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
                        'game_name': self._sanitize_string(session.game_name),
                        'server_name': self._sanitize_string(session.server.name),
                        'players': [self._sanitize_string(p) for p in session.players],
                        'max_players': session.max_players,
                        'status': self._sanitize_string(session.status)
                    })
                return jsonify(sessions)
            return jsonify([])

        @self.app.route('/api/recordings', methods=['GET'])
        def get_recordings():
            """Obtiene lista de grabaciones."""
            recordings = {'videos': [], 'inputs': [], 'network': []}
            output_dir = Path(self.bot.config['recording']['output_directory'])

            for category in self.security.ALLOWED_CATEGORIES:
                category_dir = output_dir / category
                if category_dir.exists() and category_dir.is_dir():
                    try:
                        for file in category_dir.glob('*'):
                            if file.is_file():
                                stat = file.stat()
                                if stat.st_size <= self.security.MAX_FILE_SIZE:
                                    recordings[category].append({
                                        'name': file.name,
                                        'size': stat.st_size,
                                        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                                        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                                    })
                    except Exception as e:
                        self.logger.error(f"Error listando grabaciones en {category}: {e}")

            return jsonify(recordings)

        @self.app.route('/api/recordings/<category>/<filename>', methods=['GET'])
        def download_recording(category: str, filename: str):
            """Descarga una grabación de forma segura."""
            if not self._validate_category(category):
                abort(403)
            
            if not self._validate_filename(filename):
                abort(403)
            
            output_dir = Path(self.bot.config['recording']['output_directory'])
            category_dir = output_dir / category
            
            safe_path = self._sanitize_path(category_dir, filename)
            if not safe_path:
                abort(403)
            
            if not safe_path.exists() or not safe_path.is_file():
                abort(404)
            
            try:
                return send_from_directory(str(category_dir), filename, as_attachment=True)
            except Exception as e:
                self.logger.error(f"Error descargando archivo: {e}")
                abort(500)

        @self.app.route('/api/recordings/<category>/<filename>', methods=['DELETE'])
        def delete_recording(category: str, filename: str):
            """Elimina una grabación de forma segura."""
            if not self._validate_category(category):
                abort(403)
            
            if not self._validate_filename(filename):
                abort(403)
            
            try:
                output_dir = Path(self.bot.config['recording']['output_directory'])
                file_path = output_dir / category / filename
                
                safe_path = self._sanitize_path(output_dir / category, filename)
                if not safe_path:
                    abort(403)
                
                if safe_path.exists() and safe_path.is_file():
                    safe_path.unlink()
                    return jsonify({'success': True, 'message': 'Grabación eliminada'})
                return jsonify({'success': False, 'message': 'Archivo no encontrado'}), 404
            except Exception as e:
                self.logger.error(f"Error eliminando archivo: {e}")
                return jsonify({'success': False, 'message': 'Error interno'}), 500

        @self.app.route('/api/logs', methods=['GET'])
        def get_logs():
            """Obtiene las últimas líneas del log de forma segura."""
            log_file = self.bot.config.get('logging', {}).get('file', 'logs/kaillera_bot.log')
            lines = request.args.get('lines', 100, type=int)
            
            lines = max(1, min(lines, self.security.MAX_LOG_LINES))
            
            log_path = Path(log_file)
            if not log_path.exists():
                return jsonify({'lines': []})
            
            if not self._is_safe_path(log_path):
                abort(403)
            
            try:
                with open(log_path, 'r', encoding='utf-8') as f:
                    all_lines = f.readlines()
                    last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    sanitized_lines = [self._sanitize_string(line.strip()) for line in last_lines]
                    return jsonify({'lines': sanitized_lines})
            except FileNotFoundError:
                return jsonify({'lines': []})
            except Exception as e:
                self.logger.error(f"Error leyendo logs: {e}")
                return jsonify({'error': 'Error interno'}), 500

    def _sanitize_config(self, config: dict) -> dict:
        """Sanitiza la configuración antes de enviarla."""
        safe_config = config.copy()
        
        sensitive_keys = ['password', 'secret', 'token', 'api_key', 'credential']
        for key in sensitive_keys:
            if key in safe_config:
                safe_config[key] = '***REDACTED***'
        
        return safe_config

    def _validate_config(self, config: dict) -> bool:
        """Valida que la configuración sea segura."""
        dangerous_paths = ['/etc/', '/root/', 'C:\\Windows\\', '~']
        
        def check_dict(d):
            for key, value in d.items():
                if isinstance(value, dict):
                    if not check_dict(value):
                        return False
                elif isinstance(value, str):
                    for dangerous in dangerous_paths:
                        if dangerous in value:
                            return False
            return True
        
        return check_dict(config)

    def _sanitize_string(self, text: Optional[str]) -> Optional[str]:
        """Sanitiza un string para prevenir XSS."""
        if text is None:
            return None
        
        if not isinstance(text, str):
            text = str(text)
        
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        text = text.replace('&', '&amp;')
        text = text.replace('"', '&quot;')
        text = text.replace("'", '&#x27;')
        
        return text

    def _is_safe_path(self, path: Path) -> bool:
        """Verifica que una ruta sea segura."""
        try:
            resolved = path.resolve()
            
            if resolved.is_symlink():
                return False
            
            return True
        except Exception:
            return False

    def _setup_socketio(self) -> None:
        """Configura los eventos de SocketIO."""

        @self.socketio.on('connect')
        def handle_connect():
            """Cliente conectado."""
            self.logger.info(f'Cliente conectado: {request.remote_addr}')
            emit('status_update', self._get_bot_status())

        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Cliente desconectado."""
            self.logger.info(f'Cliente desconectado: {request.remote_addr}')

        @self.socketio.on('request_status')
        def handle_request_status():
            """Solicitud de estado actualizado."""
            emit('status_update', self._get_bot_status())

    def _get_bot_status(self) -> Dict[str, Any]:
        """Obtiene el estado completo del bot."""
        status = {
            'running': self.bot.running,
            'current_session': self._sanitize_string(self.bot.current_session) if self.bot.current_session else None,
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
            status['current_game'] = self._sanitize_string(self.bot.client.get_current_game())
            if self.bot.client.server_address:
                status['server'] = f"{self.bot.client.server_address}:{self.bot.client.server_port}"

        if self.bot.scanner:
            status['scanning'] = self.bot.scanner.scanning
            status['servers_found'] = len(self.bot.scanner.get_servers())
            status['sessions_found'] = len(self.bot.scanner.get_sessions())

        if self.bot.current_session and self.bot.recording_start_time > 0:
            status['recording_duration'] = time.time() - self.bot.recording_start_time

        return status

    def broadcast_status(self) -> None:
        """Envía actualización de estado a todos los clientes conectados."""
        self.socketio.emit('status_update', self._get_bot_status())

    def broadcast_log(self, log_line: str) -> None:
        """Envía una línea de log a todos los clientes."""
        self.socketio.emit('log_update', {'line': self._sanitize_string(log_line)})

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
