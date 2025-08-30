#!/data/data/com.termux/files/usr/bin/bash
set -e  # exit on any error

# Handle Ctrl+C / termination
trap 'echo "⏹ Shutting down…"; jobs -p | xargs -r kill; exit' SIGINT SIGTERM

# Activate virtualenv (ensure you created it with python3 -m venv venv)
source venv/bin/activate

cd movies
# Start Python app
python app.py &

# Start Node app (in nodejs folder)
( cd nodejs && node server.js ) &

# Wait for all background jobs
wait
