#!/usr/bin/env python3
"""Script para probar conexión a servidor Kaillera específico."""

import socket
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))


def test_dns_resolution(hostname):
    """Verifica resolución DNS."""
    print(f"🔍 Resolviendo DNS: {hostname}")
    try:
        ip = socket.gethostbyname(hostname)
        print(f"   ✅ {hostname} -> {ip}")
        return ip
    except Exception as e:
        print(f"   ❌ Error DNS: {e}")
        return None


def test_tcp_connection(hostname, port, timeout=5):
    """Prueba conexión TCP."""
    print(f"\n🔍 Probando conexión TCP: {hostname}:{port}")
    
    # Resolver DNS primero
    ip = test_dns_resolution(hostname)
    if not ip:
        return False
    
    try:
        print(f"   Conectando a {ip}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        
        start = time.time()
        sock.connect((ip, port))
        elapsed = (time.time() - start) * 1000
        
        print(f"   ✅ Conexión exitosa en {elapsed:.0f}ms")
        sock.close()
        return True
        
    except socket.timeout:
        print(f"   ❌ Timeout después de {timeout}s")
        return False
    except ConnectionRefusedError:
        print(f"   ❌ Conexión rechazada (¿servidor no está corriendo?)")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False


def test_kaillera_protocol(hostname, port):
    """Prueba protocolo Kaillera básico."""
    print(f"\n🔍 Probando protocolo Kaillera: {hostname}:{port}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        # Resolver DNS
        ip = socket.gethostbyname(hostname)
        sock.connect((ip, port))
        
        # Enviar handshake básico de Kaillera
        # El protocolo Kaillera espera ciertos bytes iniciales
        print("   Enviando handshake...")
        
        # Intentar enviar datos de prueba
        # NOTA: Este es un handshake genérico, puede necesitar ajustes
        test_data = b'\x00\x00\x00\x00'  # Handshake básico
        sock.send(test_data)
        
        # Esperar respuesta
        try:
            response = sock.recv(1024)
            print(f"   ✅ Respuesta recibida: {len(response)} bytes")
            print(f"   Datos: {response[:50]}...")  # Primeros 50 bytes
            return True
        except socket.timeout:
            print("   ⚠️  Sin respuesta del servidor")
            return False
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    finally:
        try:
            sock.close()
        except:
            pass


def test_with_bot_client(hostname, port):
    """Prueba usando el cliente del bot."""
    print(f"\n🔍 Probando con cliente del bot: {hostname}:{port}")
    
    try:
        from kaillera_bot.network import KailleraClient
        
        client = KailleraClient(username="TestBot")
        
        print(f"   Intentando conectar a {hostname}:{port}...")
        success = client.connect(hostname, port)
        
        if success:
            print("   ✅ Cliente conectado exitosamente")
            time.sleep(1)
            client.disconnect()
            return True
        else:
            print("   ❌ Cliente no pudo conectar")
            return False
            
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_config_file():
    """Verifica configuración actual."""
    print("\n🔍 Verificando configuración actual...")
    
    config_path = Path("config/settings.yaml")
    if not config_path.exists():
        print("   ❌ Archivo config/settings.yaml no existe")
        return None
    
    try:
        import yaml
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        servers = config.get('kaillera', {}).get('servers', [])
        if not servers:
            print("   ⚠️  No hay servidores configurados")
            return None
        
        print(f"   ✅ {len(servers)} servidor(es) encontrado(s):")
        for i, server in enumerate(servers, 1):
            print(f"      {i}. {server['name']}: {server['address']}:{server['port']}")
        
        return servers
        
    except Exception as e:
        print(f"   ❌ Error leyendo config: {e}")
        return None


def main():
    print("=" * 60)
    print("TEST DE CONEXIÓN KAILLERA - SERVIDOR ESPECÍFICO")
    print("=" * 60)
    
    # Verificar configuración actual
    servers = check_config_file()
    
    if servers:
        print("\n" + "=" * 60)
        print("TEST CON SERVIDORES CONFIGURADOS")
        print("=" * 60)
        
        for server in servers:
            hostname = server['address']
            port = server['port']
            
            print(f"\n{'='*60}")
            print(f"Servidor: {server['name']}")
            print(f"{'='*60}")
            
            # Test 1: TCP
            tcp_ok = test_tcp_connection(hostname, port)
            
            # Test 2: Protocolo
            if tcp_ok:
                proto_ok = test_kaillera_protocol(hostname, port)
                
                # Test 3: Cliente del bot
                if proto_ok:
                    client_ok = test_with_bot_client(hostname, port)
                    
                    if client_ok:
                        print(f"\n✅ TODO OK - Servidor {server['name']} funcionando")
                    else:
                        print(f"\n⚠️  Servidor accesible pero cliente del bot falla")
                else:
                    print(f"\n⚠️  Servidor accesible pero protocolo Kaillera no responde")
            else:
                print(f"\n❌ Servidor {server['name']} no accesible")
    
    # Permitir test manual
    print("\n" + "=" * 60)
    print("TEST MANUAL")
    print("=" * 60)
    
    hostname = input("\nIngresa hostname/IP de tu servidor (Enter para saltar): ").strip()
    
    if hostname:
        try:
            port_input = input("Puerto (Enter para 27888): ").strip()
            port = int(port_input) if port_input else 27888
        except:
            port = 27888
        
        print(f"\n{'='*60}")
        print(f"PROBANDO: {hostname}:{port}")
        print(f"{'='*60}")
        
        tcp_ok = test_tcp_connection(hostname, port)
        
        if tcp_ok:
            proto_ok = test_kaillera_protocol(hostname, port)
            
            if proto_ok:
                client_ok = test_with_bot_client(hostname, port)
                
                if client_ok:
                    print("\n✅✅✅ CONEXIÓN EXITOSA - Servidor funcionando correctamente")
                    print("\n📝 Actualiza tu config/settings.yaml:")
                    print(f"""
kaillera:
  servers:
    - name: "Mi Servidor"
      address: "{hostname}"
      port: {port}
""")
                else:
                    print("\n⚠️  Servidor responde pero cliente del bot falla")
                    print("   Revisa los logs del bot para más detalles")
            else:
                print("\n⚠️  Servidor accesible pero no responde protocolo Kaillera")
                print("   Verifica que sea un servidor Kaillera válido")
        else:
            print("\n❌ No se puede conectar al servidor")
            print("\n   Posibles causas:")
            print("   1. Servidor no está ejecutándose")
            print("   2. Firewall bloqueando el puerto")
            print("   3. IP/dominio incorrecto")
            print("   4. Puerto incorrecto")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
