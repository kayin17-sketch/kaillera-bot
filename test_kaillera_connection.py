#!/usr/bin/env python3
"""Script para diagnosticar conexion a servidor Kaillera."""

import socket
import sys
import time as time_module

def parse_server_status(data):
    """Parsea mensaje ServerStatus."""
    if len(data) < 10:
        print("   Datos muy cortos")
        return
    
    pos = 6
    pos += 1
    num_users = int.from_bytes(data[pos:pos+4], 'little')
    pos += 4
    num_games = int.from_bytes(data[pos:pos+4], 'little')
    pos += 4
    
    print(f"   Usuarios: {num_users}, Partidas: {num_games}")
    
    users = []
    for i in range(num_users):
        name_start = pos
        while pos < len(data) and data[pos] != 0:
            pos += 1
        name = data[name_start:pos].decode('latin-1', errors='ignore')
        pos += 1
        ping = int.from_bytes(data[pos:pos+4], 'little')
        pos += 4
        status = data[pos]
        pos += 1
        user_id = int.from_bytes(data[pos:pos+2], 'little')
        pos += 2
        conn_type = data[pos]
        pos += 1
        users.append({'name': name, 'ping': ping, 'id': user_id})
    
    print(f"   Lista de usuarios:")
    for u in users:
        print(f"     - {u['name']} (ping: {u['ping']}ms)")
    
    games = []
    for i in range(num_games):
        name_start = pos
        while pos < len(data) and data[pos] != 0:
            pos += 1
        game_name = data[name_start:pos].decode('latin-1', errors='ignore')
        pos += 1
        game_id = int.from_bytes(data[pos:pos+4], 'little')
        pos += 4
        
        client_start = pos
        while pos < len(data) and data[pos] != 0:
            pos += 1
        client = data[client_start:pos].decode('latin-1', errors='ignore')
        pos += 1
        
        creator_start = pos
        while pos < len(data) and data[pos] != 0:
            pos += 1
        creator = data[creator_start:pos].decode('latin-1', errors='ignore')
        pos += 1
        
        players_start = pos
        while pos < len(data) and data[pos] != 0:
            pos += 1
        players_str = data[players_start:pos].decode('latin-1', errors='ignore')
        pos += 1
        
        status = data[pos] if pos < len(data) else 0
        pos += 1
        
        games.append({'name': game_name, 'id': game_id, 'creator': creator, 'players': players_str})
    
    print(f"   Lista de partidas:")
    for g in games:
        print(f"     - {g['name']} ({g['players']}) por {g['creator']}")

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
                    
                    if msg_type == 0x05:
                        print("\n3. ServerAck recibido, enviando ClientAck...")
                        ack_msg = b"\x01"
                        ack_msg += msg_num.to_bytes(2, 'little')
                        ack_msg += (17).to_bytes(2, 'little')
                        ack_msg += b"\x06"
                        ack_msg += (0).to_bytes(4, 'little')
                        ack_msg += (1).to_bytes(4, 'little')
                        ack_msg += (2).to_bytes(4, 'little')
                        ack_msg += (3).to_bytes(4, 'little')
                        
                        print(f"   ACK body length: {len(ack_msg) - 5}")
                        print(f"   Enviando ACK (msg_num={msg_num}): {ack_msg.hex()}")
                        sock.sendto(ack_msg, (address, port))
                        last_ack_time = time_module.time()
                        
                        print("\n4. Solicitando lista de juegos...")
                        get_games_msg = b"\x01"
                        get_games_msg += (1).to_bytes(2, 'little')
                        get_games_msg += (6).to_bytes(2, 'little')
                        get_games_msg += b"\x08"
                        get_games_msg += b"\x00"
                        print(f"   GetGames: {get_games_msg.hex()}")
                        sock.sendto(get_games_msg, (address, port))
                        
                        print("   Esperando mensajes (30 segundos)...")
                        sock.settimeout(3)
                        
                        msg_count = 0
                        
                        for i in range(30):
                            try:
                                current_time = time_module.time()
                                if current_time - last_ack_time > 5:
                                    ack_response = b"\x01"
                                    ack_response += msg_num.to_bytes(2, 'little')
                                    ack_response += (17).to_bytes(2, 'little')
                                    ack_response += b"\x06"
                                    ack_response += (0).to_bytes(4, 'little')
                                    ack_response += (1).to_bytes(4, 'little')
                                    ack_response += (2).to_bytes(4, 'little')
                                    ack_response += (3).to_bytes(4, 'little')
                                    sock.sendto(ack_response, (address, port))
                                    last_ack_time = current_time
                                
                                data, addr = sock.recvfrom(8192)
                                msg_count += 1
                                print(f"\n   Mensaje {msg_count}: {len(data)} bytes - HEX: {data.hex()}")
                                
                                if len(data) > 0:
                                    msg_count_in_bundle = data[0]
                                    print(f"   Messages in bundle: {msg_count_in_bundle}")
                                    
                                    pos = 1
                                    for j in range(msg_count_in_bundle):
                                        if pos + 5 > len(data):
                                            break
                                            
                                        msg_num_r = int.from_bytes(data[pos:pos+2], 'little')
                                        pos += 2
                                        msg_len = int.from_bytes(data[pos:pos+2], 'little')
                                        pos += 2
                                        msg_type = data[pos]
                                        pos += 1
                                        
                                        print(f"   [Msg {j+1}] num: {msg_num_r}, len: {msg_len}, type: {msg_type:#x}")
                                        
                                        if msg_type == 0x04:
                                            print("\n   *** ServerStatus recibido! ***")
                                            parse_server_status(data)
                                            return
                                        elif msg_type == 0x05:
                                            msg_num = msg_num_r
                                            print("   ServerAck (keepalive)")
                                        
                                        pos += msg_len - 5
                                        
                            except socket.timeout:
                                pass
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
