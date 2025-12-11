LLM Backend – Setup & Run Guide

A lightweight backend for running an LLM server with FastAPI and Uvicorn.

Prerequisites

Python 3.10 or higher

pip

(macOS/Linux recommended; Windows instructions included)

Installation
1. Clone the repository
git clone <repository-url>
cd Python_Final_Project

2. Navigate into the backend directory
cd llm_backend

3. Create a virtual environment
python3 -m venv venv

4. Activate the virtual environment
macOS / Linux:
source venv/bin/activate

Windows PowerShell:
.\venv\Scripts\Activate.ps1
Note: Only do this if the venv files show up correctly

5. Install dependencies
pip install -r requirements.txt

Running the Server
Start FastAPI with Uvicorn

Run this inside the activated virtual environment:

uvicorn main:app --reload


This will start the backend on:

http://127.0.0.1:8000


The --reload flag automatically restarts the server when files change (good for development).

Project Structure (Simplified)
llm_backend/
│
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
├── venv/                # Virtual environment (auto-created)
└── ... other backend files ...

Troubleshooting
Virtual environment not activating

macOS/Linux users may need:

chmod +x venv/bin/activate


Windows users must run PowerShell as Administrator and may need:

Set-ExecutionPolicy RemoteSigned

Dependencies not installing

Make sure the venv is active:

which python3
which pip


Should point inside llm_backend/venv/.

Server won't start

Verify main.py has:

app = FastAPI()


and that uvicorn is installed.