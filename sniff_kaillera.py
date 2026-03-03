#!/usr/bin/env python3
"""
Script para capturar tráfico del emulador Kaillera y ver el protocolo real.

INSTRUCCIONES:
1. Ejecuta este script
2. Conecta tu emulador al servidor
3. Observa los paquetes que envía el emulador
4. Podremos implementar el protocolo correcto
"""

import socket
import struct
import threading
import time
from datetime import datetime


class KailleraProtocolSniffer:
    """Captura tráfico entre emulador y servidor Kaillera."""
    
    def __init__(self, listen_port=27888, server_address=None, server_port=27888):
        self.listen_port = listen_port
        self.server_address = server_address
        self.server_port = server_port
        self.running = False
        
        self.client_socket = None
        self.server_socket = None
        
        self.packets_captured = []
    
    def start_proxy(self):
        """Inicia proxy para capturar tráfico."""
        print("=" * 60)
        print("SNIFFER DE PROTOCOLO KAILLERA")
        print("=" * 60)
        print(f"\n🔧 Configuración:")
        print(f"   Puerto local: {self.listen_port}")
        if self.server_address:
            print(f"   Servidor real: {self.server_address}:{self.server_port}")
        
        print("\n📋 Instrucciones:")
        print("   1. Configura tu emulador para conectar a: 127.0.0.1:27888")
        print("   2. Este proxy capturará todo el tráfico")
        print("   3. Conecta con el emulador")
        print("   4. Los paquetes se mostrarán aquí")
        print("\n⏳ Esperando conexión del emulador...\n")
        
        try:
            # Socket para escuchar emulador
            listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listen_socket.bind(('0.0.0.0', self.listen_port))
            listen_socket.listen(1)
            
            print(f"✅ Escuchando en 127.0.0.1:{self.listen_port}")
            
            # Aceptar conexión del emulador
            self.client_socket, client_addr = listen_socket.accept()
            print(f"\n🎮 Emulador conectado desde: {client_addr}")
            
            # Si tenemos servidor real, conectar
            if self.server_address:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.connect((self.server_address, self.server_port))
                print(f"✅ Conectado al servidor real: {self.server_address}:{self.server_port}")
                
                # Iniciar proxy bidireccional
                self.running = True
                
                # Thread: Emulador -> Servidor
                threading.Thread(
                    target=self._forward_client_to_server,
                    daemon=True
                ).start()
                
                # Thread: Servidor -> Emulador
                threading.Thread(
                    target=self._forward_server_to_client,
                    daemon=True
                ).start()
            else:
                # Solo capturar lo que envía el emulador
                self.running = True
                threading.Thread(
                    target=self._capture_client_only,
                    daemon=True
                ).start()
            
            # Mantener activo
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Detenido por usuario")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        finally:
            self.running = False
            if self.client_socket:
                self.client_socket.close()
            if self.server_socket:
                self.server_socket.close()
            
            # Guardar paquetes capturados
            self._save_packets()
    
    def _forward_client_to_server(self):
        """Reenvía datos del emulador al servidor."""
        try:
            while self.running:
                data = self.client_socket.recv(4096)
                if not data:
                    break
                
                # Mostrar paquete
                self._display_packet("EMULADOR → SERVIDOR", data, outbound=True)
                
                # Reenviar al servidor
                self.server_socket.send(data)
                
        except Exception as e:
            print(f"Error en forward client->server: {e}")
            self.running = False
    
    def _forward_server_to_client(self):
        """Reenvía datos del servidor al emulador."""
        try:
            while self.running:
                data = self.server_socket.recv(4096)
                if not data:
                    break
                
                # Mostrar paquete
                self._display_packet("SERVIDOR → EMULADOR", data, outbound=False)
                
                # Reenviar al emulador
                self.client_socket.send(data)
                
        except Exception as e:
            print(f"Error en forward server->client: {e}")
            self.running = False
    
    def _capture_client_only(self):
        """Solo captura lo que envía el emulador."""
        try:
            while self.running:
                data = self.client_socket.recv(4096)
                if not data:
                    break
                
                # Mostrar paquete
                self._display_packet("EMULADOR (sin servidor)", data, outbound=True)
                
        except Exception as e:
            print(f"Error capturando: {e}")
            self.running = False
    
    def _display_packet(self, direction, data, outbound=True):
        """Muestra un paquete capturado."""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        print("\n" + "=" * 60)
        print(f"[{timestamp}] {direction}")
        print("=" * 60)
        print(f"Tamaño: {len(data)} bytes")
        
        # Hex dump
        print("\n📦 HEX:")
        hex_str = ' '.join(f'{b:02x}' for b in data[:64])
        print(f"   {hex_str}")
        if len(data) > 64:
            print(f"   ... ({len(data) - 64} bytes más)")
        
        # ASCII (si es imprimible)
        print("\n📝 ASCII:")
        try:
            ascii_str = data.decode('utf-8', errors='replace')[:64]
            print(f"   {repr(ascii_str)}")
        except:
            print("   (no es texto)")
        
        # Intentar parsear como texto
        print("\n📄 TEXTO (si aplica):")
        try:
            text = data.decode('utf-8', errors='ignore').strip()
            if text and text.isprintable():
                print(f"   {text}")
        except:
            pass
        
        # Guardar
        packet_info = {
            'timestamp': timestamp,
            'direction': direction,
            'size': len(data),
            'hex': data.hex(),
            'outbound': outbound
        }
        self.packets_captured.append(packet_info)
    
    def _save_packets(self):
        """Guarda paquetes capturados a archivo."""
        if not self.packets_captured:
            return
        
        filename = f"kaillera_traffic_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        print(f"\n\n💾 Guardando {len(self.packets_captured)} paquetes en {filename}")
        
        with open(filename, 'w') as f:
            f.write("TRÁFICO KAILLERA CAPTURADO\n")
            f.write("=" * 60 + "\n\n")
            
            for packet in self.packets_captured:
                f.write(f"Timestamp: {packet['timestamp']}\n")
                f.write(f"Dirección: {packet['direction']}\n")
                f.write(f"Tamaño: {packet['size']} bytes\n")
                f.write(f"Hex: {packet['hex']}\n")
                f.write("\n" + "-" * 60 + "\n\n")
        
        print("✅ Archivo guardado")


def main():
    import sys
    
    print("\n🔧 CONFIGURACIÓN:")
    print("   Este sniffer puede trabajar en 2 modos:\n")
    print("   MODO 1: Solo captura (sin servidor)")
    print("     - Solo verás lo que envía el emulador")
    print("     - No habrá respuesta del servidor")
    print("     - Útil para ver el handshake inicial\n")
    print("   MODO 2: Proxy (con servidor real)")
    print("     - Captura tráfico en ambas direcciones")
    print("     - El emulador funcionará normalmente")
    print("     - Verás el protocolo completo\n")
    
    modo = input("Modo (1=solo captura, 2=proxy): ").strip()
    
    if modo == "2":
        server = input("Dirección del servidor real (ej: tu-servidor.com): ").strip()
        port_str = input("Puerto del servidor (Enter para 27888): ").strip()
        port = int(port_str) if port_str else 27888
        
        sniffer = KailleraProtocolSniffer(
            listen_port=27888,
            server_address=server,
            server_port=port
        )
    else:
        sniffer = KailleraProtocolSniffer(listen_port=27888)
    
    sniffer.start_proxy()


if __name__ == "__main__":
    main()
