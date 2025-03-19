#!/bin/bash
set -e

# Attendre que la base de données soit prête (si nécessaire)
echo "Attente de la base de données..."
sleep 5

# Appliquer les migrations
echo "Application des migrations..."
python manage.py migrate

# Créer les migrations si nécessaire
echo "Création des migrations..."
python manage.py makemigrations

# Démarrer le serveur
echo "Démarrage du serveur Django..."
python manage.py runserver 0.0.0.0:8000 