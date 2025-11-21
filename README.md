# SweetCookies Management System

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.10+-3776AB.svg)
![Flask](https://img.shields.io/badge/flask-3.0-000000.svg)
![Docker](https://img.shields.io/badge/docker-ready-2496ED.svg)

Sistema integral de gestión de pedidos y producción diseñado para optimizar el flujo de trabajo de emprendimientos gastronómicos. Esta solución centraliza la administración de clientes, pedidos y métricas financieras en una interfaz moderna y reactiva.

![Dashboard Preview](screenshots/dashboard.png)

## 🚀 Características Principales

### 🔐 Seguridad y Control de Acceso
*   **Autenticación Robusta**: Sistema de Login protegido implementando `Flask-Login` con hasheo de contraseñas (Bcrypt) para garantizar la seguridad de los datos.
*   **Gestión de Sesiones**: Protección de rutas y persistencia de autenticación.

### 📊 Inteligencia de Negocio (BI)
*   **Dashboard en Tiempo Real**: Visualización instantánea de KPIs críticos (Ingresos totales, producción diaria, pedidos pendientes).
*   **Reportes Exportables**: Generación automática de hojas de cálculo (`.xlsx`) mediante **Pandas** para contabilidad y auditoría externa.
*   **Análisis de Demanda**: Gráficos interactivos (`Chart.js`) para visualizar la distribución de ventas por sabor/producto.

### 🛠 Gestión Operativa
*   **CRUD Completo**: Ciclo de vida total de pedidos (Crear, Leer, Actualizar, Eliminar) con soporte para ítems anidados.
*   **Control de Estados**: Seguimiento visual del flujo de caja (Pendiente vs Pagado).
*   **UX/UI Moderna**: Interfaz responsiva construida con **TailwindCSS**, incluyendo soporte nativo para **Modo Oscuro**.

## 💻 Stack Tecnológico

El proyecto sigue una arquitectura MVC (Modelo-Vista-Controlador) adaptada.

*   **Backend**: Python 3.10, Flask, Pandas, SQLite (Transaccional).
*   **Frontend**: HTML5, TailwindCSS, Alpine.js (Reactividad ligera), Chart.js.
*   **Infraestructura**: Docker, Gunicorn (ready).

## ⚙️ Instalación y Despliegue

### Pre-requisitos
*   Python 3.8+ o Docker Desktop.

### Opción A: Despliegue Local (Tradicional)

1.  **Clonar el repositorio**
    ```bash
    git clone https://github.com/BlundaBranco/sweetcookies-manager.git
    cd sweetcookies-manager
    ```

2.  **Configurar entorno virtual**
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Linux/Mac:
    source venv/bin/activate
    ```

3.  **Instalar dependencias**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Inicializar base de datos y usuario admin**
    Este script crea la estructura DB y genera datos de prueba.
    ```bash
    python seed_data.py
    ```

5.  **Ejecutar la aplicación**
    ```bash
    python app.py
    ```
    El sistema estará disponible en `http://127.0.0.1:5000`.

### Opción B: Despliegue con Docker

1.  **Construir la imagen**
    ```bash
    docker build -t sweetcookies-app .
    ```

2.  **Ejecutar el contenedor**
    ```bash
    docker run -d -p 5000:5000 --name sweetcookies_instance sweetcookies-app
    ```

## 🔑 Credenciales de Acceso (Demo)

Para facilitar la revisión del proyecto, el script de inicialización genera un usuario administrador por defecto:

*   **Usuario:** `admin`
*   **Contraseña:** `admin123`

## 📂 Estructura del Proyecto

```
sweetcookies-manager/
├── database/          # Lógica de persistencia (SQLite)
├── static/            # Assets estáticos
│   ├── css/           # Estilos personalizados
│   ├── js/            # Lógica cliente (Alpine.js)
│   └── favicon.ico
├── templates/         # Plantillas Jinja2 (HTML)
│   ├── index.html     # Dashboard SPA
│   └── login.html     # Vista de autenticación
├── app.py             # Controlador principal API & Rutas
├── seed_data.py       # Script de población de datos y Admin
├── Dockerfile         # Configuración de contenedor
├── requirements.txt   # Dependencias del proyecto
└── README.md          # Documentación

## 📸 Galería de Capturas

| Login Seguro | Gestión de Pedidos |
|:---:|:---:|
| ![Login Screen](screenshots/login.png) | ![Formulario Pedido](screenshots/modal.png) |
| *Acceso protegido con modo oscuro* | *Formulario reactivo y validaciones* |

> **Nota:** El diseño es completamente responsivo y se adapta a dispositivos móviles.