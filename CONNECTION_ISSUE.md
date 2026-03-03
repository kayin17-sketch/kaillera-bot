# ⚠️ Problema de Conexión - Servidores Kaillera

## 🔍 **Diagnóstico**

El problema es que **los servidores públicos de Kaillera están inactivos**.

```
❌ master.kaillera.com - No responde
❌ Servidores alternativos - No disponibles
```

---

## ✅ **Soluciones Rápidas**

### **Opción 1: Modo Local (Recomendado)**

Ejecuta el bot **sin conexión automática**:

```bash
# Configurar para modo manual
nano config/settings.yaml
```

Cambiar:
```yaml
automation:
  auto_join: false      # No conectar automáticamente
  auto_record: false    # Grabación manual
```

Ejecutar:
```bash
kaillera-bot-web
```

Acceder a: **http://localhost:5000**

**Ventajas**:
- ✅ Funciona inmediatamente
- ✅ Interfaz web disponible
- ✅ Puedes grabar partidas locales
- ✅ Ver grabaciones existentes

---

### **Opción 2: Servidor Kaillera Local**

**1. Descargar servidor**:
```bash
# Opción A: Desde repositorio
git clone https://github.com/kaillera/kaillera-server

# Opción B: Buscar "kaillerasrv" en internet
```

**2. Ejecutar servidor**:
```bash
./kaillerasrv
```

**3. Configurar bot**:
```yaml
kaillera:
  servers:
    - name: "Local"
      address: "127.0.0.1"
      port: 27888

automation:
  auto_join: true
  auto_record: true
```

**4. Ejecutar bot**:
```bash
kaillera-bot-web
```

---

### **Opción 3: Servidor Conocido**

Si tienes la **IP de un servidor privado**:

```yaml
kaillera:
  servers:
    - name: "Mi Servidor"
      address: "192.168.1.100"  # IP del servidor
      port: 27888
```

---

## 🎮 **Usar Sin Servidor Kaillera**

El bot tiene **funcionalidad limitada** sin servidor:

**✅ Disponible**:
- Interfaz web completa
- Ver grabaciones anteriores
- Descargar grabaciones
- Ver configuración
- Ver logs

**❌ No disponible**:
- Escaneo automático de partidas
- Unión automática a juegos
- Grabación automática de partidas online

---

## 🔧 **Pasos para Empezar**

### **Inicio Rápido**:

```bash
# 1. Instalar
pip install -e .

# 2. Configurar modo manual
nano config/settings.yaml
# Cambiar: auto_join: false, auto_record: false

# 3. Ejecutar
kaillera-bot-web

# 4. Abrir navegador
# http://localhost:5000
```

### **Con Servidor Local**:

```bash
# 1. Descargar servidor Kaillera
# Buscar "kaillerasrv download" en Google

# 2. Ejecutar servidor
./kaillerasrv

# 3. Configurar bot
# address: "127.0.0.1"

# 4. Ejecutar bot
kaillera-bot-web

# 5. Conectar desde emulador RMG
# A localhost:27888
```

---

## 📋 **Checklist**

- [ ] Dependencias instaladas (`pip install -e .`)
- [ ] Configuración editada (`config/settings.yaml`)
- [ ] Emulador RMG descargado
- [ ] ROMs disponibles
- [ ] Servidor Kaillera local (opcional)
- [ ] Bot ejecutándose (`kaillera-bot-web`)
- [ ] Interfaz web accesible (http://localhost:5000)

---

## 🆘 **Ayuda**

### **El bot no arranca**:
```bash
# Verificar configuración
python check_setup.py

# Ver logs
tail -f logs/kaillera_bot.log
```

### **No puedo acceder a la web**:
```bash
# Verificar que está corriendo
ps aux | grep kaillera

# Verificar puerto
netstat -tulpn | grep 5000

# Usar otro puerto
kaillera-bot-web --port 8080
```

### **Quiero conectar a servidor real**:
1. Abrir RMG Kaillera Edition
2. Ir a Kaillera Client
3. Ver lista de servidores
4. Copiar IP del servidor deseado
5. Agregar a `config/settings.yaml`

---

## 📖 **Documentación Completa**

- [KAILLERA_CONNECTION.md](KAILLERA_CONNECTION.md) - Guía detallada de conexión
- [WEB_INTERFACE.md](WEB_INTERFACE.md) - Manual de la interfaz web
- [README.md](README.md) - Documentación general

---

## 💡 **Estado Actual del Proyecto**

**✅ Funcional**:
- Interfaz web
- Grabación manual
- Visualización de grabaciones
- Configuración
- Logs

**⚠️ Limitado**:
- Conexión automática a servidores públicos
- Escaneo de partidas online

**📋 Pendiente**:
- Servidor Kaillera local para pruebas
- Lista de servidores activos actualizada

---

## 🎯 **Recomendación Final**

**Para probar el bot AHORA**:

1. **Ejecutar en modo manual** (sin auto-join)
2. **Explorar la interfaz web**
3. **Verificar que todo funciona**
4. **Luego buscar/configurar servidor Kaillera**

```bash
# Modo manual (funciona sin servidor)
kaillera-bot-web

# Abrir navegador
firefox http://localhost:5000
```

**Una vez verifiques que funciona, configura el servidor Kaillera**.
