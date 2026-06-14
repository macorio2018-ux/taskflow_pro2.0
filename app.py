from flask import Flask, render_template, request, redirect, session, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
import json
import os
import uuid
from datetime import datetime
app = Flask(__name__)
app.secret_key = "taskflow_secreto_unifranz_2026" # Clave para sesiones seguras

USUARIOS_FILE = "data/usuarios.json"
TAREAS_FILE = "data/tareas.json"

# --- FUNCIONES DE MANEJO DE ARCHIVOS (JSON) ---
def cargar_json(ruta, valor_defecto):
    if not os.path.exists(ruta):
        return valor_defecto
    with open(ruta, "r", encoding="utf-8") as archivo:
        try:
            return json.load(archivo)
        except json.JSONDecodeError:
            return valor_defecto

def guardar_json(ruta, datos):
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    with open(ruta, "w", encoding="utf-8") as archivo:
        json.dump(datos, archivo, indent=4, ensure_ascii=False)

# --- RUTAS DE LA APLICACIÓN ---
@app.route("/")
def inicio():
    if "usuario_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))

@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "").strip()
        facultad = request.form.get("facultad", "").strip()
        carrera = request.form.get("carrera", "").strip()

        usuarios = cargar_json(USUARIOS_FILE, [])

        if not usuario or not password or not facultad or not carrera:
            flash("Todos los campos son obligatorios", "error")
            return redirect(url_for("registro"))

        for u in usuarios:
            if u["usuario"] == usuario:
                flash("El usuario ya existe", "error")
                return redirect(url_for("registro"))

        nuevo_usuario = {
            "id": str(uuid.uuid4()),
            "usuario": usuario,
            "password_hash": generate_password_hash(password),
            "facultad": facultad,
            "carrera": carrera,
            "auth_provider": "local"
        }

        usuarios.append(nuevo_usuario)
        guardar_json(USUARIOS_FILE, usuarios)
        return redirect(url_for("login"))

    return render_template("registro.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario", "").strip()
        password = request.form.get("password", "").strip()

        usuarios = cargar_json(USUARIOS_FILE, [])

        for u in usuarios:
            if u["usuario"] == usuario and check_password_hash(u["password_hash"], password):
                session["usuario_id"] = u["id"]
                session["usuario"] = u["usuario"]
                session["facultad"] = u["facultad"]
                session["carrera"] = u["carrera"]
                return redirect(url_for("dashboard"))

        flash("Usuario o contraseña incorrectos", "error")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
def dashboard():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    tareas_data = cargar_json(TAREAS_FILE, {})
    usuario_id = session["usuario_id"]
    tareas = tareas_data.get(usuario_id, [])

    total = len(tareas)
    pendientes = len([t for t in tareas if t["estado"] == "pendiente"])
    completadas = len([t for t in tareas if t["estado"] == "completada"])

    productividad = 0
    if total > 0:
        productividad = round((completadas / total) * 100)

    user_info = {
        "usuario": session["usuario"],
        "carrera": session["carrera"]
    }

    stats_info = {
        "total": total,
        "pendientes": pendientes,
        "completadas": completadas,
        "productividad": productividad
    }

    # Transformar fecha_limite a datetime objects para que strftime funcione
    for t in tareas:
        if isinstance(t["fecha_limite"], str):
            try:
                t["fecha_limite"] = datetime.strptime(t["fecha_limite"], "%Y-%m-%dT%H:%M")
            except ValueError:
                try:
                    t["fecha_limite"] = datetime.strptime(t["fecha_limite"], "%Y-%m-%d")
                except ValueError:
                    pass

    return render_template(
        "dashboard.html",
        user=user_info,
        stats=stats_info,
        tareas=tareas
    )

@app.route("/crear-tarea", methods=["GET", "POST"])
def crear_tarea():
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        titulo = request.form.get("titulo", "").strip()
        descripcion = request.form.get("descripcion", "").strip()
        materia = request.form.get("materia", "").strip()
        prioridad = request.form.get("prioridad", "").strip()
        fecha_limite = request.form.get("fecha_limite", "").strip()

        if not titulo or not descripcion or not materia or not prioridad or not fecha_limite:
            flash("Todos los campos de la tarea son obligatorios", "error")
            return redirect(url_for("crear_tarea"))

        tareas_data = cargar_json(TAREAS_FILE, {})
        usuario_id = session["usuario_id"]

        if usuario_id not in tareas_data:
            tareas_data[usuario_id] = []

        nueva = {
            "id": str(uuid.uuid4()),
            "titulo": titulo,
            "descripcion": descripcion,
            "materia": materia,
            "prioridad": prioridad,
            "fecha_limite": fecha_limite,
            "estado": "pendiente"
        }

        tareas_data[usuario_id].append(nueva)
        guardar_json(TAREAS_FILE, tareas_data)
        flash("Tarea creada exitosamente", "success")
        return redirect(url_for("dashboard"))

    user_info = {
        "usuario": session["usuario"],
        "carrera": session["carrera"]
    }
    return render_template("nueva_tarea.html", user=user_info)

@app.route("/completar-tarea/<tarea_id>")
def completar_tarea(tarea_id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    tareas_data = cargar_json(TAREAS_FILE, {})
    usuario_id = session["usuario_id"]

    for tarea in tareas_data.get(usuario_id, []):
        if tarea["id"] == tarea_id:
            tarea["estado"] = "completada"

    guardar_json(TAREAS_FILE, tareas_data)
    flash("Tarea completada", "success")
    return redirect(url_for("dashboard"))

@app.route("/eliminar-tarea/<tarea_id>")
def eliminar_tarea(tarea_id):
    if "usuario_id" not in session:
        return redirect(url_for("login"))

    tareas_data = cargar_json(TAREAS_FILE, {})
    usuario_id = session["usuario_id"]

    tareas_data[usuario_id] = [
        tarea for tarea in tareas_data.get(usuario_id, [])
        if tarea["id"] != tarea_id
    ]

    guardar_json(TAREAS_FILE, tareas_data)
    flash("Tarea eliminada", "success")
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    app.run(debug=True, port=5050)