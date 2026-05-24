from flask import Flask, render_template, request, jsonify
import multiprocessing
import sys
import io
import traceback
import random
import re

app = Flask(__name__)

# Simuliertes Antwort-System für Eingabe-Fragen der Schüler (z.B. input() / Frage-Block)
def mock_input(prompt=""):
    if prompt:
        print(prompt) # Zeigt die Frage in der Konsole an
    
    # Eine Liste typischer Schülernamen für die Simulation
    names = ["Emma", "Nico", "Lukas", "Mia", "Maximilian", "Sofia", "David", "Laura"]
    chosen_name = random.choice(names)
    
    print(chosen_name) # Simuliert das Eintippen des Namens in der Konsole
    return chosen_name

# Kinderfreundliche Übersetzung von Python-Fehlermeldungen
def translate_error(error_traceback):
    if not error_traceback:
        return "Unbekannter Fehler ❌"
    
    error_lines = error_traceback.strip().split('\n')
    last_line = error_lines[-1]
    
    # Fehlerübersetzungen
    if "ZeroDivisionError" in last_line:
        return "Fehler ❌:\nUups! Du hast versucht, eine Zahl durch 0 zu teilen. Das ist in der Mathematik nicht erlaubt! 🧮"
        
    elif "NameError" in last_line:
        match = re.search(r"name '(.+)' is not defined", last_line)
        variable_name = f" '{match.group(1)}'" if match else ""
        return f"Fehler ❌:\nHoppla! Du verwendest ein Wort oder eine Variable{variable_name}, die der Computer noch nicht kennt. Hast du dich vielleicht vertippt oder vergessen, die Variable vorher zu erstellen? 🔍"
        
    elif "TypeError" in last_line:
        return "Fehler ❌:\nDa passen die Typen nicht zusammen! Beispielsweise kannst du Text nicht mit einer Zahl addieren, ohne sie vorher umzuwandeln. 🧩"
        
    elif "SyntaxError" in last_line:
        return "Fehler ❌:\nHier stimmt die Grammatik (Syntax) deines Codes nicht. Hast du irgendwo eine Klammer vergessen, Anführungszeichen nicht geschlossen oder falsch eingerückt? ✍️"
        
    elif "IndexError" in last_line:
        return "Fehler ❌:\nDu greifst auf ein Element in einer Liste zu, das gar nicht existiert (z. B. das 5. Element bei einer Liste mit nur 3 Einträgen). 📋"
        
    elif "AttributeError" in last_line:
        return "Fehler ❌:\nDu versuchst etwas zu benutzen, das dieses Objekt gar nicht kann oder besitzt. Hast du dich beim Namen vertippt? ⚙️"
    
    # Standard-Fehlermeldung, falls kein Filter greift
    return f"Fehler ❌:\n{last_line}"

# Diese Funktion läuft isoliert in einem eigenen Prozess (Schutz vor Endlosschleifen)
def execute_student_code(code, return_dict):
    redirected_output = io.StringIO()
    sys.stdout = redirected_output
    
    try:
        # Wir modifizieren die "builtins", um blockierende input() Befehle 
        # durch unsere sichere, simulierte "mock_input" Funktion zu ersetzen.
        builtins_dict = __import__('builtins').__dict__.copy()
        builtins_dict['input'] = mock_input
        builtins_dict['raw_input'] = mock_input
        
        local_scope = {}
        # Ausführung des generierten Codes mit modifizierten builtins
        exec(code, {"__builtins__": builtins_dict}, local_scope)
        
        return_dict['output'] = redirected_output.getvalue()
        return_dict['error'] = None
    except Exception as e:
        return_dict['error'] = traceback.format_exc()
    finally:
        sys.stdout = sys.__stdout__

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run_code', methods=['POST'])
def run_code():
    data = request.get_json()
    code = data.get('code', '')
    
    manager = multiprocessing.Manager()
    return_dict = manager.dict()
    
    # Schüler-Code in isoliertem Prozess starten
    p = multiprocessing.Process(target=execute_student_code, args=(code, return_dict))
    p.start()
    
    # Maximal 2 Sekunden warten (Timeout-Schutz)
    p.join(2.0)
    
    if p.is_alive():
        p.terminate()
        p.join()
        return jsonify({'output': 'Fehler ❌:\nZeitüberschreitung! Hast du eine Endlosschleife gebaut?'})
    
    if return_dict.get('error'):
        # Übersetze den abgefangenen Fehler
        friendly_error = translate_error(return_dict['error'])
        return jsonify({'output': friendly_error})
        
    output = return_dict.get('output', '')
    return jsonify({'output': output if output else "Programm erfolgreich ausgeführt (keine Textausgabe)."})

if __name__ == '__main__':
    app.run(debug=True)
