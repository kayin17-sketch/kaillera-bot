# Guía de Conexión Kaillera

## 🚨 **Problema Común: Servidores Públicos Inactivos**

Los servidores maestros públicos de Kaillera están **mayormente inactivos**. Esto es normal ya que:
- Kaillera es un protocolo antiguo (año 2000)
- Los servidores maestros originales han ido desapareciendo
- No hay una lista centralizada actualizada

---

## ✅ **Soluciones para Conectar**

### **Opción 1: Servidor Local (Para pruebas)**

**Instalar servidor Kaillera local**:

1. **Descargar Kaillera Server**:
   - Windows: `kaillerasrv.exe`
   - Linux: `kaillerasrv`

2. **Ejecutar servidor**:
   ```bash
   # En una terminal
   ./kaillerasrv
   ```
   
3. **Configurar el bot**:
   ```yaml
   kaillera:
     servers:
       - name: "Servidor Local"
         address: "127.0.0.1"
         port: 27888
   ```

---

### **Opción 2: Servidor Privado Conocido**

Si tienes la **IP de un servidor privado** (ej: servidor de un amigo):

```yaml
kaillera:
  servers:
    - name: "Servidor de Amigo"
      address: "192.168.1.100"  # IP del servidor
      port: 27888
```

---

### **Opción 3: Buscar Servidores Activos**

**Método 1: Desde el emulador**

1. Abrir **RMG Kaillera Edition**
2. Ir a **Kaillera Client**
3. Ver lista de servidores disponibles
4. Copiar la IP del servidor deseado
5. Agregarla a `config/settings.yaml`

**Método 2: Escaneo de red**

```bash
# Escanear rangos de IPs comunes
nmap -p 27888 192.168.1.0/24 --open
```

---

### **Opción 4: Servidor Dedicado**

**Montar tu propio servidor Kaillera**:

1. **Descargar Kaillera Server**:
   - https://github.com/kaillera/kaillera-server

2. **Configurar**:
   ```ini
   ; kaillerasrv.conf
   ServerName=Mi Servidor Kaillera
   MaxUsers=100
   Port=27888
   ```

3. **Ejecutar**:
   ```bash
   ./kaillerasrv -c kaillerasrv.conf
   ```

4. **Configurar el bot**:
   ```yaml
   kaillera:
     servers:
       - name: "Mi Servidor"
         address: "tu-ip-publica"
         port: 27888
   ```

---

## 🔧 **Configuración Recomendada**

Para **uso local/pruebas**:

```yaml
# config/settings.yaml
kaillera:
  servers:
    # Servidor local para pruebas
    - name: "Localhost"
      address: "127.0.0.1"
      port: 27888
    
    # Servidor en red local (ej: otro PC)
    - name: "Red Local"
      address: "192.168.1.XXX"  # IP del otro PC
      port: 27888
  
  scan_interval: 30
  
  filters:
    games: []  # Todos los juegos
    min_players: 1  # Aceptar partidas con 1 jugador (para pruebas)
    max_players: 4
```

---

## 🎮 **Modo de Prueba Local**

**Sin servidor Kaillera (solo grabación)**:

El bot puede funcionar en **modo manual** sin conectarse a Kaillera:

1. **Configurar**:
   ```yaml
   automation:
     auto_join: false  # No conectarse automáticamente
   ```

2. **Ejecutar**:
   ```bash
   kaillera-bot-web
   ```

3. **Usar interfaz web** para:
   - Ver configuración
   - Iniciar grabación manualmente
   - Ver grabaciones existentes

---

## 📝 **Checklist de Diagnóstico**

Ejecuta el diagnóstico:

```bash
cd grabador_partidas
python3 diagnose.py
```

**Verificar**:
- [ ] Conexión a internet ✅
- [ ] DNS funciona ✅
- [ ] Puerto 27888 no bloqueado por firewall
- [ ] Servidor Kaillera accesible (IP conocida)
- [ ] Emulador configurado

---

## 🌐 **Lista de Servidores Comunes (Pueden no funcionar)**

Historial de servidores conocidos (algunos pueden estar caídos):

```
master.kaillera.com:27888 (Oficial - suele estar caído)
antofka.zapto.org:27888 (Comunidad)
kaillera.com:27888 (Alternativo)
```

**Recomendación**: Buscar en foros de emulación o comunidades de Kaillera para servidores activos.

---

## 🛠️ **Solución de Problemas**

### **Error: "No se puede conectar al servidor"**

**Causas**:
1. ❌ Servidor no existe o está caído
2. ❌ Firewall bloqueando puerto 27888
3. ❌ ISP bloqueando conexiones
4. ❌ DNS no resuelve el nombre

**Soluciones**:
1. ✅ Usar IP en lugar de nombre de dominio
2. ✅ Verificar firewall: `sudo ufw allow 27888`
3. ✅ Probar con VPN
4. ✅ Usar servidor local

### **Error: "Connection refused"**

**Causa**: El servidor existe pero no acepta conexiones

**Solución**:
- Servidor lleno
- IP bloqueada
- Servidor mal configurado

### **Error: "Timeout"**

**Causa**: El servidor no responde

**Solución**:
- Servidor caído
- Problemas de red
- Firewall bloqueando

---

## 📞 **Ayuda Adicional**

Si continúas con problemas:

1. **Verifica que el emulador funcione**:
   - Abre RMG Kaillera Edition
   - Intenta conectarte a un servidor manualmente
   - Si funciona, copia la IP a la configuración del bot

2. **Usa modo offline**:
   - Configura `auto_join: false`
   - Usa la interfaz web para control manual
   - Graba partidas locales

3. **Contacta a la comunidad**:
   - Foros de emulación
   - Discord/Reddit de Kaillera
   - Pregunta por servidores activos

---

## ✅ **Recomendación Final**

**Para empezar rápidamente**:

1. **Instala un servidor Kaillera local**
2. **Configura el bot para conectarse a localhost**
3. **Prueba todas las funcionalidades**
4. **Luego busca servidores públicos activos**

```bash
# 1. Descargar servidor
wget https://example.com/kaillerasrv

# 2. Ejecutar
./kaillerasrv

# 3. Configurar bot
# En config/settings.yaml:
# address: "127.0.0.1"

# 4. Ejecutar bot
kaillera-bot-web
```
