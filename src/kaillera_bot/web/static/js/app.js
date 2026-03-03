class KailleraBotUI {
    constructor() {
        this.socket = null;
        this.connected = false;
        this.statusUpdateInterval = null;
        this.currentRecordingType = 'videos';
        this.config = null;
        this.configSchema = null;
        this.originalConfig = null;
        this.currentSection = null;
        
        this.init();
    }

    async init() {
        this.connectWebSocket();
        this.setupEventListeners();
        this.startStatusUpdates();
        await this.loadInitialData();
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
        document.getElementById('btn-start').addEventListener('click', () => this.startBot());
        document.getElementById('btn-stop').addEventListener('click', () => this.stopBot());
        document.getElementById('btn-refresh').addEventListener('click', () => this.refreshAll());

        document.querySelectorAll('#recordings-tabs a').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const type = e.currentTarget.getAttribute('data-type');
                this.loadRecordings(type);
                
                document.querySelectorAll('#recordings-tabs a').forEach(l => l.classList.remove('active'));
                e.currentTarget.classList.add('active');
            });
        });

        document.getElementById('btn-clear-logs').addEventListener('click', () => {
            document.getElementById('logs-container').textContent = '';
        });

        document.getElementById('btn-save-config').addEventListener('click', () => this.saveConfig());
        document.getElementById('btn-reset-config').addEventListener('click', () => this.resetConfig());
        
        document.getElementById('btn-add-server').addEventListener('click', () => this.addServer());
        document.getElementById('btn-add-game').addEventListener('click', () => this.addGame());
    }

    startStatusUpdates() {
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

        const connectionInfo = status.connected 
            ? `${status.server || 'Conectado'}` 
            : 'Desconectado';
        document.getElementById('connection-info').textContent = connectionInfo;

        document.getElementById('current-game').textContent = 
            status.current_game || 'Ninguno';

        const duration = this.formatDuration(status.recording_duration);
        document.getElementById('recording-duration').textContent = duration;

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
            const [configRes, schemaRes] = await Promise.all([
                fetch('/api/config'),
                fetch('/api/config/schema')
            ]);
            
            this.config = await configRes.json();
            this.configSchema = await schemaRes.json();
            this.originalConfig = JSON.parse(JSON.stringify(this.config));
            
            this.renderConfigMenu();
        } catch (error) {
            console.error('Error cargando configuración:', error);
        }
    }

    renderConfigMenu() {
        const menu = document.getElementById('config-menu');
        menu.innerHTML = '';
        
        for (const [sectionKey, sectionData] of Object.entries(this.configSchema)) {
            const item = document.createElement('a');
            item.href = '#';
            item.className = 'list-group-item list-group-item-action d-flex align-items-center';
            item.innerHTML = `<i class="bi ${sectionData.icon} me-2"></i> ${sectionData.label}`;
            item.addEventListener('click', (e) => {
                e.preventDefault();
                document.querySelectorAll('.config-menu .list-group-item').forEach(i => i.classList.remove('active'));
                item.classList.add('active');
                this.renderConfigSection(sectionKey);
            });
            menu.appendChild(item);
        }
    }

    renderConfigSection(sectionKey) {
        this.currentSection = sectionKey;
        const sectionData = this.configSchema[sectionKey];
        const sectionConfig = this.config[sectionKey];
        
        document.getElementById('config-section-title').innerHTML = 
            `<i class="bi ${sectionData.icon}"></i> ${sectionData.label}`;
        
        const container = document.getElementById('config-form-container');
        let html = '';
        
        if (sectionData.fields) {
            html += this.renderFields(sectionKey, sectionData.fields, sectionConfig);
        }
        
        if (sectionData.subsections) {
            for (const [subKey, subData] of Object.entries(sectionData.subsections)) {
                html += `<div class="config-subsection mt-4">
                    <h6 class="border-bottom pb-2 mb-3">${subData.label}</h6>`;
                
                if (subData.type === 'list') {
                    html += this.renderListField(`${sectionKey}.${subKey}`, subData, sectionConfig[subKey] || []);
                } else if (subData.type === 'object') {
                    html += this.renderFields(`${sectionKey}.${subKey}`, subData.fields, sectionConfig[subKey] || {});
                }
                
                html += '</div>';
            }
        }
        
        container.innerHTML = html;
        this.attachConfigListeners(container);
    }

    renderFields(path, fieldsSchema, config) {
        let html = '';
        
        for (const [fieldKey, fieldData] of Object.entries(fieldsSchema)) {
            const fieldPath = `${path}.${fieldKey}`;
            const value = config[fieldKey];
            
            html += `<div class="mb-3">
                <label class="form-label">${fieldData.label}</label>`;
            
            if (fieldData.description) {
                html += `<small class="d-block text-muted mb-1">${fieldData.description}</small>`;
            }
            
            switch (fieldData.type) {
                case 'text':
                    html += `<input type="text" class="form-control" 
                        data-path="${fieldPath}" 
                        value="${this.escapeHtml(value || '')}">`;
                    break;
                    
                case 'number':
                    html += `<input type="number" class="form-control" 
                        data-path="${fieldPath}" 
                        value="${value || 0}"
                        ${fieldData.min !== undefined ? `min="${fieldData.min}"` : ''}
                        ${fieldData.max !== undefined ? `max="${fieldData.max}"` : ''}>`;
                    break;
                    
                case 'boolean':
                    html += `<div class="form-check form-switch">
                        <input type="checkbox" class="form-check-input" 
                            data-path="${fieldPath}" 
                            ${value ? 'checked' : ''}>
                        <label class="form-check-label">${fieldData.label}</label>
                    </div>`;
                    break;
                    
                case 'select':
                    html += `<select class="form-select" data-path="${fieldPath}">
                        ${fieldData.options.map(opt => 
                            `<option value="${opt}" ${value === opt ? 'selected' : ''}>${opt}</option>`
                        ).join('')}
                    </select>`;
                    break;
            }
            
            html += '</div>';
        }
        
        return html;
    }

    renderListField(path, listSchema, items) {
        let html = '';
        
        if (listSchema.item_fields) {
            html += `<div class="list-items" data-list-path="${path}">`;
            
            items.forEach((item, index) => {
                html += `<div class="card mb-2 list-item" data-index="${index}">
                    <div class="card-body py-2">
                        <div class="row align-items-center">`;
                
                for (const [fieldKey, fieldData] of Object.entries(listSchema.item_fields)) {
                    const fieldPath = `${path}[${index}].${fieldKey}`;
                    const colSize = Math.floor(12 / Object.keys(listSchema.item_fields).length);
                    
                    html += `<div class="col-${colSize}">`;
                    
                    if (fieldData.type === 'text') {
                        html += `<input type="text" class="form-control form-control-sm" 
                            data-path="${fieldPath}" 
                            placeholder="${fieldData.label}"
                            value="${this.escapeHtml(item[fieldKey] || '')}">`;
                    } else if (fieldData.type === 'number') {
                        html += `<input type="number" class="form-control form-control-sm" 
                            data-path="${fieldPath}" 
                            placeholder="${fieldData.label}"
                            value="${item[fieldKey] || 0}"
                            ${fieldData.min !== undefined ? `min="${fieldData.min}"` : ''}
                            ${fieldData.max !== undefined ? `max="${fieldData.max}"` : ''}>`;
                    }
                    
                    html += '</div>';
                }
                
                html += `<div class="col-auto">
                    <button type="button" class="btn btn-outline-danger btn-sm btn-remove-item" data-path="${path}" data-index="${index}">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>`;
                
                html += `</div></div></div>`;
            });
            
            html += '</div>';
            
            if (path.includes('servers')) {
                html += `<button type="button" class="btn btn-outline-primary btn-sm" data-bs-toggle="modal" data-bs-target="#addServerModal">
                    <i class="bi bi-plus"></i> Agregar Servidor
                </button>`;
            } else if (path.includes('games')) {
                html += `<button type="button" class="btn btn-outline-primary btn-sm" data-bs-toggle="modal" data-bs-target="#addGameModal">
                    <i class="bi bi-plus"></i> Agregar Juego
                </button>`;
            }
        } else if (listSchema.item_type === 'text') {
            html += `<div class="list-items" data-list-path="${path}">`;
            
            items.forEach((item, index) => {
                html += `<div class="input-group mb-2 list-item" data-index="${index}">
                    <input type="text" class="form-control" 
                        data-path="${path}[${index}]" 
                        value="${this.escapeHtml(item || '')}">
                    <button type="button" class="btn btn-outline-danger btn-remove-item" data-path="${path}" data-index="${index}">
                        <i class="bi bi-trash"></i>
                    </button>
                </div>`;
            });
            
            html += '</div>';
            
            html += `<button type="button" class="btn btn-outline-primary btn-sm btn-add-simple-item" data-path="${path}">
                <i class="bi bi-plus"></i> Agregar
            </button>`;
        }
        
        return html;
    }

    attachConfigListeners(container) {
        container.querySelectorAll('input, select').forEach(input => {
            input.addEventListener('change', () => this.updateConfigValue(input));
            if (input.type === 'text' || input.type === 'number') {
                input.addEventListener('input', () => this.updateConfigValue(input));
            }
        });
        
        container.querySelectorAll('.btn-remove-item').forEach(btn => {
            btn.addEventListener('click', () => {
                const path = btn.dataset.path;
                const index = parseInt(btn.dataset.index);
                this.removeListItem(path, index);
            });
        });
        
        container.querySelectorAll('.btn-add-simple-item').forEach(btn => {
            btn.addEventListener('click', () => {
                const path = btn.dataset.path;
                this.addSimpleListItem(path);
            });
        });
    }

    updateConfigValue(input) {
        const path = input.dataset.path;
        let value;
        
        if (input.type === 'checkbox') {
            value = input.checked;
        } else if (input.type === 'number') {
            value = parseFloat(input.value);
        } else {
            value = input.value;
        }
        
        this.setNestedValue(this.config, path, value);
    }

    setNestedValue(obj, path, value) {
        const parts = path.replace(/\[(\d+)\]/g, '.$1').split('.');
        let current = obj;
        
        for (let i = 0; i < parts.length - 1; i++) {
            const part = parts[i];
            if (!current[part]) {
                current[part] = isNaN(parts[i + 1]) ? {} : [];
            }
            current = current[part];
        }
        
        current[parts[parts.length - 1]] = value;
    }

    getNestedValue(obj, path) {
        const parts = path.replace(/\[(\d+)\]/g, '.$1').split('.');
        let current = obj;
        
        for (const part of parts) {
            if (current === undefined || current === null) return undefined;
            current = current[part];
        }
        
        return current;
    }

    removeListItem(path, index) {
        const list = this.getNestedValue(this.config, path);
        if (Array.isArray(list)) {
            list.splice(index, 1);
            this.renderConfigSection(this.currentSection);
        }
    }

    addSimpleListItem(path) {
        const list = this.getNestedValue(this.config, path) || [];
        if (!Array.isArray(this.getNestedValue(this.config, path))) {
            this.setNestedValue(this.config, path, list);
        }
        list.push('');
        this.renderConfigSection(this.currentSection);
    }

    addServer() {
        const name = document.getElementById('new-server-name').value.trim();
        const address = document.getElementById('new-server-address').value.trim();
        const port = parseInt(document.getElementById('new-server-port').value) || 27888;
        
        if (!name || !address) {
            this.showNotification('Nombre y dirección son requeridos', 'warning');
            return;
        }
        
        if (!this.config.kaillera.servers) {
            this.config.kaillera.servers = [];
        }
        
        this.config.kaillera.servers.push({ name, address, port });
        
        bootstrap.Modal.getInstance(document.getElementById('addServerModal')).hide();
        document.getElementById('new-server-name').value = '';
        document.getElementById('new-server-address').value = '';
        document.getElementById('new-server-port').value = '27888';
        
        if (this.currentSection === 'kaillera') {
            this.renderConfigSection('kaillera');
        }
        
        this.showNotification('Servidor agregado', 'success');
    }

    addGame() {
        const name = document.getElementById('new-game-name').value.trim();
        
        if (!name) {
            this.showNotification('El nombre del juego es requerido', 'warning');
            return;
        }
        
        if (!this.config.kaillera.filters.games) {
            this.config.kaillera.filters.games = [];
        }
        
        this.config.kaillera.filters.games.push(name);
        
        bootstrap.Modal.getInstance(document.getElementById('addGameModal')).hide();
        document.getElementById('new-game-name').value = '';
        
        if (this.currentSection === 'kaillera') {
            this.renderConfigSection('kaillera');
        }
        
        this.showNotification('Juego agregado', 'success');
    }

    async saveConfig() {
        try {
            const response = await fetch('/api/config/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(this.config)
            });
            const data = await response.json();
            
            if (data.success) {
                this.originalConfig = JSON.parse(JSON.stringify(this.config));
                this.showNotification(data.message, 'success');
            } else {
                this.showNotification(data.message, 'danger');
            }
        } catch (error) {
            this.showNotification('Error al guardar: ' + error.message, 'danger');
        }
    }

    resetConfig() {
        if (confirm('¿Estás seguro de resetear los cambios? Se perderán todas las modificaciones no guardadas.')) {
            this.config = JSON.parse(JSON.stringify(this.originalConfig));
            if (this.currentSection) {
                this.renderConfigSection(this.currentSection);
            }
            this.showNotification('Configuración reseteada', 'info');
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
        const toast = document.createElement('div');
        toast.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }
}

const ui = new KailleraBotUI();
