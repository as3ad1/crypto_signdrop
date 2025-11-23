@echo off
echo Setting up Signdrop backend...
cd backend
python -m venv venv
call venv\Scripts\activate.bat
pip install -r requirements.txt
echo.
echo Backend setup complete! Run: python app.py

cd ..\frontend
echo.
echo Setting up frontend...
call npm install
echo.
echo Frontend setup complete! Run: npm start
