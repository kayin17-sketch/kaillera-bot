// Kaillera Bot Web Interface
class KailleraBotUI {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.statusUpdateInterval = null;
        this.currentRecordingType = 'videos';
        
        this.init();
    }

    init() {
        this.connectWebSocket();
        this.setupEventListeners();
        this.startStatusUpdates();
        this.loadInitialData();
    }

    connectWebSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Conectado al servidor WebSocket');
            this.connected = true;
            this.updateConnectionStatus(true);
        });

        this.socket.on('disconnect', () => {
            console.log('Desconectado del servidor WebSocket');
            this.connected = false;
            this.updateConnectionStatus(false);
        });

        this.socket.on('status_update', (data) => {
            this.updateStatus(data);
        });

        this.socket.on('log_update', (data) => {
            this.appendLog(data.line);
        });
    }

    updateConnectionStatus(connected) {
        const statusEl = document.getElementById('connection-status');
        if (connected) {
            statusEl.innerHTML = '<i class="bi bi-circle-fill text-success"></i> Conectado';
            statusEl.classList.add('connected');
            statusEl.classList.remove('disconnected');
        } else {
            statusEl.innerHTML = '<i class="bi bi-circle-fill text-danger"></i> Desconectado';
            statusEl.classList.add('disconnected');
            statusEl.classList.remove('connected');
        }
    }

    setupEventListeners() {
        // Botones de control
        document.getElementById('btn-start').addEventListener('click', () => this.startBot());
        document.getElementById('btn-stop').addEventListener('click', () => this.stopBot());
        document.getElementById('btn-refresh').addEventListener('click', () => this.refreshAll());

        // Tabs de grabaciones
        document.querySelectorAll('#recordings-tabs a').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const type = e.currentTarget.getAttribute('data-type');
                this.loadRecordings(type);
                
                document.querySelectorAll('#recordings-tabs a').forEach(l => l.classList.remove('active'));
                e.currentTarget.classList.add('active');
            });
        });

        // Limpiar logs
        document.getElementById('btn-clear-logs').addEventListener('click', () => {
            document.getElementById('logs-container').textContent = '';
        });

        // Guardar configuración
        document.getElementById('btn-save-config').addEventListener('click', () => this.saveConfig());
    }

    startStatusUpdates() {
        // Solicitar actualización de estado cada 2 segundos
        this.statusUpdateInterval = setInterval(() => {
            if (this.connected) {
                this.socket.emit('request_status');
            }
        }, 2000);
    }

    async loadInitialData() {
        await Promise.all([
            this.loadServers(),
            this.loadSessions(),
            this.loadRecordings('videos'),
            this.loadConfig(),
            this.loadLogs()
        ]);
    }

    async refreshAll() {
        await this.loadInitialData();
        this.showNotification('Datos actualizados', 'success');
    }

    updateStatus(status) {
        // Estado del bot
        const botStatusEl = document.getElementById('bot-status');
        if (status.running) {
            botStatusEl.innerHTML = '<span class="badge bg-success">Ejecutando</span>';
            document.getElementById('btn-start').disabled = true;
            document.getElementById('btn-stop').disabled = false;
        } else {
            botStatusEl.innerHTML = '<span class="badge bg-secondary">Detenido</span>';
            document.getElementById('btn-start').disabled = false;
            document.getElementById('btn-stop').disabled = true;
        }

        // Conexión
        const connectionInfo = status.connected 
            ? `${status.server || 'Conectado'}` 
            : 'Desconectado';
        document.getElementById('connection-info').textContent = connectionInfo;

        // Juego actual
        document.getElementById('current-game').textContent = 
            status.current_game || 'Ninguno';

        // Duración
        const duration = this.formatDuration(status.recording_duration);
        document.getElementById('recording-duration').textContent = duration;

        // Grabaciones activas
        this.updateRecordingStatus(status.recordings);
    }

    updateRecordingStatus(recordings) {
        const html = `
            <span class="badge ${recordings.video ? 'bg-success' : 'bg-secondary'} me-2">
                Video: <i class="bi bi-${recordings.video ? 'check-circle' : 'x-circle'}"></i>
            </span>
            <span class="badge ${recordings.inputs ? 'bg-success' : 'bg-secondary'} me-2">
                Inputs: <i class="bi bi-${recordings.inputs ? 'check-circle' : 'x-circle'}"></i>
            </span>
            <span class="badge ${recordings.network ? 'bg-success' : 'bg-secondary'}">
                Network: <i class="bi bi-${recordings.network ? 'check-circle' : 'x-circle'}"></i>
            </span>
        `;
        document.getElementById('active-recordings').innerHTML = html;
    }

    formatDuration(seconds) {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);
        return `${h.toString().padStart(2, '0')}:${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
    }

    async startBot() {
        try {
            const response = await fetch('/api/start', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message, 'success');
            } else {
                this.showNotification(data.message, 'warning');
            }
        } catch (error) {
            this.showNotification('Error al iniciar el bot: ' + error.message, 'danger');
        }
    }

    async stopBot() {
        try {
            const response = await fetch('/api/stop', { method: 'POST' });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(data.message, 'success');
            } else {
                this.showNotification(data.message, 'warning');
            }
        } catch (error) {
            this.showNotification('Error al detener el bot: ' + error.message, 'danger');
        }
    }

    async loadServers() {
        try {
            const response = await fetch('/api/servers');
            const servers = await response.json();
            
            const tbody = document.getElementById('servers-table');
            
            if (servers.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="5" class="text-center text-muted">
                            No se encontraron servidores
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = servers.map(server => `
                <tr>
                    <td>${this.escapeHtml(server.name)}</td>
                    <td><code>${server.address}:${server.port}</code></td>
                    <td>
                        <span class="badge bg-primary">${server.players}/${server.max_players}</span>
                    </td>
                    <td>${this.escapeHtml(server.country)}</td>
                    <td>${server.ping > 0 ? server.ping + ' ms' : '-'}</td>
                </tr>
            `).join('');
        } catch (error) {
            console.error('Error cargando servidores:', error);
        }
    }

    async loadSessions() {
        try {
            const response = await fetch('/api/sessions');
            const sessions = await response.json();
            
            const tbody = document.getElementById('sessions-table');
            
            if (sessions.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center text-muted">
                            No se encontraron partidas
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = sessions.map(session => `
                <tr>
                    <td>${this.escapeHtml(session.game_name)}</td>
                    <td>${this.escapeHtml(session.server_name)}</td>
                    <td>
                        <span class="badge bg-info">${session.players.length}/${session.max_players}</span>
                    </td>
                    <td>
                        <span class="badge ${session.status === 'Waiting' ? 'bg-warning' : 'bg-success'}">
                            ${this.escapeHtml(session.status)}
                        </span>
                    </td>
                </tr>
            `).join('');
        } catch (error) {
            console.error('Error cargando sesiones:', error);
        }
    }

    async loadRecordings(type) {
        this.currentRecordingType = type;
        
        try {
            const response = await fetch('/api/recordings');
            const recordings = await response.json();
            const items = recordings[type] || [];
            
            const tbody = document.getElementById('recordings-table');
            
            if (items.length === 0) {
                tbody.innerHTML = `
                    <tr>
                        <td colspan="4" class="text-center text-muted">
                            No hay grabaciones de este tipo
                        </td>
                    </tr>
                `;
                return;
            }

            tbody.innerHTML = items.map(item => `
                <tr>
                    <td>${this.escapeHtml(item.name)}</td>
                    <td>${this.formatSize(item.size)}</td>
                    <td>${new Date(item.created).toLocaleString()}</td>
                    <td>
                        <a href="/api/recordings/${type}/${encodeURIComponent(item.name)}" 
                           class="btn btn-sm btn-primary" download>
                            <i class="bi bi-download"></i>
                        </a>
                        <button class="btn btn-sm btn-danger" 
                                onclick="ui.deleteRecording('${type}', '${this.escapeHtml(item.name)}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </td>
                </tr>
            `).join('');
        } catch (error) {
            console.error('Error cargando grabaciones:', error);
        }
    }

    async deleteRecording(type, filename) {
        if (!confirm(`¿Estás seguro de eliminar ${filename}?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/recordings/${type}/${encodeURIComponent(filename)}`, {
                method: 'DELETE'
            });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Grabación eliminada', 'success');
                this.loadRecordings(type);
            } else {
                this.showNotification(data.message, 'danger');
            }
        } catch (error) {
            this.showNotification('Error al eliminar: ' + error.message, 'danger');
        }
    }

    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            const config = await response.json();
            
            const configDisplay = document.getElementById('config-display');
            configDisplay.textContent = JSON.stringify(config, null, 2);
        } catch (error) {
            console.error('Error cargando configuración:', error);
        }
    }

    async saveConfig() {
        try {
            const configText = document.getElementById('config-display').textContent;
            const config = JSON.parse(configText);
            
            const response = await fetch('/api/config', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
            const data = await response.json();
            
            if (data.success) {
                this.showNotification('Configuración guardada', 'success');
            } else {
                this.showNotification(data.message, 'danger');
            }
        } catch (error) {
            this.showNotification('Error al guardar: ' + error.message, 'danger');
        }
    }

    async loadLogs() {
        try {
            const response = await fetch('/api/logs?lines=100');
            const data = await response.json();
            
            const logsContainer = document.getElementById('logs-container');
            logsContainer.textContent = data.lines.join('\n');
            logsContainer.scrollTop = logsContainer.scrollHeight;
        } catch (error) {
            console.error('Error cargando logs:', error);
        }
    }

    appendLog(line) {
        const logsContainer = document.getElementById('logs-container');
        logsContainer.textContent += '\n' + line;
        
        // Auto-scroll si está al final
        if (logsContainer.scrollHeight - logsContainer.scrollTop === logsContainer.clientHeight) {
            logsContainer.scrollTop = logsContainer.scrollHeight;
        }
    }

    formatSize(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + ' KB';
        if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
        return (bytes / (1024 * 1024 * 1024)).toFixed(2) + ' GB';
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    showNotification(message, type = 'info') {
        // Crear notificación toast
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        
        // Auto-remover después de 3 segundos
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

// Inicializar UI
const ui = new KailleraBotUI();
