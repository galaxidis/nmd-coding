from flask import Flask, render_template, request, jsonify
import multiprocessing
import sys
import io
import traceback

app = Flask(__name__)

# Diese Funktion läuft isoliert in einem eigenen Prozess (Schutz vor Endlosschleifen)
def execute_student_code(code, return_dict):
    redirected_output = io.StringIO()
    sys.stdout = redirected_output
    
    try:
        local_scope = {}
        # Ausführung des generierten Codes
        exec(code, {"__builtins__": __import__('builtins')}, local_scope)
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