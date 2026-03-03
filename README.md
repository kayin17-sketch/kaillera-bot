# Kaillera Bot - Grabador de Partidas N64

Bot automatizado para conectarse a servidores Kaillera y grabar partidas de Nintendo 64 usando RMG Kaillera Edition.

## Características

- **Detección automática de partidas**: Escanea servidores Kaillera y detecta partidas activas
- **Grabación completa**: Captura inputs, video y datos de red
- **Control de emulador**: Automatiza RMG Kaillera Edition
- **Multi-servidor**: Soporte para múltiples servidores Kaillera
- **Logging completo**: Sistema de logs detallado para debugging

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

## Configuración

Edita `config/settings.yaml` para personalizar:

- Ruta al ejecutable de RMG Kaillera Edition
- Servidores Kaillera a monitorear
- Opciones de grabación (video, inputs, red)
- Filtros de partidas (juego específico, número de jugadores, etc.)

Ver `config/settings.yaml.example` para un ejemplo completo.

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
- [DEBUGGING.md](DEBUGGING.md) - Guía de debugging detallada

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
