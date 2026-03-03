#!/usr/bin/env python3
"""
Diagnóstico completo de conexión Kaillera.
"""

import socket
import sys
import time

def test_basic_connection(hostname, port):
    """Test básico de conexión."""
    print(f"\n{'='*60}")
    print(f"TEST: {hostname}:{port}")
    print(f"{'='*60}\n")
    
    # 1. DNS
    print("1️⃣  DNS Resolution:")
    try:
        ip = socket.gethostbyname(hostname)
        print(f"   ✅ {hostname} -> {ip}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False
    
    # 2. TCP con timeout largo
    print("\n2️⃣  TCP Connection (timeout 30s):")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(30)  # Timeout muy largo
        
        start = time.time()
        sock.connect((ip, port))
        elapsed = time.time() - start
        
        print(f"   ✅ Conectado en {elapsed:.2f}s")
        
        # 3. Intentar recibir
        print("\n3️⃣  Recibir datos iniciales:")
        sock.settimeout(5)
        try:
            data = sock.recv(4096)
            if data:
                print(f"   ✅ Recibidos {len(data)} bytes")
                print(f"   Hex: {data[:32].hex()}")
                return True, sock, data
            else:
                print("   ⚠️  Sin datos")
                return True, sock, None
        except socket.timeout:
            print("   ⚠️  Timeout (normal si el servidor espera cliente primero)")
            return True, sock, None
        except Exception as e:
            print(f"   ❌ Error recibiendo: {e}")
            return True, sock, None
            
    except socket.timeout:
        print(f"   ❌ Timeout después de 30s")
        return False, None, None
    except ConnectionRefusedError:
        print(f"   ❌ Conexión rechazada")
        return False, None, None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False, None, None

def test_emulator_style(hostname, port):
    """Intentar conectar como lo hace un emulador."""
    print(f"\n{'='*60}")
    print("TEST: Conexión estilo emulador")
    print(f"{'='*60}\n")
    
    try:
        ip = socket.gethostbyname(hostname)
    except:
        print("   ❌ DNS falló")
        return
    
    print("1️⃣  Creando socket TCP...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
    
    print("2️⃣  Conectando...")
    sock.settimeout(10)
    
    try:
        sock.connect((ip, port))
        print("   ✅ Conectado")
        
        print("\n3️⃣  Enviando paquete HELLO...")
        # Intentar diferentes formatos de HELLO
        hellos = [
            ("Texto con salto de línea", b"HELLO\n"),
            ("Texto con doble salto", b"HELLO\n\n"),
            ("Binario genérico", b'\x00HELLO\x00'),
            ("Kaillera string", b'KAILLERA'),
        ]
        
        for name, hello_data in hellos:
            print(f"\n   Probando: {name}")
            print(f"   Enviando: {hello_data.hex()}")
            
            try:
                sock.send(hello_data)
                print("      ✅ Enviado")
                
                # Esperar respuesta
                sock.settimeout(2)
                try:
                    response = sock.recv(4096)
                    if response:
                        print(f"      📥 Respuesta: {len(response)} bytes")
                        print(f"      Hex: {response.hex()}")
                        print(f"      ASCII: {response}")
                        
                        # Guardar en archivo
                        filename = "kaillera_response.txt"
                        with open(filename, 'w') as f:
                            f.write(f"RESPUESTA DEL SERVIDOR\n")
                            f.write(f"{'='*60}\n\n")
                            f.write(f"Enviado: {hello_data.hex()}\n")
                            f.write(f"Recibido: {response.hex()}\n\n")
                            f.write(f"Datos:\n")
                            f.write(f"  Hex: {response.hex()}\n")
                            try:
                                f.write(f"  UTF-8: {response.decode('utf-8', errors='replace')}\n")
                            except:
                                pass
                            try:
                                f.write(f"  Latin-1: {response.decode('latin-1', errors='replace')}\n")
                            except:
                                pass
                        
                        print(f"\n   💾 Respuesta guardada en: {filename}")
                        return response
                        
                except socket.timeout:
                    print("      ⚠️  Sin respuesta (timeout)")
                except Exception as e:
                    print(f"      ❌ Error recibiendo: {e}")
                    
                # Pausa entre intentos
                time.sleep(1)
                
            except Exception as e:
                print(f"      ❌ Error enviando: {e}")
        
        sock.close()
        
    except Exception as e:
        print(f"   ❌ Error conectando: {e}")

def test_udp(hostname, port):
    """Test si Kaillera usa UDP en lugar de TCP."""
    print(f"\n{'='*60}")
    print("TEST: UDP (por si Kaillera usa UDP)")
    print(f"{'='*60}\n")
    
    try:
        ip = socket.gethostbyname(hostname)
    except:
        return
    
    print("1️⃣  Creando socket UDP...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.settimeout(5)
    
    print("2️⃣  Enviando datagrama...")
    try:
        sock.sendto(b"HELLO", (ip, port))
        print("   ✅ Datagrama enviado")
        
        print("3️⃣  Esperando respuesta...")
        try:
            data, addr = sock.recvfrom(4096)
            print(f"   📥 Respuesta de {addr}: {len(data)} bytes")
            print(f"   Hex: {data.hex()}")
        except socket.timeout:
            print("   ⚠️  Sin respuesta UDP")
        
        sock.close()
        
    except Exception as e:
        print(f"   ❌ Error: {e}")

def main():
    print("=" * 60)
    print("DIAGNÓSTICO AVANZADO KAILLERA")
    print("=" * 60)
    
    # Pedir servidor
    hostname = input("\nHostname/IP del servidor: ").strip()
    if not hostname:
        print("❌ Error: hostname requerido")
        return
    
    port_str = input("Puerto (Enter para 27888): ").strip()
    port = int(port_str) if port_str else 27888
    
    # Test 1: TCP básico
    success, sock, data = test_basic_connection(hostname, port)
    
    if success:
        print("\n✅ Conexión TCP exitosa")
        
        if sock:
            sock.close()
    else:
        print("\n❌ No se pudo conectar por TCP")
    
    # Test 2: Estilo emulador
    test_emulator_style(hostname, port)
    
    # Test 3: UDP
    test_udp(hostname, port)
    
    # Sugerencias
    print("\n" + "=" * 60)
    print("SIGUIENTES PASOS")
    print("=" * 60)
    
    if not success:
        print("""
❌ No se pudo conectar. Verifica:

1. ¿El servidor está corriendo?
   - En el servidor: netstat -tulpn | grep 27888
   - Debería mostrar algo escuchando en el puerto

2. ¿Firewall permite conexiones?
   - En el servidor: sudo ufw status
   - Si está activo: sudo ufw allow 27888

3. ¿El puerto es correcto?
   - Kaillera por defecto: 27888
   - Verifica configuración del servidor

4. ¿Puedes hacer telnet?
   - telnet {} {}

5. ¿El emulador REALMENTE conecta?
   - Abre RMG Kaillera Edition
   - Intenta conectar a {}: {}
   - ¿Funciona?
""".format(hostname, port, hostname, port))
    else:
        print("""
✅ El servidor está accesible por TCP

Si el emulador conecta pero el bot no:
1. El protocolo es diferente
2. Revisa el archivo kaillera_response.txt
3. Necesitamos ver qué envía el emulador
""")

if __name__ == "__main__":
    main()
