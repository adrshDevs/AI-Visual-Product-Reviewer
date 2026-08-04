#!/bin/bash

# Kill background processes on exit
trap "kill 0" EXIT

echo "🚀 Building React Frontend..."
npm run build

echo "📡 Starting Unified Server on http://localhost:8000..."
source venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &

echo "💻 Also starting Frontend Dev Server on http://localhost:5173..."
npm run dev &

wait
