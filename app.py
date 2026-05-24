from flask import Flask, render_template, request, jsonify
import multiprocessing
import sys
import io
import traceback
import re
import random

app = Flask(__name__)

def translate_error(error_str):
    """
    Übersetzt kryptische Python-Fehlermeldungen in kindgerechte, 
    motivierende Erklärungen auf Deutsch mit passenden Emojis.
    """
    if "ZeroDivisionError" in error_str:
        return "Hoppla! Du versuchst, durch 0 zu teilen. Das mag die Mathematik gar nicht! 🛑"
        
    elif "NameError" in error_str:
        match = re.search(r"name '(\w+)' is not defined", error_str)
        var_name = match.group(1) if match else "unbekannt"
        return f"Du hast eine Variable namens '{var_name}' benutzt, die der Computer noch nicht kennt. Hast du dich vielleicht vertippt? 🔍"
        
    elif "SyntaxError" in error_str:
        return "Ein Rechtschreibfehler im Code! Schau genau hin, ob irgendwo ein Doppelpunkt (:), eine Klammer oder ein Anführungszeichen fehlt. 📝"
        
    elif "IndexError" in error_str:
        return "Du greifst auf ein Element in einer Liste zu, das gar nicht existiert (z. B. das 5. Element bei einer Liste mit nur 3 Dingen). 📊"
        
    elif "TypeError" in error_str:
        return "Hier passen die Datentypen nicht zusammen (z. B. wenn du Text mit einer Zahl addieren möchtest). Nutze dafür den 'erstelle Text aus' Block! 🧩"
        
    # Standard-Rückgabe, falls kein bekannter Fehler gematcht wurde (die letzte Zeile des Tracebacks)
    error_lines = error_str.strip().split('\n')
    return f"Fehler ❌:\n{error_lines[-1] if error_lines else 'Unbekannter Fehler'}"

def mock_input(prompt=""):
    """
    Simuliert die klassische Python input() Funktion, damit der 
    Server bei Benutzerabfragen im Klassenzimmer nicht hängen bleibt.
    """
    if prompt:
        print(prompt)
    
    # Eine Liste lustiger, zufälliger Schülernamen zur Simulation
    namen = ["Emma 👧", "Nico 👦", "Lukas 🎒", "Mia 🌸", "Leo 🦁", "Sofia 🎈"]
    gewaehlter_name = random.choice(namen)
    print(f"-> [Automatische Antwort]: {gewaehlter_name}")
    return gewaehlter_name

def execute_student_code(code, return_dict, pressed_keys):
    """
    Diese Funktion läuft isoliert in einem eigenen Prozess.
    Dadurch ist der Haupt-Webserver vor blockierenden Endlosschleifen geschützt.
    """
    redirected_output = io.StringIO()
    sys.stdout = redirected_output
    
    try:
        # Wir modifizieren die "builtins", um blockierende input() Befehle zu ersetzen
        builtins_dict = __import__('builtins').__dict__.copy()
        builtins_dict['input'] = mock_input
        builtins_dict['raw_input'] = mock_input
        
        # Funktion zur Abfrage des interaktiven Tastendrucks im Sandbox-System
        def is_key_pressed(key):
            is_pressed = str(key).lower() in [str(k).lower() for k in pressed_keys]
            print(f"📡 Prüfe Taste [{str(key).upper()}]: {'GEDRÜCKT! 🟢' if is_pressed else 'nicht gedrückt 🔴'}")
            return is_pressed
            
        builtins_dict['is_key_pressed'] = is_key_pressed
        
        local_scope = {}
        # Ausführung des Schüler-Codes mit den modifizierten Sandbox-Optionen
        exec(code, {"__builtins__": builtins_dict}, local_scope)
        
        return_dict['output'] = redirected_output.getvalue()
        return_dict['error'] = None
    except Exception as e:
        return_dict['error'] = traceback.format_exc()
    finally:
        sys.stdout = sys.__stdout__

@app.route('/')
def index():
    """Rendert die Blockly-Hauptseite im Browser."""
    return render_template('index.html')

@app.route('/run_code', methods=['POST'])
def run_code():
    """
    Empfängt den Python-Code und die aktuell gedrückten Tasten des Frontends,
    führt sie in der isolierten Sandbox aus und liefert die Ausgabe zurück.
    """
    data = request.get_json() or {}
    code = data.get('code', '')
    pressed_keys = data.get('pressed_keys', [])  # Holt gedrückte Tasten vom Client-Browser
    
    # Manager für die sichere Datenübertragung zwischen den Prozessen
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    
    # Starte den Sandbox-Prozess mit einem harten Timeout-Schutz
    p = multiprocessing.Process(
        target=execute_student_code, 
        args=(code, return_dict, pressed_keys)
    )
    p.start()
    
    # Maximal 2.0 Sekunden auf die Ausführung warten
    p.join(2.0)
    
    # Falls der Prozess noch lebt, handelt es sich um eine Endlosschleife
    if p.is_alive():
        p.terminate()
        p.join()
        return jsonify({
            'output': 'Fehler ❌:\nZeitüberschreitung! Hast du eine unendliche "wiederhole solange"-Schleife gebaut? ⏳'
        })
    
    # Fehlerprüfung und ggf. Übersetzung
    if return_dict.get('error'):
        user_friendly_error = translate_error(return_dict['error'])
        return jsonify({'output': user_friendly_error})
        
    output = return_dict.get('output', '')
    return jsonify({
        'output': output if output else "Dein Programm wurde erfolgreich ausgeführt! (Es gab aber keine Textausgabe mit 'gib aus'.)"
    })

if __name__ == '__main__':
    # Aktiviert den Debugger für lokale Tests vor dem Deployment
    app.run(debug=True)
```
eof

### Übersicht der Backend-Architektur:
* **Präzises Timeout-Management:** Die Zeitüberschreitungs-Meldung wurde kindgerecht aufbereitet und mit einer Sanduhr (`⏳`) versehen, falls Schüler eine Endlosschleife konstruieren.
* **Intelligente Simulation:** Der `input()`-Ersatz simuliert nun automatisch eine Schülerantwort mit wechselnden Emojis in der Konsole. Das macht die Terminal-Ausgabe lebendiger.
* **Vollständige Tastenabfrage:** Die Liste der gedrückten Tasten (`pressed_keys`) wird sicher aus dem Request extrahiert und der virtuellen Funktion `is_key_pressed()` im Sandkasten zur Verfügung gestellt.
