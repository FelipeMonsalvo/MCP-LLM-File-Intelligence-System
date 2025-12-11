import os
import json
import xml.etree.ElementTree as ET
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from mcp_client import get_mcp_tools_for_openai, execute_mcp_tool
from database.auth_routes import router as auth_router, get_current_user
from database.database import init_db, get_db, User, ChatSession, Conversation  
from database.db_utils import (get_or_create_chat_session, get_conversation_history, save_message, get_user_sessions, delete_chat_session, delete_all_user_sessions)

def detect_backend(user_text: str) -> str | None:
    text = user_text.lower()
    if "dropbox" in text or "dbx" in text:
        return "dropbox"
    if "google" in text or ("drive" in text and "dropbox" not in text):
        return "google"
    return None

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:8000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(auth_router)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

client = OpenAI(api_key=OPENAI_API_KEY)

def load_system_prompt():
    path = os.path.join(os.path.dirname(__file__), "prompts", "system_prompt.xml")
    tree = ET.parse(path)
    root = tree.getroot()

    purpose = root.findtext("Purpose", default="")
    capabilities = root.findtext("Capabilities", default="")
    decision_logic = root.findtext("DecisionLogic", default="")
    guidelines = root.findtext("Guidelines", default="")
    formatting = root.findtext("FormattingGuidelines", default="")

    return (
        purpose.strip()
        + "\n\nCapabilities:\n" + capabilities.strip()
        + "\n\nDecision Logic:\n" + decision_logic.strip()
        + "\n\nGuidelines:\n" + guidelines.strip()
        + "\n\nFormatting Guidelines:\n" + formatting.strip()
    )

SYSTEM_PROMPT = load_system_prompt()


class ChatMessage(BaseModel):
    message: str
    session_id: str | None = None

class ChatResponse(BaseModel):
    reply: str
    session_id: str

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    return templates.TemplateResponse(request, "index.html")

@app.get("/login", response_class=HTMLResponse)
async def get_login(request: Request):
    return templates.TemplateResponse(request, "login.html")

@app.get("/signup", response_class=HTMLResponse)
async def get_signup(request: Request):
    return templates.TemplateResponse(request, "signup.html")

@app.get("/favicon.ico")
async def favicon():
    return Response(status_code=204)

@app.get("/chat/history/{session_id}")
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    from fastapi import HTTPException
    
    session = db.query(ChatSession).filter(
        ChatSession.session_id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    conversations = db.query(Conversation).filter(
        Conversation.session_id == session.id 
    ).order_by(Conversation.created_at.asc()).all()
    
    return JSONResponse({
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat()
            }
            for msg in conversations
        ]
    })

@app.post("/chat/new")
async def new_chat(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chat_session = get_or_create_chat_session(db, current_user.id)
    return JSONResponse({"session_id": chat_session.session_id})


@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    chat: ChatMessage,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chat_session = get_or_create_chat_session(db, current_user.id, chat.session_id)
    session_id = chat_session.session_id

    mcp_tools = await get_mcp_tools_for_openai()
    conversation_history = get_conversation_history(db, session_id, current_user.id)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(conversation_history)
    messages.append({"role": "user", "content": chat.message})

    save_message(db, session_id, current_user.id, "user", chat.message)

    iteration = 0
    
    try:
        while iteration < MAX_ITERATIONS:
            iteration += 1
            
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=mcp_tools if mcp_tools else None,
                    tool_choice="auto" if mcp_tools else None,  
                    max_tokens=MAX_TOKENS,
                )
            except Exception as e:
                error_msg = f"OpenAI API error: {str(e)}"
                save_message(db, session_id, current_user.id, "assistant", error_msg)
                return ChatResponse(reply=error_msg, session_id=session_id)

            response_message = response.choices[0].message
            messages.append(response_message)
                    
            if response_message.tool_calls:
                backend_to_use = "google"
                
                detected_from_message = detect_backend(chat.message)
                if detected_from_message:
                    backend_to_use = detected_from_message

                for tool_call in response_message.tool_calls:
                    tool_name = tool_call.function.name

                    try:
                        tool_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError as e:
                        tool_result = f"Error parsing tool arguments: {str(e)}"
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": tool_result
                        })
                        continue

                    if tool_name == "list_files" or tool_name == "search_files":
                        if "backend" in tool_args and tool_args.get("backend", "").lower() in ["dropbox", "google"]:
                            backend_to_use = tool_args["backend"].lower()
                        else:
                            folder_id = tool_args.get("folder_id")
                            folder_name = tool_args.get("folder_name")
                            
                            for msg in reversed(messages[-BACKEND_CONTEXT_MESSAGES:]):
                                role = msg.get("role") if isinstance(msg, dict) else getattr(msg, "role", None)
                                content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)
                                
                                if role == "tool" and content:
                                    content_str = str(content)
                                    content_lower = content_str.lower()
                                    
                                    is_dropbox_result = "[backend: dropbox]" in content_lower
                                    is_google_result = "[backend: google drive]" in content_lower
                                    
                                    if not is_dropbox_result and not is_google_result:
                                        dropbox_patterns = ["dropbox root contents", "dropbox folder:", "dropbox root search", "dropbox folder search"]
                                        google_patterns = ["google drive", "first 5 google drive", "google folder:"]
                                        is_dropbox_result = any(pattern in content_lower for pattern in dropbox_patterns)
                                        is_google_result = any(pattern in content_lower for pattern in google_patterns)
                                    
                                    if is_dropbox_result or is_google_result:
                                        if folder_id or folder_name:
                                            folder_found = False
                                            if folder_id and folder_id in content_str:
                                                folder_found = True
                                            elif folder_name and folder_name.lower() in content_str.lower():
                                                folder_found = True
                                            
                                            if folder_found:
                                                backend_to_use = "dropbox" if is_dropbox_result else "google"
                                                break
                                        else:
                                            backend_to_use = "dropbox" if is_dropbox_result else "google"
                                            break
                            
                            tool_args["backend"] = backend_to_use

                    tool_result = await execute_mcp_tool(tool_name, tool_args)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": tool_name,
                        "content": tool_result
                    })

                continue
            
            else:
                ai_reply = response_message.content
                
                save_message(db, session_id, current_user.id, "assistant", ai_reply)
                
                return ChatResponse(reply=ai_reply, session_id=session_id)

        raise Exception("MAX_ITERATIONS")
    
    except Exception as e:
        if str(e) == "MAX_ITERATIONS":
            error_msg = "ERROR: MAX ITERATIONS REACHED"
        else:
            error_msg = f"An unexpected error occurred: {str(e)}"
        save_message(db, session_id, current_user.id, "assistant", error_msg)
        return ChatResponse(reply=error_msg, session_id=session_id)


@app.get("/chat/sessions")
async def get_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all chat sessions for the current user."""
    sessions = get_user_sessions(db, current_user.id)
    return JSONResponse({"sessions": sessions})


@app.delete("/chat/sessions/{session_id}")
async def delete_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a specific chat session and all its messages."""
    deleted = delete_chat_session(db, session_id, current_user.id)
    if not deleted:
        return JSONResponse(
            {"error": "Session not found or access denied"},
            status_code=404
        )
    return JSONResponse({"message": "Session deleted successfully"})


@app.delete("/chat/sessions")
async def delete_all_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete all chat sessions for the current user."""
    count = delete_all_user_sessions(db, current_user.id)
    return JSONResponse({"message": f"Deleted {count} session(s) successfully", "count": count})


MAX_ITERATIONS = 5
MAX_TOKENS = 500
BACKEND_CONTEXT_MESSAGES = 5