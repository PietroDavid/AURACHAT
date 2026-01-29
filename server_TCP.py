import socket
import datetime
import xml.etree.ElementTree as ET
import os
import threading
from logger import log_message, generate_html_log

def broadcast_server_presence(server_ip, tcp_port):
    """Trasmette in broadcast l'IP del server sulla rete locale"""
    BROADCAST_PORT = 37020
    TCP_PORT = tcp_port
    
    # Crea socket UDP per broadcast
    broadcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    broadcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    print(f" Servizio di broadcast attivo (UDP porta {BROADCAST_PORT})")
    print(f"   Trasmetto: {server_ip}:{TCP_PORT}\n")
    
    while True:
        try:
            # Messaggio di broadcast con formato: SERVER_DISCOVERY:IP:PORTA
            message = f"SERVER_DISCOVERY:{server_ip}:{TCP_PORT}"
            broadcast_sock.sendto(message.encode(), ('<broadcast>', BROADCAST_PORT))
            threading.Event().wait(2)  # Invia ogni 2 secondi
        except Exception as e:
            print(f"Errore broadcast: {e}")
            break

def gestisci_client(client_socket, client_address):
    """Funzione che gestisce la comunicazione con UN SINGOLO client"""
    print(f"[THREAD] Nuovo client connesso: {client_address}")
    
    try:
        while True:
            data = client_socket.recv(1024).decode()
            
            if not data:
                break
                
            print(f"[{client_address}] Messaggio ricevuto: {data}")
            generate_html_log()
            
            if data.upper() == "EXIT":
                risposta = "-1"
                client_socket.send(risposta.encode())
                log_message(mittente="SERVER", ip=client_address[0], contenuto=risposta)
                generate_html_log()
                break
                
            elif data.upper() == "TIME":
                time = datetime.datetime.now()
                risposta = f"{time.hour}:{time.minute}:{time.second}"
                client_socket.send(risposta.encode())
                log_message(mittente="SERVER", ip=client_address[0], contenuto=risposta)
                generate_html_log()

            elif data.upper() == "NAME":
                risposta = f"Sono il server: {socket.gethostname()}"
                client_socket.send(risposta.encode())
                log_message(mittente="SERVER", ip=client_address[0], contenuto=risposta)
                generate_html_log()

            else: 
                risposta = f"Ciao {client_address[0]}, ho ricevuto: '{data}'"
                client_socket.send(risposta.encode())
                log_message(mittente="SERVER", ip=client_address[0], contenuto=risposta)
                generate_html_log()
    
    except Exception as e:
        print(f"[ERRORE] Client {client_address}: {e}")
    
    finally:
        client_socket.close()
        print(f"[THREAD] Client {client_address} disconnesso")

# ========== AVVIO SERVER ==========

# Ottieni e mostra l'IP del server
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
except:
    local_ip = "127.0.0.1"
finally:
    s.close()

print("=" * 60)
print(" SERVER TCP CON AUTO-DISCOVERY")
print("=" * 60)
print(f" IP del server: {local_ip}")
print(f" Porta TCP: 12345")
print(f" Porta Broadcast: 37020")
print("=" * 60)
print()

# Avvia thread per il broadcast
broadcast_thread = threading.Thread(target=broadcast_server_presence, args=(local_ip, 12345), daemon=True)
broadcast_thread.start()

# Creazione del socket TCP
SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
SERVER.bind((local_ip, 12345))
SERVER.listen(5)

print(" Server TCP in ascolto sulla porta 12345...")
print(" In attesa di client...\n")

try:
    while True:
        client_socket, client_address = SERVER.accept()
        client_thread = threading.Thread(target=gestisci_client, args=(client_socket, client_address))
        client_thread.daemon = True
        client_thread.start()   
        print(f" Thread avviato per {client_address}\n")

except KeyboardInterrupt:
    print("\n\n Server interrotto dall'utente")
finally:
    SERVER.close()
    print(" Server chiuso correttamente")