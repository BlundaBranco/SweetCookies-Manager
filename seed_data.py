import sqlite3
import random
import os
from werkzeug.security import generate_password_hash

DB_NAME = "cookies_pedidos.db"

# Datos de prueba
NOMBRES = ["María González", "Juan Pérez", "Lucía Fernández", "Carlos Rodríguez", "Ana López", "Sofía Martínez"]
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
SABORES = ["Pistacho", "Rocher", "Sweet", "Velvet", "Kinder", "Cadbury", "Milka", "Coco", "Doublechocolate"]
DIRECCIONES = ["Av. Siempre Viva 123", "Centro", "Retiro por local", "Belgrano 1200"]

def inicializar_schema(cursor):
    """Crea las tablas necesarias si no existen (para evitar errores de 'no such table')."""
    # Tabla de Usuarios
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
    ''')
    
    # Tabla de Pedidos
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
    
    # Tabla de Items
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pedido_items (
            item_id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            sabor TEXT NOT NULL,
            cantidad INTEGER NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos (id) ON DELETE CASCADE
        )
    ''')

def generar_datos():
    # Si existe el archivo db, nos conectamos. Si no, se crea.
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        print("1. Verificando estructura de base de datos...")
        inicializar_schema(cursor)

        print("2. Limpiando datos antiguos...")
        cursor.execute("DELETE FROM pedido_items")
        cursor.execute("DELETE FROM pedidos")
        cursor.execute("DELETE FROM users")
        # Reiniciar contadores de IDs
        cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('pedidos', 'pedido_items', 'users')")

        print("3. Creando usuario Administrador...")
        # Usuario: admin / Pass: admin123
        hashed_pw = generate_password_hash("admin123")
        cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", ("admin", hashed_pw))

        print("4. Generando pedidos de prueba...")
        for _ in range(15): # Creamos 15 pedidos
            nombre = random.choice(NOMBRES)
            dia = f"{random.choice(DIAS)} {random.randint(1, 30)}"
            direccion = random.choice(DIRECCIONES)
            total = 0
            items = []
            
            # Generar items aleatorios para este pedido
            for _ in range(random.randint(1, 4)):
                sabor = random.choice(SABORES)
                cant = random.randint(1, 6)
                total += cant * 1200 # Precio ficticio
                items.append((sabor, cant))

            # Insertar pedido
            cursor.execute('''
                INSERT INTO pedidos (dia, nombre, precio_pedido, precio_envio, direccion, horario, pago)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (dia, nombre, total, random.choice([0, 500, 1000]), direccion, "14:00-18:00", random.choice([0, 1])))
            
            pid = cursor.lastrowid
            
            # Insertar items
            for s, c in items:
                cursor.execute("INSERT INTO pedido_items (pedido_id, sabor, cantidad) VALUES (?, ?, ?)", (pid, s, c))

        conn.commit()
        print("\n¡ÉXITO! Base de datos poblada correctamente.")
        print("-------------------------------------------")
        print("Usuario Admin creado:")
        print("User: admin")
        print("Pass: admin123")
        print("-------------------------------------------")

    except Exception as e:
        print(f"\nERROR CRÍTICO: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    generar_datos()