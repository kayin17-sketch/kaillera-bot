# Kaillera Bot - Guía de Inicio Rápido

## Configuración Inicial

1. **Instalar dependencias**:
   ```bash
   cd grabador_partidas
   pip install -e .
   ```

2. **Configurar el emulador**:
   - Descarga RMG Kaillera Edition desde: https://github.com/Rosalie241/RMG
   - Edita `config/settings.yaml` y actualiza:
     - `emulator.executable_path`: Ruta al ejecutable de RMG
     - `emulator.roms_directory`: Directorio donde tienes tus ROMs de N64

3. **Configurar servidores Kaillera** (opcional):
   - En `config/settings.yaml`, añade los servidores que quieras monitorear
   - Puedes filtrar por juegos específicos

## Uso

### Modo Automático
El bot escaneará servidores automáticamente y se unirá a partidas:

```bash
kaillera-bot
```

### Modo Manual
Desactiva `auto_join` en la configuración para controlar manualmente qué partidas grabar.

## Estructura de Salida

Las grabaciones se guardan en `output/`:
- `videos/`: Archivos de video MP4
- `inputs/`: Archivos JSON con inputs grabados
- `network/`: Archivos JSON con datos de red

## Solución de Problemas

### El emulador no inicia
- Verifica que la ruta al ejecutable sea correcta
- En Linux, asegúrate de que el ejecutable tenga permisos

### No se detectan partidas
- Verifica tu conexión a internet
- Comprueba que los servidores Kaillera estén activos
- Revisa los logs en `logs/kaillera_bot.log`

### La grabación de video falla
- Asegúrate de tener las dependencias de OpenCV instaladas
- En Linux puede que necesites: `sudo apt-get install python3-opencv`

## Notas Importantes

- Este bot es para uso educativo y personal
- Respeta los términos de servicio de los servidores Kaillera
- Solo usa ROMs que poseas legalmente
