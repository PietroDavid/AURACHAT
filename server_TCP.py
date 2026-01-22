import socket
import datetime
import xml.etree.ElementTree as ET
import os
import threading

def log_message(mittente, ip, contenuto, filename="utils\\log_server.xml"):
    """Funzione per loggare messaggi in formato XML"""
    os.makedirs("utils", exist_ok=True)
    
    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        root = ET.Element("logs")
        tree = ET.ElementTree(root)
        tree.write(filename, encoding="utf-8", xml_declaration=True)

    tree = ET.parse(filename)
    root = tree.getroot()
    message = ET.SubElement(root, "message")
    ET.SubElement(message, "timestamp").text = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ET.SubElement(message, "sender").text = mittente
    ET.SubElement(message, "ip").text = ip
    ET.SubElement(message, "contenuto").text = contenuto
    ET.indent(tree, space="    ", level=0)
    tree.write(filename, encoding="utf-8", xml_declaration=True)

def generate_html_log():
    """Genera un file HTML con i log colorati del SERVER"""
    log_file = "utils\\log_server.xml"
    html_file = "utils\\log_server.html"
    
    if not os.path.exists(log_file):
        return
    
    tree = ET.parse(log_file)
    root = tree.getroot()
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Server Log</title>
    <style>
        body { font-family: 'Courier New', monospace; background-color: #1e1e1e; color: #d4d4d4; padding: 20px; }
        .log-entry { margin: 15px 0; padding: 10px; border-left: 4px solid; }
        .log-entry.client { border-color: #4FC3F7; background-color: #2d3d4d; }
        .log-entry.server { border-color: #81C784; background-color: #2d3d2d; }
        .field { margin: 5px 0; }
        .label { font-weight: bold; color: #FFB74D; }
        .timestamp { color: #CE93D8; }
        .sender { color: #4FC3F7; }
        .ip { color: #FFB74D; }
        .contenuto { color: #d4d4d4; }
        h1 { color: #81C784; }
    </style>
</head>
<body>
    <h1>🖥️ Server Log (Auto-Discovery)</h1>
"""
    
    for message in root.findall("message"):
        sender = message.find("sender").text
        status_class = "client" if sender == "CLIENT" else "server"
        html_content += f'    <div class="log-entry {status_class}">\n'
        html_content += f'        <div class="field"><span class="label">TIMESTAMP:</span> <span class="timestamp">{message.find("timestamp").text}</span></div>\n'
        html_content += f'        <div class="field"><span class="label">SENDER:</span> <span class="sender">{sender}</span></div>\n'
        html_content += f'        <div class="field"><span class="label">IP:</span> <span class="ip">{message.find("ip").text}</span></div>\n'
        html_content += f'        <div class="field"><span class="label">CONTENUTO:</span> <span class="contenuto">{message.find("contenuto").text}</span></div>\n'
        html_content += '    </div>\n'
    
    html_content += """</body>
</html>"""
    
    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)

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
            log_message(mittente="CLIENT", ip=client_address[0], contenuto=data)
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