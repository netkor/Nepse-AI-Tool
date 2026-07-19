#!/bin/bash
# Exit on error
#bash update_data.sh
set -e

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

echo "=================================================="
echo "1. Pulling latest stock CSVs from GitHub..."
echo "=================================================="
cd "$SCRIPT_DIR/nepse-data"
git pull

echo ""
echo "=================================================="
echo "2. Syncing new records to Django SQLite DB..."
echo "=================================================="
cd "$SCRIPT_DIR/nepse_backend"
../venv/bin/python manage.py import_nepse_data

echo ""
echo "=================================================="
echo "Update Complete! Your database is now up to date."
echo "=================================================="
