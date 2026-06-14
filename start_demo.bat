@echo off
echo Starting Onto_Wiz System...

echo 1. Starting Backend (Port 8000)...
start "OntoWiz Backend" cmd /k "python src/api/server.py"

echo 2. Starting Frontend (Port 3000)...
cd frontend
start "OntoWiz Frontend" cmd /k "npm run dev"

echo System Started. Go to http://localhost:3000
pause
