#!/usr/bin/env python3
"""
Capturador SIMPLE de paquetes Kaillera.
Siempre genera un archivo, incluso si hay errores.
"""

import socket
import sys
from datetime import datetime

def main():
    print("=" * 60)
    print("CAPTURADOR SIMPLE KAILLERA")
    print("=" * 60)
    
    # Pedir datos
    server_host = input("\nHostname/IP del servidor Kaillera: ").strip()
    if not server_host:
        print("❌ Error: Debes ingresar un hostname/IP")
        return
    
    server_port_str = input("Puerto (Enter para 27888): ").strip()
    server_port = int(server_port_str) if server_port_str else 27888
    
    # Nombre del archivo
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"kaillera_traffic_{timestamp}.txt"
    
    print(f"\n📄 Archivo de salida: {filename}")
    print(f"🎯 Servidor: {server_host}:{server_port}")
    
    # Crear archivo desde el inicio
    with open(filename, 'w') as f:
        f.write("CAPTURA DE TRÁFICO KAILLERA\n")
        f.write("=" * 60 + "\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Servidor: {server_host}:{server_port}\n")
        f.write("=" * 60 + "\n\n")
    
    print("\n✅ Archivo creado")
    
    # Intentar conectar
    print(f"\n🔍 Conectando a {server_host}:{server_port}...")
    
    try:
        # Resolver DNS
        ip = socket.gethostbyname(server_host)
        print(f"   DNS: {server_host} -> {ip}")
        
        # Crear socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        
        # Conectar
        sock.connect((ip, server_port))
        print(f"   ✅ Conectado a {ip}:{server_port}")
        
        # Guardar info de conexión
        with open(filename, 'a') as f:
            f.write("CONEXIÓN EXITOSA\n")
            f.write(f"IP: {ip}\n")
            f.write(f"Puerto: {server_port}\n")
            f.write("\n" + "-" * 60 + "\n\n")
        
        # Intentar recibir datos
        print("\n📥 Esperando datos del servidor...")
        
        try:
            sock.settimeout(3)
            data = sock.recv(4096)
            
            if data:
                print(f"   ✅ Recibidos {len(data)} bytes")
                
                # Guardar datos recibidos
                with open(filename, 'a') as f:
                    f.write("DATOS RECIBIDOS DEL SERVIDOR\n")
                    f.write(f"Tamaño: {len(data)} bytes\n\n")
                    
                    # Hex dump
                    f.write("HEX:\n")
                    hex_lines = []
                    for i in range(0, len(data), 16):
                        hex_part = ' '.join(f'{b:02x}' for b in data[i:i+16])
                        ascii_part = ''.join(chr(b) if 32 <= b < 127 else '.' for b in data[i:i+16])
                        hex_lines.append(f"  {hex_part:<48}  {ascii_part}")
                    f.write('\n'.join(hex_lines))
                    f.write("\n\n")
                    
                    # Intentar como texto
                    try:
                        text = data.decode('utf-8', errors='replace')
                        f.write("TEXTO (UTF-8):\n")
                        f.write(f"  {repr(text)}\n")
                    except:
                        pass
                    
                    f.write("\n" + "-" * 60 + "\n\n")
                
                print(f"   💾 Datos guardados en {filename}")
            
            else:
                print("   ⚠️  El servidor no envió datos")
                with open(filename, 'a') as f:
                    f.write("El servidor NO envió datos iniciales\n")
        
        except socket.timeout:
            print("   ⚠️  Timeout esperando datos")
            with open(filename, 'a') as f:
                f.write("TIMEOUT: El servidor no envió datos en 3 segundos\n")
        
        # Ahora intentar enviar algo
        print("\n📤 Enviando datos de prueba...")
        
        # Intentar diferentes tipos de handshake
        test_packets = [
            ("Texto simple", b"HELLO\n"),
            ("Texto con usuario", b"HELLO\nTestBot\n"),
            ("Binario Kaillera", b"KAILLERA\x00\x01\x00\x00\x00\x00"),
        ]
        
        with open(filename, 'a') as f:
            f.write("INTENTOS DE HANDSHAKE\n")
            f.write("=" * 60 + "\n\n")
        
        for name, packet in test_packets:
            print(f"   Probando: {name}")
            
            with open(filename, 'a') as f:
                f.write(f"Enviando: {name}\n")
                f.write(f"Hex: {packet.hex()}\n")
            
            try:
                sock.send(packet)
                print(f"      ✅ Enviado")
                
                # Esperar respuesta
                sock.settimeout(2)
                try:
                    response = sock.recv(4096)
                    if response:
                        print(f"      📥 Respuesta: {len(response)} bytes")
                        
                        with open(filename, 'a') as f:
                            f.write(f"Respuesta: {len(response)} bytes\n")
                            f.write(f"Hex: {response.hex()}\n")
                            try:
                                f.write(f"Texto: {response.decode('utf-8', errors='replace')}\n")
                            except:
                                pass
                            f.write("\n")
                    else:
                        print(f"      ⚠️  Sin respuesta")
                        with open(filename, 'a') as f:
                            f.write("Sin respuesta\n\n")
                
                except socket.timeout:
                    print(f"      ⚠️  Timeout")
                    with open(filename, 'a') as f:
                        f.write("Timeout esperando respuesta\n\n")
                
                except Exception as e:
                    print(f"      ❌ Error: {e}")
                    with open(filename, 'a') as f:
                        f.write(f"Error: {e}\n\n")
                
                # Pausa entre intentos
                import time
                time.sleep(0.5)
                
            except Exception as e:
                print(f"      ❌ Error enviando: {e}")
                with open(filename, 'a') as f:
                    f.write(f"Error enviando: {e}\n\n")
        
        # Cerrar
        sock.close()
        
        print(f"\n✅ Captura completada")
        print(f"📄 Archivo guardado: {filename}")
        
        # Mostrar contenido
        print("\n" + "=" * 60)
        print("CONTENIDO DEL ARCHIVO:")
        print("=" * 60)
        with open(filename, 'r') as f:
            print(f.read())
    
    except socket.timeout:
        print(f"❌ Timeout conectando a {server_host}:{server_port}")
        with open(filename, 'a') as f:
            f.write(f"ERROR: Timeout conectando\n")
    
    except ConnectionRefusedError:
        print(f"❌ Conexión rechazada por {server_host}:{server_port}")
        with open(filename, 'a') as f:
            f.write(f"ERROR: Conexión rechazada\n")
            f.write("El servidor no está escuchando en ese puerto\n")
    
    except Exception as e:
        print(f"❌ Error: {e}")
        with open(filename, 'a') as f:
            f.write(f"ERROR: {e}\n")
    
    print(f"\n📄 Revisa el archivo: {filename}")


if __name__ == "__main__":
    main()
