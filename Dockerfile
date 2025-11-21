# Usar imagen oficial ligera de Python
FROM python:3.10-slim

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de dependencias e instalar
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Exponer el puerto
EXPOSE 5000

# Comando para ejecutar la app (usando gunicorn para producción sería mejor, pero python app.py sirve para demo)
CMD ["python", "app.py"]