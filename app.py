import os
import sqlite3
import webbrowser
import io
import pandas as pd
from threading import Timer
from typing import Tuple
from flask import Flask, render_template, request, jsonify, Response, redirect, url_for, send_file
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Configuración
app = Flask(__name__)
app.secret_key = 'sweetcookies_secret_key_demo' # En producción esto va en variables de entorno
CORS(app)

# Configuración Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

DB_NAME = "cookies_pedidos.db"
SABORES_VALIDOS = [
    "Pistacho", "Rocher", "Sweet", "Velvet", "Kinder", "Rasta",
    "Cadbury", "Milka", "Blackblock", "Coco", "Doublechocolate",
]

# --- Modelos de Usuario ---
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user_data = cursor.fetchone()
    conn.close()
    
    if user_data:
        return User(id=user_data['id'], username=user_data['username'], password_hash=user_data['password_hash'])
    return None

# --- Base de Datos ---
def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db() -> None:
    conn = get_db()
    cursor = conn.cursor()
    
    # Tablas de negocio
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dia TEXT NOT NULL,
            nombre TEXT NOT NULL,
            precio_pedido REAL NOT NULL,
            precio_envio REAL DEFAULT 0.0,
            direccion TEXT,
            horario TEXT,
            pago INTEGER DEFAULT 0,
            fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedido_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            sabor TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos (id) ON DELETE CASCADE
        )
    ''')
    
    # Tabla de Usuarios (Auth)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_pedido_id ON pedido_items (pedido_id)')
    
    # Migraciones simples
    cursor.execute("PRAGMA table_info(pedidos)")
    columns = [info[1] for info in cursor.fetchall()]
    if 'pago' not in columns:
        cursor.execute('ALTER TABLE pedidos ADD COLUMN pago INTEGER DEFAULT 0')
    
    conn.commit()
    conn.close()

# --- Rutas de Autenticación ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user_data = cursor.fetchone()
        conn.close()
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(id=user_data['id'], username=user_data['username'], password_hash=user_data['password_hash'])
            login_user(user)
            return redirect(url_for('index'))
        
        return render_template('login.html', error="Credenciales inválidas")
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- Rutas Principales ---

@app.route('/')
@login_required
def index() -> str:
    return render_template('index.html', user=current_user)

@app.route('/api/exportar', methods=['GET'])
@login_required
def exportar_excel():
    """Genera y descarga un reporte Excel de los pedidos."""
    try:
        conn = get_db()
        
        # Query SQL uniendo tablas para el reporte
        query = """
            SELECT 
                p.id as 'Nro Pedido',
                p.fecha_registro as 'Fecha Registro',
                p.dia as 'Día Entrega',
                p.nombre as 'Cliente',
                p.direccion as 'Dirección',
                (p.precio_pedido + p.precio_envio) as 'Total ($)',
                CASE WHEN p.pago = 1 THEN 'Pagado' ELSE 'Pendiente' END as 'Estado Pago',
                GROUP_CONCAT(pi.cantidad || 'x ' || pi.sabor, ', ') as 'Detalle Items'
            FROM pedidos p
            LEFT JOIN pedido_items pi ON p.id = pi.pedido_id
            GROUP BY p.id
            ORDER BY p.fecha_registro DESC
        """
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        
        # Crear archivo en memoria
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Pedidos SweetCookies')
            
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'reporte_pedidos.xlsx'
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# --- API Endpoints (Protegidos) ---

@app.route('/api/pedidos', methods=['GET'])
@login_required
def get_pedidos() -> Tuple[Response, int]:
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pedidos ORDER BY dia, fecha_registro DESC")
        pedidos_db = cursor.fetchall()
        
        pedidos_completos = []
        for pedido_row in pedidos_db:
            pedido_dict = dict(pedido_row)
            cursor.execute("SELECT sabor, cantidad FROM pedido_items WHERE pedido_id = ?", (pedido_dict['id'],))
            items_db = cursor.fetchall()
            pedido_dict['items'] = [dict(item) for item in items_db]
            pedidos_completos.append(pedido_dict)
        
        conn.close()
        return jsonify({"success": True, "pedidos": pedidos_completos}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/pedidos', methods=['POST'])
@login_required
def crear_pedido() -> Tuple[Response, int]:
    conn = None
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        
        sql_pedido = """
            INSERT INTO pedidos (dia, nombre, precio_pedido, precio_envio, direccion, horario)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql_pedido, (
            data['dia'], data['nombre'], data['precio_pedido'],
            data.get('precio_envio', 0), data.get('direccion', ''), data.get('horario', '')
        ))
        pedido_id = cursor.lastrowid
        
        if data.get('items'):
            sql_item = "INSERT INTO pedido_items (pedido_id, sabor, cantidad) VALUES (?, ?, ?)"
            for item in data['items']:
                cursor.execute(sql_item, (pedido_id, item['sabor'], item['cantidad']))
        
        conn.commit()
        return jsonify({"success": True, "pedido_id": pedido_id}), 201
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/pedidos/<int:pedido_id>', methods=['GET'])
@login_required
def get_pedido(pedido_id: int) -> Tuple[Response, int]:
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pedidos WHERE id = ?", (pedido_id,))
        pedido_row = cursor.fetchone()
        if not pedido_row:
            conn.close()
            return jsonify({"success": False, "error": "Pedido no encontrado"}), 404
        
        pedido_dict = dict(pedido_row)
        cursor.execute("SELECT sabor, cantidad FROM pedido_items WHERE pedido_id = ?", (pedido_id,))
        pedido_dict['items'] = [dict(item) for item in cursor.fetchall()]
        conn.close()
        return jsonify({"success": True, "pedido": pedido_dict}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/pedidos/<int:pedido_id>', methods=['PUT'])
@login_required
def actualizar_pedido(pedido_id: int) -> Tuple[Response, int]:
    conn = None
    try:
        data = request.json
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("BEGIN TRANSACTION")
        
        sql_update = """
            UPDATE pedidos
            SET dia = ?, nombre = ?, precio_pedido = ?, precio_envio = ?,
                direccion = ?, horario = ?, pago = ?
            WHERE id = ?
        """
        cursor.execute(sql_update, (
            data['dia'], data['nombre'], data['precio_pedido'],
            data.get('precio_envio', 0), data.get('direccion', ''),
            data.get('horario', ''), data.get('pago', 0), pedido_id
        ))
        
        cursor.execute("DELETE FROM pedido_items WHERE pedido_id = ?", (pedido_id,))
        if data.get('items'):
            sql_item = "INSERT INTO pedido_items (pedido_id, sabor, cantidad) VALUES (?, ?, ?)"
            for item in data['items']:
                cursor.execute(sql_item, (pedido_id, item['sabor'], item['cantidad']))
        
        conn.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/pedidos/<int:pedido_id>', methods=['DELETE'])
@login_required
def eliminar_pedido(pedido_id: int) -> Tuple[Response, int]:
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM pedidos WHERE id = ?", (pedido_id,))
        conn.commit()
        eliminado = cursor.rowcount > 0
        conn.close()
        if eliminado: return jsonify({"success": True}), 200
        return jsonify({"success": False, "error": "Pedido no encontrado"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/pedidos/<int:pedido_id>/toggle-pago', methods=['POST'])
@login_required
def toggle_pago(pedido_id: int) -> Tuple[Response, int]:
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT pago FROM pedidos WHERE id = ?", (pedido_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return jsonify({"success": False, "error": "Pedido no encontrado"}), 404
        nuevo_estado = 1 if result['pago'] == 0 else 0
        cursor.execute("UPDATE pedidos SET pago = ? WHERE id = ?", (nuevo_estado, pedido_id))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "nuevo_estado": nuevo_estado}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/estadisticas', methods=['GET'])
@login_required
def get_estadisticas() -> Tuple[Response, int]:
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM pedidos")
        pedidos = cursor.fetchall()
        
        stats = {
            "produccion_total": {}, "produccion_por_dia": {},
            "total_recaudado": 0.0, "total_pedidos": len(pedidos),
            "pedidos_pagados": 0, "pedidos_pendientes": 0, "total_cookies": 0
        }
        
        for pedido_row in pedidos:
            pedido = dict(pedido_row)
            stats["total_recaudado"] += pedido['precio_pedido'] + pedido.get('precio_envio', 0)
            if pedido.get('pago', 0) == 1: stats["pedidos_pagados"] += 1
            else: stats["pedidos_pendientes"] += 1
            
            cursor.execute("SELECT sabor, cantidad FROM pedido_items WHERE pedido_id = ?", (pedido['id'],))
            items = cursor.fetchall()
            
            dia = pedido['dia']
            if dia not in stats["produccion_por_dia"]: stats["produccion_por_dia"][dia] = {}

            for item in items:
                sabor = item['sabor']
                cantidad = item['cantidad']
                stats["produccion_total"][sabor] = stats["produccion_total"].get(sabor, 0) + cantidad
                stats["produccion_por_dia"][dia][sabor] = stats["produccion_por_dia"][dia].get(sabor, 0) + cantidad
                stats["total_cookies"] += cantidad
        
        conn.close()
        return jsonify({"success": True, "estadisticas": stats}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/sabores', methods=['GET'])
@login_required
def get_sabores() -> Tuple[Response, int]:
    return jsonify({"success": True, "sabores": SABORES_VALIDOS}), 200

if __name__ == '__main__':
    init_db()
    def open_browser():
        webbrowser.open('http://127.0.0.1:5000/login')
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        Timer(1, open_browser).start()
    app.run(debug=False, port=5000)