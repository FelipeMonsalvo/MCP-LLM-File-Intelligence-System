let currentSessionId = null;
let lastUserMessage = null;
let isSignedIn = false;
let userName = null;

async function initAuth() {
  try {
    const response = await fetch('/auth/me', {method: 'GET', credentials: 'include'});
    
    if (response.ok) {
      const userData = await response.json();
      isSignedIn = true;
      userName = userData.username;
      updateHeader();
      enableChatInput();
      loadChatSessions();

    } else {
      isSignedIn = false;
      userName = null;
      updateHeader();
      disableChatInput();
    }

  } catch (error) {
    console.error('Auth check failed:', error);
    isSignedIn = false;
    userName = null;
    updateHeader();
    disableChatInput();
  }
}


async function loadChatSessions() {
  try {
    const response = await fetch('/chat/sessions', {
      method: 'GET',
      credentials: 'include'
    });
    
    if (response.ok) {
      const data = await response.json();
      displayChatSessions(data.sessions);
    }

  } catch (error) {
    console.error('Failed to load chat sessions:', error);
  }
}


function displayChatSessions(sessions) {
  const chatList = document.querySelector('.chat-list');
  if (!chatList) return;
  
  chatList.innerHTML = '';
  
  if (!sessions || sessions.length === 0) {
    chatList.innerHTML = '<div class="no-sessions">No chat history yet</div>';
    return;
  }
  
  sessions.forEach(session => {
    const sessionDiv = document.createElement('div');
    sessionDiv.className = 'chat-session-item';

    if (session.session_id === currentSessionId) {
      sessionDiv.classList.add('active');
    }
    
    const title = session.title || `Chat ${new Date(session.created_at).toLocaleDateString()}`;
    const date = new Date(session.created_at).toLocaleString();
    
    sessionDiv.innerHTML = `
      <div class="session-content">
        <div class="session-title">${title}</div>
        <div class="session-date">${date}</div>
      </div>
      <button class="delete-session-btn" title="Delete chat" onclick="event.stopPropagation(); deleteChatSession('${session.session_id}')">×</button>
    `;
    
    sessionDiv.onclick = () => loadSession(session.session_id);
    
    chatList.appendChild(sessionDiv);
  });
}


async function loadSession(sessionId) {
  try {
    const response = await fetch(`/chat/history/${sessionId}`, {
      method: 'GET',
      credentials: 'include'
    });
    
    if (response.ok) {
      const data = await response.json();
      currentSessionId = sessionId;
      
      const chatDiv = document.getElementById('chat');
      chatDiv.innerHTML = '';
      
      data.messages.forEach(msg => {addMessage(msg.content, msg.role, formatTimestamp(new Date(msg.created_at)), msg.id);});

      document.querySelectorAll('.chat-session-item').forEach(item => {
        item.classList.remove('active');
      });

      document.querySelector(`[data-session-id="${sessionId}"]`)?.classList.add('active');
      
      chatDiv.scrollTop = chatDiv.scrollHeight;
    }
  } catch (error) {
    console.error('Failed to load session:', error);
  }
}


async function createNewChat() {
  try {
    const response = await fetch('/chat/new', {
      method: 'POST',
      credentials: 'include'
    });
    
    if (response.ok) {
      const data = await response.json();
      currentSessionId = data.session_id;
      
      const chatDiv = document.getElementById('chat');
      chatDiv.innerHTML = '<div class="empty-state"><p>Start a conversation by typing a message below!</p></div>';
      
      loadChatSessions();
    }
  } catch (error) {
    console.error('Failed to create new chat:', error);
  }
}

async function deleteChatSession(sessionId) {
  if (!confirm('Are you sure you want to delete this chat? This cannot be undone.')) {
    return;
  }
  
  try {
    const response = await fetch(`/chat/sessions/${sessionId}`, {
      method: 'DELETE',
      credentials: 'include'
    });
    
    if (response.ok) {
      if (sessionId === currentSessionId) {
        currentSessionId = null;
        const chatDiv = document.getElementById("chat");
        chatDiv.innerHTML = '<div class="empty-state"><p>Start a conversation by typing a message below!</p></div>';
      }
      
      loadChatSessions();
    } else {
      const data = await response.json();
      alert(data.error || 'Failed to delete chat session');
    }
  } catch (error) {
    console.error('Failed to delete chat session:', error);
    alert('An error occurred while deleting the chat session');
  }
}

async function deleteAllChatSessions() {
  if (!confirm('Are you sure you want to delete ALL OF THE chats? This action cannot be undone.')) {
    return;
  }
  
  try {
    const response = await fetch('/chat/sessions', {
      method: 'DELETE',
      credentials: 'include'
    });
    
    if (response.ok) {
      const data = await response.json();
      currentSessionId = null;
      
      const chatDiv = document.getElementById("chat");
      chatDiv.innerHTML = '<div class="empty-state"><p>Start a conversation by typing a message below.</p></div>';
      
      loadChatSessions();
      
      alert(`Successfully deleted ${data.count || 0} chat(s)`);

    } else {
      const data = await response.json();
      alert(data.error || 'Failed to delete all chat sessions');
    }
  } catch (error) {
    console.error('Failed to delete all chat sessions:', error);
    alert('An error occurred while deleting chat sessions');
  }
}

function getAuthHeaders() {
  return { "Content-Type": "application/json" };
}


async function logout() {
  try {
    await fetch('/auth/logout', {
      method: 'POST',
      credentials: 'include'
    });
  } catch (error) {
    console.error('Logout error:', error);

  }
  
  isSignedIn = false;
  userName = null;
  currentSessionId = null;
  updateHeader();
  disableChatInput();
  window.location.href = '/login';
}

function enableChatInput() {
  const input = document.getElementById("input");
  const sendBtn = document.getElementById("sendBtn");

  if (input) {
    input.disabled = false;
    input.placeholder = "Type a message and press Enter";
  }

  if (sendBtn) {
    sendBtn.disabled = false;
  }
}

function disableChatInput() {
  const input = document.getElementById("input");
  const sendBtn = document.getElementById("sendBtn");

  if (input) {
    input.disabled = true;
    input.placeholder = "Please sign in to send messages";
  }

  if (sendBtn) {
    sendBtn.disabled = true;
  }
}

function getSessionId() {
  return currentSessionId;
}

function setSessionId(sessionId) {
  currentSessionId = sessionId;
}

function attachLoginForm() {
  const form = document.getElementById('loginForm');
  if (!form) return;

  const errorDiv = document.getElementById('errorMessage');
  const submitBtn = form.querySelector('.login-btn');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('username')?.value || '';
    const password = document.getElementById('password')?.value || '';

    if (errorDiv) {
      errorDiv.style.display = 'none';
      errorDiv.textContent = '';
    }

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Signing in...';
    }

    try {
      const formData = new URLSearchParams();
      formData.append('username', username);
      formData.append('password', password);

      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        credentials: 'include',
        body: formData.toString()
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Login failed');
      }

      window.location.href = '/';

    } catch (error) {
      if (errorDiv) {
        errorDiv.textContent = error.message || 'An error occurred during login';
        errorDiv.style.display = 'block';
      }

      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Sign In';
      }
    }
  });
}

function attachSignupForm() {
  const form = document.getElementById('signupForm');
  if (!form) return;

  const errorDiv = document.getElementById('errorMessage');
  const submitBtn = form.querySelector('.login-btn');

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const username = document.getElementById('username')?.value || '';
    const email = document.getElementById('email')?.value || '';
    const password = document.getElementById('password')?.value || '';
    const confirmPassword = document.getElementById('confirmPassword')?.value || '';
    const termsChecked = document.getElementById('terms')?.checked;

    if (errorDiv) {
      errorDiv.style.display = 'none';
      errorDiv.textContent = '';
    }

    if (!termsChecked) {
      if (errorDiv) {
        errorDiv.textContent = 'Please agree to the Terms and Conditions to continue.';
        errorDiv.style.display = 'block';
      }
      return;
    }

    if (password !== confirmPassword) {
      if (errorDiv) {
        errorDiv.textContent = 'Passwords do not match';
        errorDiv.style.display = 'block';
      }
      return;
    }

    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Creating account. Please hold';
    }

    try {
      const response = await fetch('/auth/register', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || 'Registration failed');
      }

      alert('Account created successfully! Please sign in.');
      window.location.href = '/login';

    } catch (error) {
      if (errorDiv) {
        errorDiv.textContent = error.message || 'An error occurred during registration';
        errorDiv.style.display = 'block';
      }

      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Sign Up';
      }
    }
  });
}

function formatTimestamp(date = new Date()) {
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

function parseMessage(content) {
  let parsed = content
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;');
  
  parsed = parsed.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
  parsed = parsed.replace(/\*([^*]+?)\*/g, '<em>$1</em>');
  parsed = parsed.replace(/\\n/g, '<br>').replace(/\n/g, '<br>');
  
  return parsed;
}

function addMessage(content, type = 'assistant', timestamp = null, messageId = null) {
  const chatDiv = document.getElementById("chat");
  
  const emptyState = chatDiv.querySelector('.empty-state');
  if (emptyState) {
    emptyState.remove();
  }
  
  if (!messageId) {
    messageId = `msg-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }
  
  const messageDiv = document.createElement("div");
  messageDiv.className = `message message-${type}`;
  messageDiv.dataset.messageId = messageId;
  
  const label = type === 'user' ? 'You' : type === 'error' ? 'Error' : 'AI';
  const time = timestamp || formatTimestamp();
  
  const headerDiv = document.createElement("div");
  headerDiv.className = "message-header";
  
  const labelSpan = document.createElement("span");
  labelSpan.className = "message-label";
  labelSpan.textContent = label;
  
  const timeSpan = document.createElement("span");
  timeSpan.className = "message-time";
  timeSpan.textContent = time;
  
  headerDiv.appendChild(labelSpan);
  headerDiv.appendChild(timeSpan);
  
  const bubbleDiv = document.createElement("div");
  bubbleDiv.className = "message-bubble";
  
  const contentDiv = document.createElement("div");
  contentDiv.className = "message-content";
  
  if (type === 'assistant') {
    contentDiv.innerHTML = parseMessage(content);
  } else {
    contentDiv.textContent = content;
  }
  
  bubbleDiv.appendChild(contentDiv);
  
  const actionsDiv = document.createElement("div");
  actionsDiv.className = "message-actions";
  
  const copyBtn = document.createElement("button");
  copyBtn.className = "action-btn copy-btn";
  copyBtn.title = "Copy message";
  copyBtn.textContent = "Copy";
  copyBtn.onclick = () => copyMessage(messageId);
  
  if (type === 'error') {
    const retryBtn = document.createElement("button");
    retryBtn.className = "action-btn retry-btn";
    retryBtn.title = "Retry";
    retryBtn.textContent = "Retry";
    retryBtn.onclick = () => retryLastMessage();
    actionsDiv.appendChild(retryBtn);
  }
  
  actionsDiv.appendChild(copyBtn);
  
  messageDiv.appendChild(headerDiv);
  messageDiv.appendChild(bubbleDiv);
  messageDiv.appendChild(actionsDiv);
  
  chatDiv.appendChild(messageDiv);
  
  return messageDiv;
}

async function copyMessage(messageId) {
  const messageDiv = document.querySelector(`[data-message-id="${messageId}"]`);
  if (!messageDiv) return;
  
  const bubble = messageDiv.querySelector('.message-bubble');
  if (!bubble) return;
  
  const contentDiv = bubble.querySelector('.message-content');
  if (!contentDiv) return;
  
  const text = contentDiv.textContent || contentDiv.innerText;
  
  try {
    await navigator.clipboard.writeText(text);
    const copyBtn = messageDiv.querySelector('.copy-btn');
    
    if (copyBtn) {
      const originalText = copyBtn.textContent;
      copyBtn.textContent = "Copied!";
      copyBtn.style.color = "#4ade80";
      setTimeout(() => {copyBtn.textContent = originalText; copyBtn.style.color = "";}, 2000);
    }
  } catch (err) {
    console.error('Failed to copy:', err);
  }
}

async function retryLastMessage() {
  if (!lastUserMessage) {
    return;
  }
  
  const errorMessages = document.querySelectorAll('.message-error');

  if (errorMessages.length > 0) {
    errorMessages[errorMessages.length - 1].remove();
  }
  
  const input = document.getElementById("input");
  input.value = lastUserMessage;
  await sendMessage();
}

function showLoading() {
  const chatDiv = document.getElementById("chat");
  const emptyState = chatDiv.querySelector('.empty-state');

  if (emptyState) {
    emptyState.remove();
  }
  
  const loadingDiv = document.createElement("div");
  loadingDiv.className = "loading";
  loadingDiv.id = "loading-indicator";
  loadingDiv.innerHTML = `<div class="spinner"></div><span>AI is thinking...</span>`;
  
  chatDiv.appendChild(loadingDiv);
}

function hideLoading() {
  const loadingDiv = document.getElementById("loading-indicator");

  if (loadingDiv) {
    loadingDiv.remove();
  }
}

async function sendMessage() {
  if (!isSignedIn) {
    addMessage('Please sign in to send messages.', 'error');
    return;
  }

  const input = document.getElementById("input");
  const msg = input.value.trim();

  if (!msg) return;

  lastUserMessage = msg;

  addMessage(msg, 'user');
  input.value = "";
  input.disabled = true;
  const sendBtn = document.getElementById("sendBtn");

  if (sendBtn) sendBtn.disabled = true;
  
  showLoading();

  try {
    const sessionId = getSessionId();
    const res = await fetch("/chat", {
      method: "POST",
      headers: getAuthHeaders(),
      credentials: 'include',
      body: JSON.stringify({ 
        message: msg,
        session_id: sessionId 
      })
    });

    hideLoading();

    if (!res.ok) {
      if (res.status === 401) {
        addMessage('Your session has expired. Please sign in again', 'error');
        isSignedIn = false;
        userName = null;
        updateHeader();
        disableChatInput();
        return;
      }

      const errorData = await res.json().catch(() => ({ error: `HTTP ${res.status}: ${res.statusText}` }));
      addMessage(errorData.detail || errorData.error || 'An error occurred', 'error');
      return;
    }

    const data = await res.json();
    
    if (data.reply && data.reply.toLowerCase().includes('error')) {
      addMessage(data.reply, 'error');
    } else {
      addMessage(data.reply || 'No response received', 'assistant');

    }
    
    if (data.session_id) {
      setSessionId(data.session_id);
      loadChatSessions(); 
    }

  } catch (err) {
    hideLoading();
    addMessage(`Network error: ${err.message}. Please check your connection and try again.`, 'error');
  } finally {
    if (isSignedIn) {
      input.disabled = false;

      if (sendBtn) sendBtn.disabled = false;
      input.focus();
    }
  }
}

function sendOnEnter(event) {
  if (event.key === "Enter" && !event.shiftKey) {event.preventDefault(); sendMessage();}
}

function setProfilePic(imageUrl) {
  const profileImage = document.getElementById("profileImage");
  const profileInitials = document.getElementById("profileInitials");
  const profilePic = document.getElementById("profilePic");
  
  if (!profileImage || !profileInitials || !profilePic) return;
  
  if (imageUrl) {
    profileImage.src = imageUrl;
    profileImage.style.display = "block";
    profileInitials.style.display = "none";
    profilePic.classList.add("has-image");

  } else {
    profileImage.style.display = "none";
    profileInitials.style.display = "block";
    profilePic.classList.remove("has-image");
  }
}

function updateHeader() {
  const userNameEl = document.getElementById("userName");
  const signInBtn = document.getElementById("signInBtn");
  const logoutBtn = document.getElementById("logoutBtn");
  
  if (isSignedIn && userName) {
    if (userNameEl) {
      userNameEl.textContent = userName;
      userNameEl.style.display = "inline-block";
      userNameEl.style.cursor = "default";
      userNameEl.title = "";
    }

    if (logoutBtn) {
      logoutBtn.style.display = "inline-block";
    }

    if (signInBtn) {
      signInBtn.style.display = "none";
    }

  } else {
    if (userNameEl) {
      userNameEl.style.display = "none";
    }

    if (logoutBtn) {
      logoutBtn.style.display = "none";
    }
    
    if (signInBtn) {
      signInBtn.style.display = "inline-block";
    }
  }
}

document.addEventListener('DOMContentLoaded', () => {
  updateHeader();
  setProfilePic('/static/profile-pic.png'); 
  
  attachLoginForm();
  attachSignupForm();
  
  const input = document.getElementById("input");
  if (input) {
    input.addEventListener('keydown', sendOnEnter);
  }
  
  const sendBtn = document.getElementById("sendBtn");
  if (sendBtn) {
    sendBtn.addEventListener('click', sendMessage);
  }
  
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener('click', logout);
  }
  
  const newChatBtn = document.querySelector('.new-chat-icon');
  if (newChatBtn) {
    newChatBtn.addEventListener('click', createNewChat);
  }
  
  initAuth().catch(error => {console.error('Failed to initialize auth:', error); disableChatInput();});

});