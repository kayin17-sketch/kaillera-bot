# Guía de Debugging y Solución de Problemas

## Errores Comunes y Soluciones

### 1. Error: "Socket no inicializado"

**Causa**: Intentando usar el cliente Kaillera antes de conectar.

**Solución**:
```python
# Verificar conexión antes de usar
if client.is_connected():
    client.join_game("game_name")
```

### 2. Error: "Área de captura no configurada"

**Causa**: El grabador de video no tiene definida el área de captura.

**Solución**:
```python
# Detectar ventana automáticamente
video_recorder.auto_detect_emulator_window("Rosalie's Mupen GUI")

# O configurar manualmente
video_recorder.set_capture_area(left=0, top=0, width=1920, height=1080)
```

### 3. Error: "pyautogui.getWindowsWithTitle no disponible"

**Causa**: Función no disponible en Linux o versión antigua de pyautogui.

**Solución**:
```bash
# Actualizar pyautogui
pip install --upgrade pyautogui

# En Linux, instalar dependencias
sudo apt-get install python3-tk python3-dev
sudo apt-get install scrot
```

### 4. Error: "No se pudo inicializar el VideoWriter"

**Causa**: OpenCV no puede crear el archivo de video.

**Solución**:
```bash
# Verificar que el directorio existe
mkdir -p output/videos

# Verificar permisos
chmod 755 output/videos

# Instalar codecs de video
sudo apt-get install ffmpeg
```

### 5. Imports no resueltos (cv2, mss, numpy)

**Causa**: Dependencias no instaladas.

**Solución**:
```bash
# Instalar todas las dependencias
pip install -e .

# O instalar manualmente
pip install opencv-python mss numpy
```

## Debugging Paso a Paso

### 1. Verificar Configuración

```bash
# Verificar que el archivo existe
ls config/settings.yaml

# Verificar sintaxis YAML
python -c "import yaml; yaml.safe_load(open('config/settings.yaml'))"
```

### 2. Verificar Emulador

```python
from pathlib import Path
from src.kaillera_bot.emulator import EmulatorController

emu = EmulatorController(
    executable_path="/usr/bin/rmg",
    roms_directory="/path/to/roms"
)

# Verificar que el ejecutable existe
print(f"Ejecutable válido: {emu.is_executable_valid()}")

# Verificar directorio de ROMs
print(f"Directorio ROMs válido: {emu.is_roms_directory_valid()}")
```

### 3. Verificar Red

```python
from src.kaillera_bot.network import ServerScanner

scanner = ServerScanner()
servers = scanner.scan_master_servers()

for server in servers:
    print(f"{server.name}: {server.players}/{server.max_players} jugadores")
```

### 4. Verificar Grabación

```python
from pathlib import Path
from src.kaillera_bot.recorders import InputRecorder

recorder = InputRecorder(Path("output/inputs"))
recorder.start_recording()

# Presionar algunas teclas...

recorder.stop_recording()
print("Grabación guardada")
```

## Logs

Los logs se guardan en `logs/kaillera_bot.log`. Para ver en tiempo real:

```bash
tail -f logs/kaillera_bot.log
```

Para aumentar el nivel de debug, edita `config/settings.yaml`:

```yaml
logging:
  level: "DEBUG"
```

## Testing

Ejecutar tests para verificar que todo funciona:

```bash
# Instalar dependencias de desarrollo
pip install -e ".[dev]"

# Ejecutar tests
pytest tests/ -v

# Ejecutar con más detalle
pytest tests/ -v -s
```

## Problemas de Rendimiento

### Grabación de video lenta

1. Reducir FPS:
```yaml
recording:
  video:
    fps: 30  # en lugar de 60
```

2. Reducir calidad:
```yaml
recording:
  video:
    quality: "low"  # en lugar de "high"
```

### Alto uso de CPU

1. Aumentar intervalo de escaneo:
```yaml
kaillera:
  scan_interval: 60  # en lugar de 30
```

2. Desactivar grabación de inputs:
```yaml
recording:
  inputs:
    enabled: false
```

## Contacto y Soporte

Si encuentras un bug o necesitas ayuda:

1. Revisa los logs en `logs/kaillera_bot.log`
2. Busca en los issues de GitHub
3. Crea un nuevo issue con:
   - Descripción del problema
   - Logs relevantes
   - Pasos para reproducir
   - Sistema operativo y versión de Python
