#!/bin/bash

# Kill background processes on exit
trap "kill 0" EXIT

echo "🚀 Starting AI Visual Product Reviewer..."

# 1. Start FastAPI Backend
echo "📡 Starting Backend on http://localhost:8000..."
source venv/bin/activate
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &

# 2. Start React Frontend
echo "💻 Starting Frontend on http://localhost:5173..."
cd frontend
npm run dev &

# Wait for both
wait
