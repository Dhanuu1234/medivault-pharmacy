#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Populate the catalogue with sample data on first deploy (safe to re-run).
python manage.py seed_medicines
