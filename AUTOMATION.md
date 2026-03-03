# Automatización y Detección de Fin de Partida

## 🤖 Modo Completamente Automático

El bot ahora puede **grabar múltiples partidas automáticamente con una sola instancia**.

### Cómo Funciona

1. **Escaneo continuo**: Busca partidas en servidores Kaillera
2. **Detección automática**: Se une a partidas que cumplan los filtros
3. **Grabación**: Inicia grabación cuando empieza la partida
4. **Monitoreo activo**: Detecta cuándo termina la partida
5. **Limpieza**: Se desconecta y prepara para la siguiente
6. **Repetición**: Vuelve al paso 1 infinitamente

## ⚙️ Configuración

```yaml
automation:
  auto_join: true              # Unirse automáticamente a partidas
  auto_record: true            # Grabar automáticamente
  auto_disconnect: true        # Desconectarse al terminar
  
  max_recording_duration: 3600 # 1 hora máximo por partida
  inactivity_timeout: 300      # 5 min sin datos = fin
  no_players_timeout: 30       # 30 seg sin jugadores = fin
```

## 🎯 Condiciones de Fin de Partida

El bot detecta automáticamente cuándo terminar una partida:

### 1. **No hay jugadores** (Inmediato)
```python
# Cuando todos los jugadores se van
active_players_count == 0
```

**Comportamiento**:
- Detecta cuando `on_player_leave()` reduce el contador a 0
- Espera 30 segundos de gracia (configurable)
- Termina grabación automáticamente

### 2. **Tiempo máximo alcanzado** (Configurable)
```yaml
max_recording_duration: 3600  # segundos
```

**Comportamiento**:
- Previene grabaciones infinitas
- Útil si el emulador se cuelga
- Por defecto: 1 hora

### 3. **Inactividad de datos** (Configurable)
```yaml
inactivity_timeout: 300  # segundos
```

**Comportamiento**:
- Detecta si no hay datos del juego por 5 minutos
- Útil para partidas que se quedan colgadas
- Actualiza `last_game_data_time` con cada dato recibido

## 🔄 Flujo de Estados

```
┌─────────────┐
│   ESCANEANDO  │ ← Buscando partidas
└──────┬──────┘
       │ Partida encontrada
       ↓
┌─────────────┐
│  CONECTANDO  │ ← Uniéndose al servidor
└──────┬──────┘
       │ Conectado
       ↓
┌─────────────┐
│   GRABANDO   │ ← Partida en curso
└──────┬──────┘
       │ Condición de fin detectada
       ↓
┌─────────────┐
│  LIMPIANDO   │ ← Desconectando y guardando
└──────┬──────┘
       │ Listo
       ↓
   [Vuelve a ESCANEANDO]
```

## 📊 Monitoreo en Tiempo Real

El bot usa un **thread de monitoreo** que verifica cada 5 segundos:

```python
while current_session:
    if check_game_end_conditions():
        end_session()
        break
    sleep(5)
```

### Variables monitoreadas:
- `active_players_count`: Jugadores conectados
- `recording_start_time`: Cuándo empezó la grabación
- `last_game_data_time`: Último dato del juego recibido

## 🎮 Ejemplo de Uso

### Configuración mínima:
```yaml
automation:
  auto_join: true
  auto_record: true
  auto_disconnect: true
```

### Ejecutar:
```bash
python -m kaillera_bot.main
```

### Logs esperados:
```
[INFO] === Iniciando Kaillera Bot ===
[INFO] Escaneando servidores...
[INFO] Partida encontrada: Super Smash Bros (2/4) en Kaillera Master
[INFO] Uniéndose a partida: Super Smash Bros
[INFO] Grabación iniciada
[INFO] Monitoreo de partida iniciado
[INFO] Jugador unido: Player1 (#1)
[INFO] Jugador unido: Player2 (#2)
...
[INFO] Jugador salió: Player2 (#2)
[INFO] Jugador salió: Player1 (#1)
[INFO] No hay jugadores activos, terminando partida
[INFO] Finalizando sesión actual...
[INFO] Grabación detenida
[INFO] Sesión finalizada, listo para la siguiente partida
[INFO] Escaneando servidores...
```

## ⚠️ Casos Especiales

### Partida larga (>1 hora)
```yaml
# Aumentar tiempo máximo
max_recording_duration: 7200  # 2 horas
```

### Partida pausada
```yaml
# Aumentar timeout de inactividad
inactivity_timeout: 600  # 10 minutos
```

### Muchos jugadores se van y vuelven
```yaml
# Dar más tiempo de gracia
no_players_timeout: 60  # 1 minuto
```

## 🔧 Ajustes Recomendados

### Para partidas rápidas (< 30 min)
```yaml
max_recording_duration: 1800  # 30 min
inactivity_timeout: 180       # 3 min
no_players_timeout: 15        # 15 seg
```

### Para partidas largas (> 2 horas)
```yaml
max_recording_duration: 10800  # 3 horas
inactivity_timeout: 600        # 10 min
no_players_timeout: 60         # 1 min
```

### Para torneos/competitivo
```yaml
max_recording_duration: 7200  # 2 horas
inactivity_timeout: 120       # 2 min (estricto)
no_players_timeout: 10        # 10 seg (estricto)
```

## 🐛 Debugging

### Ver logs de monitoreo:
```yaml
logging:
  level: "DEBUG"
```

### Verificar que funciona:
```bash
# Ver logs en tiempo real
tail -f logs/kaillera_bot.log | grep -E "(monitoreo|Condición|terminando)"
```

### Probar detección de fin:
1. Unirse a una partida
2. Esperar a que los jugadores se vayan
3. Verificar que el bot termina automáticamente

## 📈 Métricas

El bot registra:
- Duración de cada partida
- Número de jugadores que pasaron
- Cantidad de datos recibidos
- Razón de fin de partida

Ver en: `output/network/network_data_*.json`

## ✅ Check List

Antes de usar automatización completa:

- [ ] Configurar `auto_join: true`
- [ ] Ajustar `max_recording_duration` según tus partidas
- [ ] Configurar `inactivity_timeout` apropiadamente
- [ ] Verificar que el emulador se cierra correctamente
- [ ] Probar con una partida de prueba
- [ ] Revisar logs para confirmar detección de fin

## 🚀 Producción

Para uso 24/7 sin supervisión:

```yaml
automation:
  auto_join: true
  auto_record: true
  auto_disconnect: true
  max_recording_duration: 3600
  inactivity_timeout: 300
  no_players_timeout: 30

logging:
  level: "INFO"
  file: "logs/kaillera_bot.log"
```

Ejecutar con nohup o systemd:

```bash
# Con nohup
nohup python -m kaillera_bot.main > /dev/null 2>&1 &

# O crear servicio systemd (ver docs/systemd/)
```
