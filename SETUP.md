# Setup Rápido - 3 Pasos

## Paso 1: Instalar
```bash
cd grabador_partidas
pip install -e .
```

## Paso 2: Configurar
```bash
cp config/settings.yaml.example config/settings.yaml
nano config/settings.yaml  # Editar con tus rutas
```

## Paso 3: Verificar y Ejecutar
```bash
python check_setup.py
python -m kaillera_bot.main
```

## ¿Problemas?

Ver [DEBUGGING.md](DEBUGGING.md) para soluciones a errores comunes.
