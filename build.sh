#!/usr/bin/env bash
# Build script run by Render during deploy.
set -o errexit

pip install -r requirements.txt

# Collect static files for WhiteNoise to serve.
python manage.py collectstatic --no-input

# Apply database migrations (sessions, Support model, etc.).
python manage.py migrate
