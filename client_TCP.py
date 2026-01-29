import socket
import datetime
import xml.etree.ElementTree as ET
import os
from logger import log_message, generate_html_log

def discover_server(timeout=10):
    """Cerca il server sulla rete locale tramite broadcast UDP"""
    BROADCAST_PORT = 37020
    
    print(" Ricerca del server sulla rete locale...")
    print(f"   Ascolto broadcast sulla porta {BROADCAST_PORT}")
    print(f"   Timeout: {timeout} secondi\n")
    
    # Crea socket UDP
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(("", BROADCAST_PORT))
    sock.settimeout(timeout)
    
    try:
        while True:
            data, addr = sock.recvfrom(1024)
            message = data.decode()
            
            # Verifica che il messaggio sia dal server
            if message.startswith("SERVER_DISCOVERY:"):
                parts = message.split(":")
                if len(parts) == 3:
                    server_ip = parts[1]
                    server_port = int(parts[2])
                    
                    print(f" Server trovato!")
                    print(f"   IP: {server_ip}")
                    print(f"   Porta: {server_port}\n")
                    
                    sock.close()
                    return server_ip, server_port
    
    except socket.timeout:
        print(" Timeout: Nessun server trovato sulla rete")
        sock.close()
        return None, None
    except Exception as e:
        print(f"Errore durante la ricerca: {e}")
        sock.close()
        return None, None

# ========== AVVIO CLIENT ==========

print("=" * 60)
print(" CLIENT TCP CON AUTO-DISCOVERY")
print("=" * 60)
print()

# Chiedi all'utente se vuole cercare automaticamente o inserire manualmente
SERVER_IP, SERVER_PORT = discover_server(timeout=10)
    
if SERVER_IP is None:
    print(" Discovery fallita: inserisci manualmente IP e porta del server")
    SERVER_IP = input("IP server: ").strip()
    port_input = input("Porta server (default 12345): ").strip()
    SERVER_PORT = int(port_input) if port_input else 12345

print(f"\n Connessione a {SERVER_IP}:{SERVER_PORT}...")

# Creazione del socket client
CLIENT = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    CLIENT.connect((SERVER_IP, SERVER_PORT))
    print(f" Connesso al server!\n")

    while True:
        mess = input("[CLIENT] --> Inserisci un messaggio da inviare: ")
        CLIENT.send(mess.encode())
        
        log_message(mittente="CLIENT", ip=SERVER_IP, contenuto=mess)
        generate_html_log()
        
        data = CLIENT.recv(1024).decode()

        if data == "-1":
            print("[SERVER] --> Disconnessione richiesta dal server")
            CLIENT.close()
            break

        print(f"[SERVER] --> {data}")
        generate_html_log()

except ConnectionRefusedError:
    print(f" ERRORE: Impossibile connettersi a {SERVER_IP}:{SERVER_PORT}")
    print("   Verifica che:")
    print("   1. Il server sia in esecuzione")
    print("   2. Il firewall permetta la connessione")
except Exception as e:
    print(f" ERRORE: {e}")
finally:
    CLIENT.close()
    print("\n Client chiuso")