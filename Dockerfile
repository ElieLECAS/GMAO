FROM python:3.11-slim

WORKDIR /app

# Installation des dépendances système nécessaires
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers de dépendances
COPY requirements.txt .

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Copie du reste des fichiers de l'application
COPY . .

# Exposition du port Streamlit
EXPOSE 8501

# Commande pour lancer l'application
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0"] 