import threading
import os
import xml.etree.ElementTree as ET
import datetime

log_lock = threading.Lock()

def log_message(mittente, ip, contenuto, filename="utils\\log.xml"):
    """
    Funzione thread-safe per loggare messaggi in formato XML.
    Usa 'with log_lock' per bloccare l'accesso al file durante la scrittura.
    """
    os.makedirs("utils", exist_ok=True)
    
    with log_lock:  # ACQUISIZIONE LOCK
        try:
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
            ET.SubElement(message, "contenuto").text = str(contenuto)
            
            ET.indent(tree, space="    ", level=0)
            tree.write(filename, encoding="utf-8", xml_declaration=True)
            
            # Rigenera l'HTML subito dopo aver aggiornato l'XML (sempre sotto lock)
            generate_html_log()
            
        except Exception as e:
            print(f"[LOG ERROR] Impossibile scrivere il log: {e}")

def generate_html_log():
    """Genera l'HTML. Questa funzione è chiamata DENTRO il lock di log_message"""
    xml_file = 'utils\\log.xml'
    html_file = xml_file.replace(".xml", ".html")
    
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        
        html_content = """<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Global Network Log</title>
    <style>
        body { font-family: 'Lucida Console', monospace; background-color: #0B2027; color: #5B7981; padding: 25px; }
        .log-entry { margin: 15px 4px; padding: 10px; border-left: 10px solid; }
        .log-entry.client { border-color: #E4B8B7; background-color: #583A38; }
        .log-entry.server { border-color: #AAD2DA; background-color: #2D4B4F; }
        .field { margin: 5px 0; }
        .label { font-weight: bold; color: #FFECAD; }
        .timestamp { color: #FFA09E; }
        .sender { color: #85EBFF; }
        .ip { color: #FFB74D; }
        .contenuto { color: #ebeaea; }
        h1 { color: #FFECAD; border-bottom: 4px solid #555; padding-bottom: 10px; }
    </style>
</head>
<body>
    <h1>🖥️ Log</h1>
"""
        # Invertiamo l'ordine per vedere i messaggi più recenti in alto (opzionale, rimuovi [::-1] se non vuoi)
        messages = root.findall("message")
        
        for message in messages:
            sender = message.find("sender").text
            # Se il mittente è SERVER lo coloriamo verde, altrimenti (i client) blu
            status_class = "server" if sender == "SERVER" else "client"
            
            html_content += f'    <div class="log-entry {status_class}">\n'
            html_content += f'        <div class="field"><span class="label">TIMESTAMP:</span> <span class="timestamp">{message.find("timestamp").text}</span></div>\n'
            html_content += f'        <div class="field"><span class="label">SENDER:</span> <span class="sender">{sender}</span></div>\n'
            html_content += f'        <div class="field"><span class="label">IP:</span> <span class="ip">{message.find("ip").text}</span></div>\n'
            html_content += f'        <div class="field"><span class="label">CONTENUTO:</span> <span class="contenuto">{message.find("contenuto").text}</span></div>\n'
            html_content += '    </div>\n'
        
        html_content += """</body></html>"""
        
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)
            
    except Exception as e:
        print(f"[HTML ERROR] {e}")