import socket
import datetime
import xml.etree.ElementTree as ET
import os

def log_message(mittente, ip, contenuto, filename="utils\\log_client.xml"):
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
    """Genera un file HTML con i log colorati del CLIENT"""
    log_file = "utils\\log_client.xml"
    html_file = "utils\\log_client.html"
    
    if not os.path.exists(log_file):
        return
    
    tree = ET.parse(log_file)
    root = tree.getroot()
    
    html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Client Log</title>
    <style>
        body { font-family: 'Andale mono', monospace; background-color: #0B2027; color: #E4B8B7; padding: 20px; }
        .log-entry { margin: 15px 0; padding: 10px; border-left: 4px solid; }
        .log-entry.client { border-color: #E4B8B7; background-color: #401A18; }
        .log-entry.server { border-color: #AAD2DA; background-color: #1B464D; }
        .field { margin: 5px 0; }
        .label { font-weight: bold; color: #E4B8B7; }
        .timestamp { color: #CE93D8; }
        .sender { color: #4FC3F7; }
        .ip { color: #FFB74D; }
        .contenuto { color: #d4d4d4; }
        h1 { color: #E4B8B7; }
    </style>
</head>
<body>
    <h1>📋 Client Log (Auto-Discovery)</h1>
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
        log_message(mittente="SERVER", ip=SERVER_IP, contenuto=data)
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