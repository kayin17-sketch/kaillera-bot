# Interfaz Web - Guía Completa

## 🌐 Acceso a la Interfaz Web

El bot incluye una **interfaz web completa** accesible desde cualquier dispositivo en tu red local.

---

## 🚀 Iniciar la Interfaz Web

### Opción 1: Comando Dedicado

```bash
kaillera-bot-web
```

### Opción 2: Con Python

```bash
python -m kaillera_bot.main --web
```

### Opción 3: Con opciones personalizadas

```bash
kaillera-bot-web --host 0.0.0.0 --port 8080 --no-bot
```

---

## 📋 Opciones Disponibles

| Opción | Descripción | Por defecto |
|--------|-------------|-------------|
| `--host` | Host para la interfaz web | `0.0.0.0` (todas las interfaces) |
| `--port` | Puerto para la interfaz web | `5000` |
| `--no-bot` | No iniciar el bot automáticamente | Desactivado |
| `--config` | Ruta al archivo de configuración | `config/settings.yaml` |

---

## 🌐 URLs de Acceso

Una vez iniciado, la interfaz estará disponible en:

### Desde el mismo equipo:
```
http://localhost:5000
```

### Desde otro dispositivo en la red local:
```
http://<IP-LOCAL>:5000
```

**Ejemplo**: Si tu IP local es `192.168.1.100`:
```
http://192.168.1.100:5000
```

---

## 🎮 Funcionalidades

### 1. **Panel de Control Principal**
- Estado del bot en tiempo real
- Información de conexión
- Juego actual
- Duración de la grabación
- Grabaciones activas (video, inputs, red)

### 2. **Control del Bot**
- ✅ Iniciar/Detener el bot
- 🔄 Actualizar datos manualmente
- 📊 Ver estado de grabaciones en vivo

### 3. **Servidores Kaillera**
- Lista de servidores encontrados
- Jugadores conectados
- País y ping
- Estado de cada servidor

### 4. **Partidas Activas**
- Lista de partidas disponibles
- Juego, servidor y jugadores
- Estado de cada partida

### 5. **Grabaciones**
- **Videos**: Ver, descargar y eliminar videos MP4
- **Inputs**: Ver y descargar archivos JSON de inputs
- **Red**: Ver y descargar archivos JSON de datos de red

### 6. **Logs en Tiempo Real**
- Ver logs del sistema en vivo
- Auto-scroll
- Coloreado por nivel (INFO, WARNING, ERROR, DEBUG)
- Limpiar logs

### 7. **Configuración**
- Ver configuración actual
- Editar configuración en vivo
- Guardar cambios

---

## 🎯 API REST

La interfaz web expone una API REST completa:

### Estado y Control

```bash
# Obtener estado del bot
GET /api/status

# Iniciar bot
POST /api/start

# Detener bot
POST /api/stop
```

### Servidores y Partidas

```bash
# Lista de servidores
GET /api/servers

# Lista de partidas
GET /api/sessions
```

### Grabaciones

```bash
# Lista de grabaciones
GET /api/recordings

# Descargar grabación
GET /api/recordings/<categoria>/<archivo>

# Eliminar grabación
DELETE /api/recordings/<categoria>/<archivo>
```

### Configuración

```bash
# Ver configuración
GET /api/config

# Actualizar configuración
POST /api/config
```

### Logs

```bash
# Obtener logs (últimas 100 líneas)
GET /api/logs?lines=100
```

---

## 📡 WebSocket

La interfaz usa **WebSocket** para actualizaciones en tiempo real:

### Eventos del Cliente

```javascript
// Solicitar actualización de estado
socket.emit('request_status');
```

### Eventos del Servidor

```javascript
// Actualización de estado
socket.on('status_update', (data) => {
    // data contiene el estado completo del bot
});

// Nueva línea de log
socket.on('log_update', (data) => {
    // data.line contiene la línea de log
});
```

---

## 🎨 Interfaz de Usuario

### Diseño
- ✅ Bootstrap 5 responsive
- ✅ Iconos Bootstrap Icons
- ✅ Tema oscuro/claro automático
- ✅ Compatible con móviles y tablets

### Características
- ✅ Actualizaciones en tiempo real (cada 2 segundos)
- ✅ Notificaciones toast
- ✅ Auto-scroll en logs
- ✅ Descarga directa de archivos
- ✅ Confirmación antes de eliminar

---

## 🔒 Seguridad

### Acceso Local Solamente
Por defecto, la interfaz solo es accesible desde la **red local**.

### Recomendaciones:
- ✅ Usar solo en redes de confianza
- ✅ Cambiar puerto si es necesario
- ✅ No exponer a internet sin autenticación
- ⚠️ NO tiene autenticación por defecto

### Para agregar autenticación (avanzado):
```python
# En server.py, agregar:
from flask_httpauth import HTTPBasicAuth

auth = HTTPBasicAuth()

@auth.verify_password
def verify_password(username, password):
    # Implementar verificación
    pass
```

---

## 📱 Uso desde Móvil/Tablet

La interfaz es **100% responsive** y funciona perfectamente en:
- 📱 Smartphones
- 📱 Tablets
- 💻 Laptops
- 🖥️ Desktop

### Vista en móvil:
- Menú colapsable
- Tarjetas apiladas verticalmente
- Botones adaptados al tacto

---

## 🔧 Configuración Avanzada

### Cambiar Puerto

```bash
kaillera-bot-web --port 8080
```

### Solo Interfaz (sin bot)

```bash
kaillera-bot-web --no-bot
```

Útil para:
- Ver grabaciones existentes
- Revisar configuración
- Ver logs históricos

### Bind a IP Específica

```bash
kaillera-bot-web --host 192.168.1.100
```

---

## 🐛 Solución de Problemas

### Puerto en uso

**Error**: `Address already in use`

**Solución**:
```bash
# Usar otro puerto
kaillera-bot-web --port 8080
```

### No accesible desde otros dispositivos

**Causas**:
1. Firewall bloqueando el puerto
2. Host configurado como `localhost` o `127.0.0.1`

**Soluciones**:
```bash
# Verificar que usa 0.0.0.0
kaillera-bot-web --host 0.0.0.0

# Abrir puerto en firewall (Linux)
sudo ufw allow 5000

# Abrir puerto en firewall (Windows)
# Panel de Control > Firewall > Reglas de entrada
```

### Dependencias no instaladas

**Error**: `ModuleNotFoundError: No module named 'flask'`

**Solución**:
```bash
pip install -e .
```

### WebSocket no conecta

**Síntomas**: Estado no se actualiza, logs no aparecen

**Solución**:
1. Verificar que no hay proxy/reverse proxy
2. Usar `http://` no `https://`
3. Deshabilitar adblocker

---

## 📊 Monitoreo

### Ver recursos en uso:

```bash
# Linux
top -p $(pgrep -f kaillera-bot-web)

# Windows
# Task Manager > Python
```

### Ver conexiones activas:

```bash
# Linux
sudo netstat -tnp | grep :5000

# Windows
netstat -ano | findstr :5000
```

---

## 🚀 Producción

### Para uso 24/7:

#### Con systemd (Linux):

```ini
# /etc/systemd/system/kaillera-bot-web.service
[Unit]
Description=Kaillera Bot Web Interface
After=network.target

[Service]
Type=simple
User=tu-usuario
WorkingDirectory=/path/to/kaillera-bot
ExecStart=/usr/bin/python3 -m kaillera_bot.main --web
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable kaillera-bot-web
sudo systemctl start kaillera-bot-web
```

#### Con nohup:

```bash
nohup kaillera-bot-web > /dev/null 2>&1 &
```

---

## 📝 Ejemplos de Uso

### Ejemplo 1: Monitoreo desde el sofá

1. Iniciar bot en PC: `kaillera-bot-web`
2. Abrir en tablet: `http://192.168.1.100:5000`
3. Monitorear partidas y grabaciones
4. Descargar videos desde la tablet

### Ejemplo 2: Control remoto

1. Iniciar solo interfaz: `kaillera-bot-web --no-bot`
2. Acceder desde móvil
3. Iniciar bot cuando haya partida interesante
4. Detener cuando termine

### Ejemplo 3: Revisión de grabaciones

1. Abrir pestaña "Grabaciones"
2. Ver lista de videos
3. Descargar los interesantes
4. Eliminar los que no sirven

---

## 🎯 Próximas Funcionalidades (Roadmap)

- [ ] Autenticación con usuario/contraseña
- [ ] HTTPS soporte
- [ ] Tema oscuro/claro manual
- [ ] Estadísticas avanzadas
- [ ] Exportar/importar configuración
- [ ] Reproducir videos en el navegador
- [ ] Visualizar inputs en tiempo real
- [ ] Notificaciones push
- [ ] Multi-idioma

---

## 📞 Soporte

Si tienes problemas:

1. Verificar que las dependencias están instaladas
2. Revisar logs en `logs/kaillera_bot.log`
3. Verificar que el puerto no está en uso
4. Comprobar configuración de firewall

Abrir issue: https://github.com/kayin17-sketch/kaillera-bot/issues

---

## ✅ Checklist

Antes de usar la interfaz web:

- [ ] Instalar dependencias: `pip install -e .`
- [ ] Configurar `config/settings.yaml`
- [ ] Verificar que el puerto 5000 está libre
- [ ] Conocer tu IP local (para acceder desde otros dispositivos)
- [ ] Tener firewall configurado (si es necesario)

---

## 🎉 Disfruta

La interfaz web hace que controlar el bot sea **fácil e intuitivo** desde cualquier dispositivo en tu red local. ¡Disfruta grabando partidas!
