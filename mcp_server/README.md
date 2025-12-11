# MCP Server for Google Drive File Search

An MCP (Model Context Protocol) server for searching files. Currently uses dummy files for testing, will be integrated with Google Drive.

## Setup

### Prerequisites

- Python 3.10 or higher
- pip

### Installation

1. **Clone the repository** (if you haven't already):
```bash
git clone <repository-url>
cd Python_Final_Project
```

2. **Navigate to the MCP server directory**:
```bash
cd mcp_server
```

3. **Create a virtual environment**:
```bash
python3 -m venv venv
```

4. **Activate virtual environment**:
```bash
source venv/bin/activate
```

5. **Install dependencies**:
```bash
pip install -r requirements.txt
```

6. **Configure Dropbox (Optional)**:
   - Create a Dropbox app at https://www.dropbox.com/developers/apps
   - Generate an access token
   - Create a `.env` file in the `mcp_server` directory
   - Add the following line to `.env`:
     ```
     DROPBOX_ACCESS_TOKEN=your_token_here
     ```
   - Restart the MCP server after adding the token

## Running the Server

### Using FastMCP CLI (Recommended)

```bash
fastmcp run server.py:mcp --transport http --port 8001
```

## Available Tools

- **list_files(backend, folder_id=None, folder_name=None)**: List files and folders from Google Drive or Dropbox
  - `backend`: "google" or "dropbox"
  - `folder_id` or `folder_name`: Optional folder to list contents of
- **search_files(backend, query, folder_id=None, folder_name=None)**: Search for files by name in Google Drive or Dropbox
  - `backend`: "google" or "dropbox"
  - `query`: Search term
  - `folder_id` or `folder_name`: Optional folder to search within

## Available Resources

- **file://{file_id}**: Read a file by its ID via URI

## Testing with Dummy Files

The server currently uses dummy files:
- `meeting_notes.txt` - ID: 1
- `project_ideas.txt` - ID: 2
- `document3.txt` - ID: 3
- `tasks.txt` - ID: 4

## Connecting to ChatGPT

To connect this MCP server to ChatGPT, you'll need to configure ChatGPT's MCP settings to point to this server. The server runs via stdio and communicates using JSON-RPC.

## Next Steps

1. Integrate Google Drive API
2. Replace dummy files with real Google Drive file access
3. Add authentication for Google Drive
4. Connect to ChatGPT or other MCP clients

## Troubleshooting

- **Import errors**: Make sure you've activated your virtual environment and installed all dependencies
- **Server won't start**: Check that Python 3.10+ is installed and FastMCP is properly installed
- **Connection issues**: Ensure the server is running and configured correctly in your MCP client
- **Dropbox access denied**: 
  - Make sure you've created a `.env` file in the `mcp_server` directory
  - Verify that `DROPBOX_ACCESS_TOKEN` is set correctly in the `.env` file
  - Ensure the token is valid and has the necessary permissions
  - Restart the MCP server after adding/updating the token

