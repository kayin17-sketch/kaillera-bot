#!/usr/bin/env python3
"""Script de diagnóstico para verificar conectividad Kaillera."""

import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_internet_connection():
    """Verifica conexión a internet."""
    print("🔍 Verificando conexión a internet...")
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        print("✅ Conexión a internet: OK")
        return True
    except Exception as e:
        print(f"❌ Sin conexión a internet: {e}")
        return False


def test_kaillera_master_server():
    """Verifica conexión al servidor maestro de Kaillera."""
    print("\n🔍 Verificando servidor maestro Kaillera...")
    
    master_servers = [
        ("master.kaillera.com", 27888),
        ("kaillera.com", 27888),
    ]
    
    for server, port in master_servers:
        try:
            print(f"   Probando {server}:{port}...")
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((server, port))
            
            if result == 0:
                print(f"   ✅ {server}:{port} - Puerto abierto")
                sock.close()
                return True
            else:
                print(f"   ❌ {server}:{port} - No responde (código: {result})")
                sock.close()
        except socket.timeout:
            print(f"   ❌ {server}:{port} - Timeout")
        except Exception as e:
            print(f"   ❌ {server}:{port} - Error: {e}")
    
    return False


def test_dns_resolution():
    """Verifica resolución DNS de servidores Kaillera."""
    print("\n🔍 Verificando resolución DNS...")
    
    servers = [
        "master.kaillera.com",
        "kaillera.com",
    ]
    
    for server in servers:
        try:
            ip = socket.gethostbyname(server)
            print(f"✅ {server} -> {ip}")
        except Exception as e:
            print(f"❌ {server} - Error DNS: {e}")


def test_local_port():
    """Verifica que el puerto local no esté en uso."""
    print("\n🔍 Verificando puertos locales...")
    
    ports = [5000, 27888]
    
    for port in ports:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('0.0.0.0', port))
            sock.close()
            print(f"✅ Puerto {port} disponible")
        except Exception as e:
            print(f"⚠️  Puerto {port} en uso o no disponible: {e}")


def test_config_file():
    """Verifica el archivo de configuración."""
    print("\n🔍 Verificando configuración...")
    
    config_path = Path("config/settings.yaml")
    
    if not config_path.exists():
        print(f"❌ Archivo de configuración no encontrado: {config_path}")
        return False
    
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        print("✅ Archivo de configuración válido")
        
        # Verificar configuración de servidores
        servers = config.get('kaillera', {}).get('servers', [])
        if not servers:
            print("⚠️  No hay servidores configurados")
            return False
        
        print(f"✅ {len(servers)} servidor(es) configurado(s)")
        for server in servers:
            print(f"   - {server['name']}: {server['address']}:{server['port']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error leyendo configuración: {e}")
        return False


def test_emulator_config():
    """Verifica configuración del emulador."""
    print("\n🔍 Verificando configuración del emulador...")
    
    config_path = Path("config/settings.yaml")
    
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        emu_config = config.get('emulator', {})
        
        exe_path = emu_config.get('executable_path', '')
        roms_path = emu_config.get('roms_directory', '')
        
        if not exe_path or exe_path == "/path/to/RMG-Kaillera-Edition":
            print("⚠️  Ruta del emulador no configurada")
            print("   Edita config/settings.yaml y configura executable_path")
            return False
        
        if not Path(exe_path).exists():
            print(f"❌ Emulador no encontrado en: {exe_path}")
            return False
        
        print(f"✅ Emulador encontrado: {exe_path}")
        
        if not roms_path or roms_path == "/path/to/roms":
            print("⚠️  Directorio de ROMs no configurado")
            return False
        
        if not Path(roms_path).exists():
            print(f"❌ Directorio de ROMs no encontrado: {roms_path}")
            return False
        
        print(f"✅ Directorio de ROMs encontrado: {roms_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def ping_kaillera_server(address, port=27888):
    """Intenta hacer ping a un servidor Kaillera."""
    print(f"\n🔍 Haciendo ping a {address}:{port}...")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        start_time = socket.getdefaulttimeout()
        sock.connect((address, port))
        end_time = socket.getdefaulttimeout()
        
        ping_ms = (end_time - start_time) * 1000 if end_time and start_time else 0
        
        print(f"✅ Conexión exitosa (ping: {ping_ms:.0f}ms)")
        
        # Intentar enviar datos de prueba
        try:
            # Enviar un byte de prueba
            sock.send(b'\x00')
            response = sock.recv(1024)
            print(f"✅ Respuesta recibida: {len(response)} bytes")
        except Exception as e:
            print(f"⚠️  Sin respuesta del servidor: {e}")
        
        sock.close()
        return True
        
    except socket.timeout:
        print(f"❌ Timeout conectando a {address}:{port}")
        return False
    except Exception as e:
        print(f"❌ Error conectando a {address}:{port}: {e}")
        return False


def main():
    """Ejecuta todos los diagnósticos."""
    print("=" * 60)
    print("DIAGNÓSTICO DE KAILLERA BOT")
    print("=" * 60)
    
    results = []
    
    # Tests básicos
    results.append(("Internet", test_internet_connection()))
    results.append(("DNS", test_dns_resolution()))
    results.append(("Puertos locales", test_local_port()))
    results.append(("Configuración", test_config_file()))
    
    # Tests de conectividad Kaillera
    results.append(("Servidor maestro", test_kaillera_master_server()))
    
    # Test de emulador
    results.append(("Emulador", test_emulator_config()))
    
    # Resumen
    print("\n" + "=" * 60)
    print("RESUMEN DE DIAGNÓSTICO")
    print("=" * 60)
    
    for name, passed in results:
        status = "✅ OK" if passed else "❌ FALLO"
        print(f"{name:20s} {status}")
    
    # Recomendaciones
    print("\n" + "=" * 60)
    print("RECOMENDACIONES")
    print("=" * 60)
    
    if not results[0][1]:  # Sin internet
        print("1. Verifica tu conexión a internet")
    
    if not results[4][1]:  # Servidor maestro no accesible
        print("2. El servidor maestro de Kaillera no responde")
        print("   - Posibles causas:")
        print("     * Servidor caído temporalmente")
        print("     * Firewall bloqueando puerto 27888")
        print("     * ISP bloqueando el puerto")
        print("   - Solución:")
        print("     * Espera unos minutos y reintenta")
        print("     * Verifica configuración de firewall")
        print("     * Intenta con VPN si el ISP bloquea")
    
    if not results[5][1]:  # Emulador no configurado
        print("3. Configura el emulador en config/settings.yaml:")
        print("   emulator:")
        print("     executable_path: '/ruta/a/tu/emulador'")
        print("     roms_directory: '/ruta/a/tus/roms'")
    
    # Test de ping a servidor específico si está configurado
    try:
        import yaml
        with open('config/settings.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        servers = config.get('kaillera', {}).get('servers', [])
        if servers:
            server = servers[0]
            ping_kaillera_server(server['address'], server['port'])
    except Exception:
        pass
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
