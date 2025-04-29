#!/bin/bash

# Start the Flask server
echo "Starting Flask server (backend) on port 5000..."
python3 server.py &

# Wait a second to make sure Flask server is ready
sleep 2

# Start the Static HTTP Server
echo "Starting Static File Server (frontend) on port 8000..."
python3 -m http.server 8000

# When you Ctrl+C to stop the HTTP server, also kill the Flask server
echo "Stopping Flask server..."
kill $(jobs -p)
