FROM python:3.9-slim

WORKDIR /app

# Installer les dépendances système requises
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    tesseract-ocr \
    libopencv-dev \
    libopenblas-dev \
    libomp-dev \
    python3-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le script d'entrée
COPY docker-entrypoint.sh .
RUN chmod +x docker-entrypoint.sh

# Copier le reste du code
COPY . .

# Exposer le port
EXPOSE 8000

# Définir le point d'entrée
ENTRYPOINT ["./docker-entrypoint.sh"]
