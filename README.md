# Kaillera Bot - Grabador de Partidas N64

Bot automatizado para conectarse a servidores Kaillera y grabar partidas de Nintendo 64 usando RMG Kaillera Edition.

## Características

- **🤖 Automatización completa**: Una instancia graba múltiples partidas automáticamente
- **🎯 Detección automática de partidas**: Escanea servidores Kaillera y detecta partidas activas
- **📹 Grabación completa**: Captura inputs, video y datos de red
- **🎮 Control de emulador**: Automatiza RMG Kaillera Edition
- **🌐 Multi-servidor**: Soporte para múltiples servidores Kaillera
- **📊 Monitoreo inteligente**: Detecta automáticamente cuándo termina una partida
- **📝 Logging completo**: Sistema de logs detallado para debugging
- **🔄 Modo 24/7**: Funciona continuamente sin intervención manual
- **🖥️ Interfaz web**: Panel de control accesible desde cualquier dispositivo en la red local

## Requisitos

- Python 3.9 o superior
- RMG Kaillera Edition instalado
- ROMs de N64 (proporcionados por el usuario)
- Sistema operativo: Linux, Windows o macOS

## Instalación

1. **Clonar y entrar al directorio**:
   ```bash
   cd grabador_partidas
   ```

2. **Instalar dependencias**:
   ```bash
   pip install -e .
   ```

3. **Verificar instalación**:
   ```bash
   python check_setup.py
   ```

4. **Configurar**:
   ```bash
   cp config/settings.yaml.example config/settings.yaml
   # Editar config/settings.yaml con tus rutas
   ```

## Uso

### Modo Automático
El bot escaneará servidores automáticamente y se unirá a partidas:

```bash
kaillera-bot
```

O con configuración personalizada:

```bash
python -m kaillera_bot.main --config config/settings.yaml
```

### Verificación Rápida

Para verificar que todo está configurado correctamente:

```bash
python check_setup.py
```

### Interfaz Web 🖥️

El bot incluye una **interfaz web completa** accesible desde cualquier dispositivo en tu red local:

```bash
kaillera-bot-web
```

O con opciones personalizadas:

```bash
kaillera-bot-web --host 0.0.0.0 --port 5000
```

**Funcionalidades:**
- ✅ Panel de control en tiempo real
- ✅ Iniciar/Detener el bot
- ✅ Ver servidores y partidas activas
- ✅ Descargar grabaciones
- ✅ Ver logs en vivo
- ✅ Editar configuración

**Acceso:** `http://localhost:5000` o `http://<tu-ip-local>:5000`

Ver [WEB_INTERFACE.md](WEB_INTERFACE.md) para documentación completa.

## Configuración

Edita `config/settings.yaml` para personalizar:

- Ruta al ejecutable de RMG Kaillera Edition
- Servidores Kaillera a monitorear
- Opciones de grabación (video, inputs, red)
- Filtros de partidas (juego específico, número de jugadores, etc.)

Ver `config/settings.yaml.example` para un ejemplo completo.

## 🤖 Automatización

### Modo Automático Completo

El bot puede **grabar múltiples partidas automáticamente con una sola instancia**:

```yaml
automation:
  auto_join: true              # Unirse automáticamente
  auto_record: true            # Grabar automáticamente
  auto_disconnect: true        # Desconectarse al terminar
  max_recording_duration: 3600 # 1 hora máximo
  inactivity_timeout: 300      # 5 min sin datos = fin
  no_players_timeout: 30       # 30 seg sin jugadores = fin
```

**Cómo funciona:**
1. Escanea servidores continuamente
2. Se une a partidas automáticamente
3. Graba mientras la partida está activa
4. **Detecta automáticamente cuándo termina** (por: sin jugadores, timeout, inactividad)
5. Se desconecta y busca la siguiente partida
6. Repite infinitamente

Ver [AUTOMATION.md](AUTOMATION.md) para documentación completa.

### Modo Manual

Para controlar qué partidas grabar:

```yaml
automation:
  auto_join: false
```

El bot escaneará pero no se unirá automáticamente.

## Estructura del Proyecto

```
grabador_partidas/
├── src/kaillera_bot/
│   ├── __init__.py
│   ├── main.py                 # Punto de entrada principal
│   ├── network/                # Módulos de red
│   │   ├── kaillera_client.py  # Cliente del protocolo Kaillera
│   │   └── server_scanner.py   # Escáner de servidores
│   ├── recorders/              # Grabadores
│   │   ├── input_recorder.py   # Grabador de inputs
│   │   ├── video_recorder.py   # Grabador de video
│   │   └── network_recorder.py # Grabador de datos de red
│   └── emulator/               # Control del emulador
│       └── emulator_controller.py
├── tests/                      # Pruebas unitarias
├── config/                     # Archivos de configuración
│   ├── settings.yaml           # Tu configuración (no commitear)
│   └── settings.yaml.example   # Ejemplo de configuración
└── output/                     # Grabaciones guardadas
    ├── videos/
    ├── inputs/
    └── network/
```

## Desarrollo

Instalar dependencias de desarrollo:

```bash
pip install -e ".[dev]"
```

Ejecutar tests:

```bash
pytest tests/
```

Formatear código:

```bash
black src/ tests/
```

Verificar tipos:

```bash
mypy src/
```

## Debugging

Para problemas y soluciones comunes, ver [DEBUGGING.md](DEBUGGING.md)

### Logs

Los logs se guardan en `logs/kaillera_bot.log`. Para ver en tiempo real:

```bash
tail -f logs/kaillera_bot.log
```

### Verbose Mode

Para más detalle en los logs, cambiar en `config/settings.yaml`:

```yaml
logging:
  level: "DEBUG"
```

## Solución de Problemas

### El emulador no inicia
- Verifica que la ruta al ejecutable sea correcta
- En Linux, asegúrate de que el ejecutable tenga permisos: `chmod +x /path/to/rmg`

### No se detectan partidas
- Verifica tu conexión a internet
- Comprueba que los servidores Kaillera estén activos
- Revisa los logs en `logs/kaillera_bot.log`

### La grabación de video falla
- Asegúrate de tener las dependencias de OpenCV instaladas
- En Linux puede que necesites: `sudo apt-get install python3-opencv`
- Verifica que el directorio `output/videos/` tenga permisos de escritura

### Error de imports
```bash
# Reinstalar dependencias
pip install --force-reinstall -e .
```

## Documentación Adicional

- [QUICKSTART.md](QUICKSTART.md) - Guía de inicio rápido
- [WEB_INTERFACE.md](WEB_INTERFACE.md) - Interfaz web completa
- [AUTOMATION.md](AUTOMATION.md) - Automatización y detección de fin de partida
- [FORMATS.md](FORMATS.md) - Formatos de grabación
- [DEBUGGING.md](DEBUGGING.md) - Guía de debugging detallada
- [SETUP.md](SETUP.md) - Setup en 3 pasos

## Contribuir

1. Fork el repositorio
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agrega nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crea un Pull Request

## Notas Importantes

- Este bot es para uso educativo y personal
- Respeta los términos de servicio de los servidores Kaillera
- Solo usa ROMs que poseas legalmente
- No uses el bot para hacer spam o sobrecargar servidores

## Licencia

MIT License
