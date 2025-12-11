# Python Final Project — MCP File Search + LLM Backend

This repository contains our Python_Final_Project, integrating an MCP (Model Context Protocol) server for multi-backend file storage (Google Drive + Dropbox) and an LLM backend for intelligent natural-language query handling.

## Overview

This project enables seamless interaction between:

- A custom MCP server that connects to Google Drive and Dropbox
- An LLM backend that interprets natural-language requests and converts them into MCP actions
- A simple web interface for querying, storing, and retrieving files

Users can search, upload, and retrieve files using natural language, while the LLM translates intent into structured operations executed by the MCP server.

## Key Features

### MCP Server (Google Drive + Dropbox)

- Unified API for listing, searching, uploading, and retrieving files
- Supports both Google Drive and Dropbox as primary storage backends
- Modular structure allowing more providers in the future

### LLM Backend

- Converts natural-language prompts into MCP actions
- Uses a configurable XML-based system prompt
- Maintains conversation history in PostgreSQL

### Web Interface

- Lightweight HTML + JavaScript frontend
- Sends queries to FastAPI backend
- Designed for quick testing and demos

### Secure Credential Handling

- `.env` for private variables
- OAuth credentials stored securely for Google Drive
- Dropbox access tokens supported

## Project Structure
```
.
├── llm_backend/
│   ├── database/
│   ├── prompts/
│   │   └── system_prompt.xml
│   ├── static/
│   │   ├── profile-pic.png
│   │   ├── script.js
│   │   └── style.css
│   ├── templates/
│   │   └── index.html
│   ├── venv/
│   ├── main.py
│   ├── mcp_client.py
│   ├── README.md
│   └── requirements.txt
│
├── mcp_server/
│   ├── venv/
│   ├── credentials.json
│   ├── drive_utils.py
│   ├── dropbox_utils.py
│   ├── README.md
│   ├── requirements.txt
│   ├── server.py
│   ├── token.pickle
│   └── tool_functions.py
│
├── .gitignore
└── README.md
```

## Setup Guide

### Clone the Repository
```bash
git clone https://github.com/yourusername/Python_Final_Project.git
cd Python_Final_Project
```

### Set Up the MCP Server

Handles communication with Google Drive and Dropbox.
```bash
cd mcp_server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Run the MCP Server
```bash
fastmcp run server.py:mcp --transport http --port 8001
```

#### Google Drive Setup

1. Place `credentials.json` into `mcp_server/`
2. On first run, authenticate via browser
3. `token.pickle` is created automatically

#### Dropbox Setup

1. Create a Dropbox app: https://www.dropbox.com/developers/apps
2. Generate a token
3. Save it as: `mcp_server/dropbox_token.txt`

Both backends work equally—selectable via `backend="google"` or `backend="dropbox"`.

### Set Up the LLM Backend
```bash
cd llm_backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### PostgreSQL Database Setup

1. Start local PostgreSQL
2. Create a database: `python_final_project`
3. Add this to `.env`:
```
DATABASE_URL=postgresql://<user>:<password>@localhost:5432/python_final_project
```

The backend auto-creates tables on startup.

#### Run the LLM Backend
```bash
uvicorn main:app --reload
```

### Run the Web Interface

With the backend active, open:
```
http://localhost:5000
```

You can now interact with the system through your browser.

## Environment Variables

Create `llm_backend/.env`:
```
OPENAI_API_KEY=your_api_key_here
MCP_SERVER_URL=http://localhost:8001
```

## Tech Stack

- **Python 3.10+**
- **FastAPI** — backend framework
- **FastMCP** — MCP server provider
- **Google Drive API + Dropbox API**
- **PostgreSQL** — conversation + user data
- **HTML/CSS/JavaScript** — frontend

## Contributors

- Jonathan Conde
- Felipe Monsalvo
- Luis Palma

## Future Improvements

- Support additional storage providers (OneDrive, S3, Box)
- Improve PDF/image preview UI
- Add user authentication / sessions
- Implement caching for faster file operations
