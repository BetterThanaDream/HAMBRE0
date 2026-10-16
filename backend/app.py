"""
HAMBRE CERO - ODS 2 (Hambre Cero)
Momento 2 - Desarrollo Sostenible

Backend Flask + SQLite
- Registro / login de usuarios (donantes y admin)
- Panel principal del donante
- Vista de gestion principal (admin): crear campanas y administrar donaciones
- Formulario de ingreso de datos (donacion)
- Vista de resultados / reportes

La base de datos se inicializa sola con el esquema y los datos de ejemplo
del dump si la base de datos esta vacia.
"""
import os
import sqlite3
from datetime import date
from functools import wraps
from flask import Flask, g, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import generate_password_hash, check_password_hash

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "frontend", "templates"), static_folder=os.path.join(BASE_DIR, "frontend", "static"))
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-cambiar-en-produccion")

SCHEMA_PATH = os.path.join(BASE_DIR, "database", "schema.sql")
DUMP_PATH = os.path.join(BASE_DIR, "database", "dump.sql")


def get_db_path():
    uri = os.environ.get("DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "database", "hambre_cero_db.sqlite"))
    if uri.startswith("sqlite:///"):
        return os.path.abspath(uri[len("sqlite:///"):])
    return uri


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(get_db_path())
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(exception):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    """Crea las tablas si no existen y si esta vacia carga los datos de ejemplo"""
    db = get_db()
    tablas = [r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    requeridas = ["usuarios", "organizaciones", "campanas", "donaciones"]
    if not all(t in tablas for t in requeridas):
        with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            db.executescript(f.read())
        db.commit()
    counts = {t: db.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in requeridas}
    if any(c == 0 for c in counts.values()):
        with open(DUMP_PATH, "r", encoding="utf-8") as f:
            sql = f.read()
        sql = "\n".join(
            line for line in sql.splitlines()
            if not line.strip().startswith("USE") and not line.strip().startswith("CREATE DATABASE")
        )
        db.executescript(sql)
        db.commit()


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            flash("Debes iniciar sesion para acceder a esa vista", "error")
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return wrapper


def admin_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session or session.get("rol") != "admin":
            abort(403)
        return f(*args, **kwargs)
    return wrapper


def current_user():
    db = get_db()
    return db.execute(
        "SELECT * FROM usuarios WHERE id_usuario = ?",
        (session.get("user_id"),)
    ).fetchone()


# ============================================================
# RUTAS - VISTAS PUBLICAS
# ============================================================

@app.route("/")
def index():
    db = get_db()
    campanas = db.execute(
        """SELECT c.*, o.nombre_org FROM campanas c
           JOIN organizaciones o ON c.id_org = o.id_org
           ORDER BY c.id_campana DESC"""
    ).fetchall()
    stats = {
        "total_donaciones": db.execute("SELECT COUNT(*) FROM donaciones WHERE estado_pago = 'aprobado'").fetchone()[0],
        "total_recaudado": db.execute("SELECT COALESCE(SUM(monto), 0) FROM donaciones WHERE estado_pago = 'aprobado'").fetchone()[0],
        "total_campanas": db.execute("SELECT COUNT(*) FROM campanas").fetchone()[0],
    }
    campanas_lista = []
    for c in campanas:
        pct = int((c["monto_recaudado"] / c["meta_financiera"] * 100)) if c["meta_financiera"] > 0 else 0
        campanas_lista.append({
            "id_campana": c["id_campana"],
            "titulo": c["titulo"],
            "descripcion": c["descripcion"],
            "monto_recaudado": c["monto_recaudado"],
            "meta_financiera": c["meta_financiera"],
            "pct": pct,
        })
    total_recaudado_str = "${:,.0f} COP".format(float(stats["total_recaudado"]))
    return render_template("index.html", campanas=campanas_lista, stats=stats, total_recaudado_str=total_recaudado_str)


# ============================================================
# RUTAS - AUTENTICACION
# ============================================================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        db = get_db()
        usuario = db.execute(
            "SELECT * FROM usuarios WHERE email = ?", (email,)
        ).fetchone()
        if usuario is None or not check_password_hash(usuario["password_hash"], password):
            flash("Email o contrasena incorrectos", "error")
            return render_template("login.html", error="Email o contrasena incorrectos")
        session.clear()
        session["user_id"] = usuario["id_usuario"]
        session["rol"] = usuario["rol"]
        flash("Bienvenido a HAMBRE Cero, " + usuario["nombre_completo"], "success")
        return redirect(url_for("panel"))
    return render_template("login.html")


@app.route("/registro", methods=["GET", "POST"])
def registro():
    if request.method == "POST":
        nombre = (request.form.get("nombre_completo") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        confirmar = request.form.get("confirmar_password") or ""
        error = None
        if len(nombre) < 3:
            error = "El nombre debe tener al menos 3 caracteres"
        elif "@" not in email or "." not in email:
            error = "El email no tiene un formato valido"
        elif len(password) < 6:
            error = "La contrasena debe tener al menos 6 caracteres"
        elif password != confirmar:
            error = "Las contrasenas no coinciden"
        if error is None:
            db = get_db()
            existe = db.execute("SELECT id_usuario FROM usuarios WHERE email = ?", (email,)).fetchone()
            if existe is not None:
                error = "El email ya esta registrado"
        if error is not None:
            flash(error, "error")
            return render_template("register.html", error=error, nombre=nombre, email=email)
        db = get_db()
        db.execute(
            "INSERT INTO usuarios (nombre_completo, email, password_hash, rol) VALUES (?, ?, ?, 'donante')",
            (nombre, email, generate_password_hash(password))
        )
        db.commit()
        flash("Cuenta creada exitosamente. Ahora inicia sesion para continuar", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/salir")
def salir():
    session.clear()
    flash("Sesion cerrada correctamente", "success")
    return redirect(url_for("index"))


# ============================================================
# RUTAS - VISTAS DE AUTENTICACION (PANEL Y REPORTES)
# ============================================================

@app.route("/panel")
@login_required
def panel():
    db = get_db()
    usuario = current_user()
    if usuario["rol"] == "admin":
        total_usuarios = db.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0]
        total_donaciones = db.execute("SELECT COUNT(*) FROM donaciones WHERE estado_pago = 'aprobado'").fetchone()[0]
        total_recaudado = db.execute("SELECT COALESCE(SUM(monto), 0) FROM donaciones WHERE estado_pago = 'aprobado'").fetchone()[0]
        ultimas = db.execute(
            """SELECT d.*, c.titulo AS campania FROM donaciones d
               JOIN campanas c ON d.id_campana = c.id_campana
               ORDER BY d.id_donacion DESC LIMIT 5"""
        ).fetchall()
        return render_template("panel_admin.html", usuario=usuario, total_usuarios=total_usuarios, total_donaciones=total_donaciones, total_recaudado=total_recaudado, ultimas=ultimas)
    mis_donaciones = db.execute(
        """SELECT d.*, c.titulo AS campania FROM donaciones d
           JOIN campanas c ON d.id_campana = c.id_campana
           WHERE d.id_usuario = ? ORDER BY d.id_donacion DESC""",
        (usuario["id_usuario"],)
    ).fetchall()
    campanas_activas = db.execute(
        """SELECT * FROM campanas ORDER BY id_campana DESC LIMIT 3"""
    ).fetchall()
    return render_template("panel.html", usuario=usuario, mis_donaciones=mis_donaciones, campanas_activas=campanas_activas)


@app.route("/reportes")
@login_required
def reportes():
    db = get_db()
    total_recaudado = db.execute("SELECT COALESCE(SUM(monto), 0) FROM donaciones WHERE estado_pago = 'aprobado'").fetchone()[0]
    total_donaciones = db.execute("SELECT COUNT(*) FROM donaciones WHERE estado_pago = 'aprobado'").fetchone()[0]
    total_campanas = db.execute("SELECT COUNT(*) FROM campanas").fetchone()[0]
    campanas = db.execute(
        """SELECT c.*, o.nombre_org FROM campanas c
           JOIN organizaciones o ON c.id_org = o.id_org
           ORDER BY c.id_campana DESC"""
    ).fetchall()
    filas = []
    for c in campanas:
        recaudado = c["monto_recaudado"]
        meta = c["meta_financiera"]
        pct = int((recaudado / meta * 100) / 10 * 10) if meta > 0 else 0
        filas.append({
            "id_campana": c["id_campana"],
            "titulo": c["titulo"],
            "org": c["nombre_org"],
            "meta": meta,
            "recaudado": recaudado,
            "pct": pct,
            "fecha_limite": c["fecha_limite"],
            "activa": c["fecha_limite"] > date.today().isoformat(),
        })
    ultimas = db.execute(
        """SELECT d.*, u.nombre_completo AS donante, c.titulo AS campania FROM donaciones d
           JOIN usuarios u ON d.id_usuario = u.id_usuario
           JOIN campanas c ON d.id_campana = c.id_campana
           ORDER BY d.id_donacion DESC LIMIT 8"""
    ).fetchall()
    return render_template("reportes.html", total_recaudado=total_recaudado, total_donaciones=total_donaciones, total_campanas=total_campanas, filas=filas, ultimas=ultimas)


# ============================================================
# RUTAS - DONACION (FORMULARIO DE INGRESO DE DATOS)
# ============================================================

@app.route("/donaciones/nueva", methods=["GET", "POST"])
@login_required
def donacion():
    db = get_db()
    usuario = current_user()
    campanas = db.execute(
        """SELECT * FROM campanas WHERE fecha_limite > ? ORDER BY id_campana DESC""",
        (date.today().isoformat(),)
    ).fetchall()
    if request.method == "POST":
        id_campana = request.form.get("id_campana")
        monto = request.form.get("monto")
        error = None
        monto_float = None
        if id_campana is None:
            error = "Debe seleccionar una campana"
        else:
            try:
                monto_float = float(monto)
            except (ValueError, TypeError):
                error = "El monto debe ser un numero valido"
            if error is None and (monto_float <= 0 or monto_float > 1000000000):
                error = "El monto debe estar entre 0 y 1000000000"
        if error is not None:
            flash(error, "error")
            return redirect(url_for("donacion"))
        db.execute(
            "INSERT INTO donaciones (id_usuario, id_campana, monto, estado_pago) VALUES (?, ?, ?, 'aprobado')",
            (usuario["id_usuario"], int(id_campana), monto_float)
        )
        db.execute(
            "UPDATE campanas SET monto_recaudado = monto_recaudado + ? WHERE id_campana = ?",
            (monto_float, int(id_campana))
        )
        db.commit()
        flash("Donacion registrada exitosamente. Gracias por apoyar el ODS 2", "success")
        return redirect(url_for("panel"))
    return render_template("donacion.html", campanas=campanas)


# ============================================================
# RUTAS - GESTION ADMINISTRADOR
# ============================================================

@app.route("/admin/gestion", methods=["GET", "POST"])
@admin_required
def gestion():
    db = get_db()
    if request.method == "POST":
        if "crear_campania" in request.form:
            titulo = (request.form.get("titulo") or "").strip()
            descripcion = (request.form.get("descripcion") or "").strip()
            meta = request.form.get("meta_financiera")
            fecha_limite = request.form.get("fecha_limite")
            id_org = request.form.get("id_org")
            error = None
            if len(titulo) < 5:
                error = "El titulo de la campania debe tener al menos 5 caracteres"
            try:
                meta_float = float(meta)
            except (ValueError, TypeError):
                error = "La meta financiera debe ser un numero valido"
            if error is None and meta_float <= 0:
                error = "La meta financiera debe ser mayor a cero"
            if error is None and not fecha_limite:
                error = "Debe definir una fecha limite"
            if error is None and not id_org:
                error = "Debe seleccionar una organizacion"
            if error is not None:
                flash(error, "error")
                return redirect(url_for("gestion"))
            db.execute(
                "INSERT INTO campanas (id_org, titulo, descripcion, meta_financiera, monto_recaudado, fecha_limite) VALUES (?, ?, ?, ?, 0.00, ?)",
                (int(id_org), titulo, descripcion, meta_float, fecha_limite)
            )
            db.commit()
            flash("Campania creada exitosamente", "success")
            return redirect(url_for("gestion"))
        if "estado_donacion" in request.form:
            id_donacion = request.form.get("id_donacion")
            nuevo_estado = request.form.get("estado")
            if nuevo_estado in ("aprobado", "rechazado", "pendiente"):
                donacion = db.execute("SELECT * FROM donaciones WHERE id_donacion = ?", (id_donacion,)).fetchone()
                if donacion is not None and donacion["estado_pago"] != nuevo_estado:
                    db.execute("UPDATE donaciones SET estado_pago = ? WHERE id_donacion = ?", (nuevo_estado, id_donacion))
                    if nuevo_estado == "rechazado" and donacion["estado_pago"] == "aprobado":
                        db.execute("UPDATE campanas SET monto_recaudado = monto_recaudado - ? WHERE id_campana = ?", (donacion["monto"], donacion["id_campana"]))
            db.commit()
            flash("Estado de la donacion actualizado", "success")
            return redirect(url_for("gestion"))
    organizaciones = db.execute("SELECT * FROM organizaciones ORDER BY id_org").fetchall()
    campanas = db.execute(
        """SELECT c.*, o.nombre_org FROM campanas c
           JOIN organizaciones o ON c.id_org = o.id_org
           ORDER BY c.id_campana DESC"""
    ).fetchall()
    donaciones = db.execute(
        """SELECT d.*, u.nombre_completo AS donante, c.titulo AS campania FROM donaciones d
           JOIN usuarios u ON d.id_usuario = u.id_usuario
           JOIN campanas c ON d.id_campana = c.id_campana
           ORDER BY d.id_donacion DESC"""
    ).fetchall()
    return render_template("gestion.html", organizaciones=organizaciones, campanas=campanas, donaciones=donaciones)


if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
