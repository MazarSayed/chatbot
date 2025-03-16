#!/bin/bash
set -e

# Update and install required packages
apt-get update
apt-get install -y sqlite3 libsqlite3-dev 

# Print SQLite version for debugging
sqlite3 --version

# Upgrade pip and install requirements
pip install --upgrade pip
pip install -r requirements.txt

# Print information about the installed versions
echo "Python version:"
python --version
echo "SQLite version in Python:"
python -c "import sqlite3; print(sqlite3.sqlite_version)"
echo "ChromaDB requirements satisfied? Let's check:"
python -c "import chromadb; print(f'ChromaDB version: {chromadb.__version__}')"

echo "Environment setup complete!" 