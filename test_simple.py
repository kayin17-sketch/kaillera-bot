#!/usr/bin/env python3
"""Script simple para probar conexión TCP a servidor Kaillera."""

import socket
import sys

def test_connection(hostname, port=27888):
    """Prueba conexión básica."""
    print(f"🔍 Probando conexión a {hostname}:{port}")
    
    # Test 1: DNS
    print("\n1️⃣ Resolución DNS:")
    try:
        ip = socket.gethostbyname(hostname)
        print(f"   ✅ {hostname} -> {ip}")
    except Exception as e:
        print(f"   ❌ Error DNS: {e}")
        return False
    
    # Test 2: TCP Connection
    print("\n2️⃣ Conexión TCP:")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        import time
        start = time.time()
        sock.connect((ip, port))
        elapsed = (time.time() - start) * 1000
        
        print(f"   ✅ Conectado en {elapsed:.0f}ms")
        
        # Test 3: Enviar datos
        print("\n3️⃣ Enviando datos de prueba:")
        try:
            # Enviar algunos bytes de prueba
            sock.send(b'\x00')
            print("   ✅ Datos enviados")
            
            # Intentar recibir
            sock.settimeout(2)
            try:
                response = sock.recv(1024)
                print(f"   ✅ Respuesta recibida: {len(response)} bytes")
            except socket.timeout:
                print("   ⚠️  Sin respuesta (timeout)")
                
        except Exception as e:
            print(f"   ❌ Error enviando: {e}")
        
        sock.close()
        return True
        
    except socket.timeout:
        print("   ❌ Timeout - servidor no responde")
        return False
    except ConnectionRefusedError:
        print("   ❌ Conexión rechazada")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("TEST DE CONEXIÓN KAILLERA")
    print("=" * 60)
    
    if len(sys.argv) > 1:
        # Usar argumento
        hostname = sys.argv[1]
        port = int(sys.argv[2]) if len(sys.argv) > 2 else 27888
        test_connection(hostname, port)
    else:
        # Modo interactivo
        print("\nUso:")
        print("  python3 test_simple.py <hostname> [puerto]")
        print("\nEjemplo:")
        print("  python3 test_simple.py mi-servidor.com")
        print("  python3 test_simple.py 192.168.1.100 27888")
        
        print("\n" + "=" * 60)
        hostname = input("\nIngresa hostname/IP (Enter para salir): ").strip()
        
        if hostname:
            port_str = input("Puerto (Enter para 27888): ").strip()
            port = int(port_str) if port_str else 27888
            
            print("\n" + "=" * 60)
            success = test_connection(hostname, port)
            
            if success:
                print("\n" + "=" * 60)
                print("✅ CONEXIÓN EXITOSA")
                print("=" * 60)
                print("\nTu servidor está accesible. Configura el bot:")
                print(f"""
# config/settings.yaml
kaillera:
  servers:
    - name: "Mi Servidor"
      address: "{hostname}"
      port: {port}
""")
            else:
                print("\n" + "=" * 60)
                print("❌ CONEXIÓN FALLIDA")
                print("=" * 60)
                print("\nPosibles soluciones:")
                print("1. Verifica que el servidor esté corriendo")
                print("2. Verifica firewall (puerto 27888)")
                print("3. Verifica que hostname/IP sea correcto")
                print("4. Intenta con IP en lugar de dominio")
