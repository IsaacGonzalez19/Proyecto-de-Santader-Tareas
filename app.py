import json
from pathlib import Path

from flask import Flask, request, render_template, redirect, url_for

app = Flask(__name__)

TAREAS_JSON = Path(__file__).resolve().parent / 'tareas.json'

tareas = []
siguiente_id = 1


def _max_id():
    return max((t['id'] for t in tareas), default=0)


def cargar_tareas():
    global tareas, siguiente_id
    if not TAREAS_JSON.is_file():
        tareas = []
        siguiente_id = 1
        return
    try:
        data = json.loads(TAREAS_JSON.read_text(encoding='utf-8'))
        tareas = data.get('tareas', [])
        if not isinstance(tareas, list):
            tareas = []
        max_id = _max_id()
        raw = data.get('siguiente_id', max_id + 1)
        siguiente_id = max(int(raw), max_id + 1) if tareas else max(int(raw), 1)
    except (OSError, json.JSONDecodeError, TypeError, ValueError, KeyError):
        tareas = []
        siguiente_id = 1


def guardar_tareas():
    payload = {'tareas': tareas, 'siguiente_id': siguiente_id}
    TAREAS_JSON.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )


cargar_tareas()


@app.route('/')
def index():
    tareas_ordenadas = sorted(tareas, key=lambda t: t['completada'])
    return render_template('index.html', tareas=tareas_ordenadas)


def agregar_tarea(texto):
    global siguiente_id
    tareas.append({'id': siguiente_id, 'texto': texto, 'completada': False})
    siguiente_id += 1
    guardar_tareas()


def completar_tarea(id):
    for tarea in tareas:
        if tarea['id'] == id:
            tarea['completada'] = True
            guardar_tareas()
            break


def obtener_tarea(id):
    for tarea in tareas:
        if tarea['id'] == id:
            return tarea
    return None


def borrar_tarea(id):
    global tareas
    antes = len(tareas)
    tareas = [t for t in tareas if t['id'] != id]
    if len(tareas) != antes:
        guardar_tareas()


def actualizar_tarea(id, texto):
    tarea = obtener_tarea(id)
    if tarea is None:
        return False
    tarea['texto'] = texto
    guardar_tareas()
    return True


@app.route('/agregar', methods=['POST'])
def agregar():
    texto_tarea = request.form.get('texto_tarea')
    if texto_tarea:
        agregar_tarea(texto_tarea)
    return redirect(url_for('index'))


@app.route('/completar/<int:id>')
def completar(id):
    completar_tarea(id)
    return redirect(url_for('index'))


@app.route('/borrar/<int:id>', methods=['POST'])
def borrar(id):
    borrar_tarea(id)
    return redirect(url_for('index'))


@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    tarea = obtener_tarea(id)
    if tarea is None:
        return redirect(url_for('index'))
    if request.method == 'POST':
        texto = (request.form.get('texto_tarea') or '').strip()
        if texto:
            actualizar_tarea(id, texto)
        return redirect(url_for('index'))
    return render_template('editar.html', tarea=tarea)


if __name__ == '__main__':
    app.run(debug=True)