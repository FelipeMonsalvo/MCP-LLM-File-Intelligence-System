from fastmcp import FastMCP
from dotenv import load_dotenv
load_dotenv()

from tool_functions import list_files_fn

mcp = FastMCP(name="drive-dropbox-mcp")

@mcp.tool()
def list_files(
    backend: str = "google",
    folder_id: str = None,
    folder_name: str = None
) -> str:
    return list_files_fn(
        backend=backend,
        folder_id=folder_id,
        folder_name=folder_name
    )

from tool_functions import search_files_fn

@mcp.tool()
def search_files(
    backend: str = "google",
    query: str = "",
    folder_id: str = None,
    folder_name: str = None
):
    return search_files_fn(
        backend=backend,
        query=query,
        folder_id=folder_id,
        folder_name=folder_name
    )

from tool_functions import get_file_fn
@mcp.tool()
def get_file(
    backend: str,
    file_id: str = None,
    file_path: str = None
) -> str:
    return get_file_fn(
        backend=backend,
        file_id=file_id,
        file_path=file_path
    )

from tool_functions import summarize_file_fn
@mcp.tool()
def summarize_file(backend: str, file_id: str = None, file_path: str = None):
    return summarize_file_fn(
        backend=backend,
        file_id=file_id,
        file_path=file_path
    )