#!/bin/bash

# Get the directory of the script
script_dir=$(dirname "$(readlink -f "$0")")
project_root=$(dirname "$(dirname "$(dirname "$(dirname "$script_dir")")")")

echo "Project root detected as: $project_root"

# Set PYTHONPATH to include the project root
export PYTHONPATH="$project_root:$PYTHONPATH"

# Run the initialization script
echo "Running database initialization..."
python "$script_dir/init_db.py"

if [ $? -eq 0 ]; then
    echo "✅ Database initialized successfully."
else
    echo "❌ Database initialization failed. Please check the logs."
    exit 1
fi
