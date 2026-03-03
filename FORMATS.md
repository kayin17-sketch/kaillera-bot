# Formatos de Grabación

El bot soporta **3 tipos de grabaciones** con diferentes formatos:

---

## 📹 **1. Video de la Partida**

### Formato Principal: **MP4**

**Extensión**: `.mp4`

**Codecs soportados**:
- `mp4v` (por defecto) - MPEG-4 Video
- `XVID` - Xvid MPEG-4
- `H264` - H.264/AVC
- `MJPG` - Motion JPEG

**Configuración**:
```yaml
recording:
  video:
    enabled: true
    format: "mp4"
    fps: 60           # Frames por segundo (30, 60, 120)
    codec: "mp4v"     # mp4v, XVID, H264, MJPG
    quality: "high"   # low, medium, high
```

**Ejemplo de archivo**:
```
output/videos/Super Smash Bros_20260303_143022.mp4
```

**Características**:
- ✅ Grabación de pantalla del emulador
- ✅ 60 FPS por defecto (configurable)
- ✅ Alta calidad con codec mp4v
- ✅ Compatible con reproductores estándar (VLC, MPV, etc.)

---

## 🎮 **2. Inputs del Juego**

### Formato: **JSON**

**Extensión**: `.json`

**Estructura**:
```json
{
  "player": "KailleraBot",
  "start_time": "2026-03-03T14:30:22.123456",
  "duration": 1847.42,
  "inputs": [
    {
      "type": "keyboard",
      "action": "press",
      "key": "a",
      "timestamp": 0.023
    },
    {
      "type": "keyboard",
      "action": "release",
      "key": "a",
      "timestamp": 0.156
    },
    {
      "type": "mouse",
      "action": "click",
      "button": "Button.left",
      "x": 960,
      "y": 540,
      "timestamp": 2.345
    }
  ]
}
```

**Configuración**:
```yaml
recording:
  inputs:
    enabled: true
    format: "json"  # Actualmente solo JSON implementado
```

**Ejemplo de archivo**:
```
output/inputs/inputs_KailleraBot_20260303_143022.json
```

**Características**:
- ✅ Registra teclas presionadas/liberadas
- ✅ Registra clicks y movimientos de mouse
- ✅ Timestamps precisos (milisegundos)
- ✅ Fácil de procesar y analizar
- ✅ Compatible con herramientas de replay

---

## 🌐 **3. Datos de Red**

### Formato: **JSON**

**Extensión**: `.json`

**Estructura**:
```json
{
  "session_id": "Super Smash Bros_20260303_143022",
  "start_time": "2026-03-03T14:30:22.123456",
  "duration": 1847.42,
  "total_packets": 15234,
  "packet_types": {
    "player_event": 12,
    "game_event": 3,
    "data": 15219
  },
  "packets": [
    {
      "type": "game_event",
      "event_type": "start",
      "game_name": "Super Smash Bros",
      "data": {},
      "timestamp": 0.0,
      "datetime": "2026-03-03T14:30:22.123456"
    },
    {
      "type": "player_event",
      "event_type": "join",
      "player_name": "Player1",
      "player_number": 1,
      "data": {},
      "timestamp": 1.234,
      "datetime": "2026-03-03T14:30:23.357456"
    },
    {
      "type": "data",
      "source": "192.168.1.100",
      "destination": "master.kaillera.com",
      "data": "...",
      "size": 256,
      "timestamp": 2.456,
      "datetime": "2026-03-03T14:30:24.579456"
    }
  ]
}
```

**Configuración**:
```yaml
recording:
  network:
    enabled: true
    format: "json"  # Actualmente solo JSON implementado
```

**Ejemplo de archivo**:
```
output/network/network_data_Super Smash Bros_20260303_143022_20260303_150529.json
```

**Características**:
- ✅ Registra eventos de jugadores (join/leave)
- ✅ Registra eventos del juego (start/end)
- ✅ Registra paquetes de datos
- ✅ Metadata completa (timestamps, contadores)
- ✅ Útil para análisis de red y debugging

---

## 📊 **Resumen de Formatos**

| Tipo | Formato | Extensión | Tamaño Aprox. | Uso |
|---|:---:|:---:|:---:|---|
| **Video** | MP4 (mp4v) | `.mp4` | ~100-500 MB/hora | Visualización |
| **Inputs** | JSON | `.json` | ~1-5 MB/hora | Análisis, replay |
| **Red** | JSON | `.json` | ~5-20 MB/hora | Debugging, análisis |

---

## 📁 **Estructura de Directorios**

```
output/
├── videos/
│   ├── Super Smash Bros_20260303_143022.mp4
│   ├── Mario Kart 64_20260303_160529.mp4
│   └── ...
├── inputs/
│   ├── inputs_KailleraBot_20260303_143022.json
│   ├── inputs_KailleraBot_20260303_160529.json
│   └── ...
└── network/
    ├── network_data_Super Smash Bros_20260303_143022_20260303_150529.json
    ├── network_data_Mario Kart 64_20260303_160529_20260303_172342.json
    └── ...
```

---

## 🎯 **Nomenclatura de Archivos**

### Video
```
{nombre_juego}_{YYYYMMDD}_{HHMMSS}.mp4
```
Ejemplo: `Super Smash Bros_20260303_143022.mp4`

### Inputs
```
inputs_{nombre_player}_{YYYYMMDD}_{HHMMSS}.json
```
Ejemplo: `inputs_KailleraBot_20260303_143022.json`

### Network
```
network_data_{session_id}_{YYYYMMDD}_{HHMMSS}.json
```
Ejemplo: `network_data_Super Smash Bros_20260303_143022_20260303_150529.json`

---

## 🔧 **Configuración Avanzada**

### Calidad de Video

```yaml
recording:
  video:
    quality: "high"  # Afecta bitrate
```

| Calidad | Bitrate | Tamaño | Uso |
|---|---|---|---|
| **low** | ~1 Mbps | ~450 MB/hora | Ahorro de espacio |
| **medium** | ~3 Mbps | ~1.3 GB/hora | Balance |
| **high** | ~5 Mbps | ~2.2 GB/hora | Máxima calidad |

### FPS de Video

```yaml
recording:
  video:
    fps: 60  # 30, 60, 120
```

| FPS | Uso | Nota |
|---|---|---|
| **30** | Partidas casuales | Menos tamaño |
| **60** | Por defecto | Balance |
| **120** | Competitivo | Más fluidez |

---

## 🛠️ **Herramientas Compatibles**

### Video (MP4)
- ✅ VLC Media Player
- ✅ MPV Player
- ✅ Windows Media Player
- ✅ QuickTime
- ✅ FFmpeg

### JSON (Inputs/Network)
- ✅ Cualquier editor de texto
- ✅ Python (json module)
- ✅ JavaScript (JSON.parse)
- ✅ jq (CLI tool)
- ✅ Online JSON viewers

---

## 📈 **Ejemplo de Uso de Datos**

### Analizar Inputs con Python
```python
import json

with open('inputs_KailleraBot_20260303_143022.json', 'r') as f:
    data = json.load(f)

print(f"Duración: {data['duration']:.2f} segundos")
print(f"Total de inputs: {len(data['inputs'])}")

# Contar teclas más usadas
from collections import Counter
keys = [i['key'] for i in data['inputs'] if i['type'] == 'keyboard']
print("Teclas más usadas:", Counter(keys).most_common(5))
```

### Procesar Datos de Red
```python
import json

with open('network_data_...json', 'r') as f:
    data = json.load(f)

print(f"Total de paquetes: {data['total_packets']}")
print(f"Tipos de paquetes: {data['packet_types']}")

# Filtrar eventos de jugadores
player_events = [p for p in data['packets'] if p['type'] == 'player_event']
for event in player_events:
    print(f"{event['event_type']}: {event['player_name']}")
```

---

## 🔍 **Formatos Futuros (No Implementados)**

Actualmente en la configuración se mencionan pero **no están implementados**:

- ❌ **Inputs en CSV**: `format: "csv"`
- ❌ **Network en PCAP**: `format: "pcap"`

Si necesitas estos formatos, se pueden implementar fácilmente.

---

## ✅ **Checklist**

Antes de grabar:

- [ ] Verificar espacio en disco (~3 GB/hora para todo)
- [ ] Configurar calidad de video según necesidades
- [ ] Ajustar FPS (30/60/120)
- [ ] Habilitar/deshabilitar tipos de grabación
- [ ] Verificar permisos de escritura en `output/`

---

## 📞 **Soporte**

Si necesitas:
- Otros formatos de video (AVI, MKV)
- Formato CSV para inputs
- Formato PCAP para red
- Compresión automática

Abre un issue en GitHub: https://github.com/kayin17-sketch/kaillera-bot/issues
