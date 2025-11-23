@echo off
echo Starting Signdrop...
echo.
start cmd /k "cd backend && venv\Scripts\activate && python app.py"
timeout /t 2
start cmd /k "cd frontend && npm start"
echo.
echo Servers starting...
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
pause
