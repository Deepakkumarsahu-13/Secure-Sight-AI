@echo off
title Secure Sight AI - Backend Server
echo Starting Python Flask Backend...
cd backend
call venv\Scripts\activate
python app.py
pause
