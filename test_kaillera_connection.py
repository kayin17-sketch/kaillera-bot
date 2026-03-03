#!/usr/bin/env python3
"""Script para diagnosticar conexion a servidor Kaillera."""

import socket
import sys

def test_kaillera_server(address, port=27888):
    print(f"Probando conexion a {address}:{port}")
    
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(10)
        
        print("\n1. Enviando HELLO...")
        hello_msg = b"HELLO0.83\x00"
        print(f"   Mensaje: {hello_msg}")
        sock.sendto(hello_msg, (address, port))
        
        print("   Esperando respuesta...")
        data, addr = sock.recvfrom(1024)
        print(f"   Recibido {len(data)} bytes de {addr}")
        print(f"   Datos raw: {data}")
        print(f"   Datos hex: {data.hex()}")
        
        if data.startswith(b"HELLOD00D"):
            port_str = data[9:].rstrip(b'\x00').decode('latin-1')
            print(f"   HELLOD00D recibido! Puerto: {port_str}")
            
            print("\n2. Enviando login v086...")
            username = b"TestBot\x00"
            client_type = b"TestClient 1.0\x00"
            connection_type = b"\x02"
            
            body = username + client_type + connection_type
            msg_length = 1 + len(body)
            
            login_msg = b"\x01"
            login_msg += (0).to_bytes(2, 'little')
            login_msg += msg_length.to_bytes(2, 'little')
            login_msg += b"\x03"
            login_msg += body
            
            print(f"   Body length: {len(body)}, Total msg_length: {msg_length}")
            print(f"   Mensaje login: {login_msg.hex()}")
            sock.sendto(login_msg, (address, port))
            
            print("   Esperando respuesta...")
            data, addr = sock.recvfrom(8192)
            print(f"   Recibido {len(data)} bytes")
            print(f"   Datos hex: {data[:100].hex()}...")
            
            if len(data) > 0:
                print(f"   Primer byte (msg count): {data[0]}")
                if len(data) > 5:
                    msg_num = int.from_bytes(data[1:3], 'little')
                    msg_len = int.from_bytes(data[3:5], 'little')
                    msg_type = data[5]
                    print(f"   Msg num: {msg_num}, Msg len: {msg_len}, Msg type: {msg_type:#x}")
        else:
            print(f"   Respuesta inesperada: {data[:20]}")
        
        sock.close()
        print("\nConexion exitosa!")
        
    except socket.timeout:
        print("\nERROR: Timeout - el servidor no responde")
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python test_kaillera_connection.py <address> [port]")
        print("Ejemplo: python test_kaillera_connection.py kayinremix.duckdns.org 27888")
        sys.exit(1)
    
    address = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 27888
    
    test_kaillera_server(address, port)
