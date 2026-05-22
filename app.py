from flask import Flask, render_template, request, jsonify
import multiprocessing
import sys
import io
import traceback
import random

app = Flask(__name__)

# Simuliertes Antwort-System für Eingabe-Fragen der Schüler (z.B. input())
def mock_input(prompt=""):
    if prompt:
        print(prompt) # Zeigt die Frage in der Konsole an
    
    # Eine Liste lustiger/typischer Schülernamen
    names = ["Emma", "Nico", "Lukas", "Mia", "Maximilian", "Sofia", "David", "Laura"]
    chosen_name = random.choice(names)
    
    print(chosen_name) # Simuliert das Eintippen in der Konsole
    return chosen_name

# Diese Funktion läuft isoliert in einem eigenen Prozess (Schutz vor Endlosschleifen)
def execute_student_code(code, return_dict):
    redirected_output = io.StringIO()
    sys.stdout = redirected_output
    
    try:
        # Wir modifizieren die "builtins", um die blockierenden input() Befehle 
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
        error_lines = return_dict['error'].strip().split('\n')
        return jsonify({'output': f"Fehler ❌:\n{error_lines[-1]}"})
        
    output = return_dict.get('output', '')
    return jsonify({'output': output if output else "Programm erfolgreich ausgeführt (keine Textausgabe)."})

if __name__ == '__main__':
    app.run(debug=True)
