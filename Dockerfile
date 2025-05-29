FROM python:3.9-slim

WORKDIR /app

# Copia i file del progetto
COPY bot_barzellette.py .
COPY barzellette.json .
COPY requirements.txt .

# Installa le dipendenze
RUN pip install --no-cache-dir -r requirements.txt

# Avvia il bot
CMD ["python", "bot_barzellette.py"]