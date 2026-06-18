#!/bin/bash

echo "Starting PostgreSQL installation and setup..."

# 1. Install PostgreSQL server and client
sudo apt update
sudo apt install -y postgresql postgresql-client

# 2. Start PostgreSQL service
sudo service postgresql start

# 3. Set the password for the 'postgres' user to 'postgres'
sudo -u postgres psql -c "ALTER USER postgres PASSWORD 'postgres';"

# 4. Create the 'margsathi' database
sudo -u postgres createdb -O postgres margsathi || echo "Database might already exist, skipping."

# 5. Install Python dependencies
pip install -r requirements.txt

echo "Setup complete! You can now run:"
echo "streamlit run main.py"
