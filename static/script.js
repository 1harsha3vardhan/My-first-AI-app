const log = document.getElementById('log');
const form = document.getElementById('promptForm');
const input = document.getElementById('promptInput');
const sessionList = document.getElementById('sessionList');
const newChatBtn = document.getElementById('newChatBtn');
const sessionTitle = document.getElementById('sessionTitle');
const sidebar = document.getElementById('sidebar');
const sidebarToggle = document.getElementById('sidebarToggle');

let currentSessionId = null;
let sessions = [];

// ---------------------------------------------------------------
// Rendering helpers
// ---------------------------------------------------------------
function renderMarkdown(text) {
  const rawHtml = marked.parse(text, { breaks: true });
  return DOMPurify.sanitize(rawHtml);
}

function addLine(tag, text, extraClass = '', asMarkdown = false) {
  const line = document.createElement('div');
  line.className = `log-line ${extraClass || tag}`;
  const textSpan = document.createElement('span');
  textSpan.className = 'text';
  if (asMarkdown) {
    textSpan.innerHTML = renderMarkdown(text);
  } else {
    textSpan.textContent = text;
  }
  const tagSpan = document.createElement('span');
  tagSpan.className = 'tag';
  tagSpan.textContent = tag;
  line.appendChild(tagSpan);
  line.appendChild(textSpan);
  log.appendChild(line);
  log.scrollTop = log.scrollHeight;
  return line;
}

function clearLog() {
  log.innerHTML = '';
}

function showSystemLine(text) {
  addLine('system', text, 'system');
}

// ---------------------------------------------------------------
// Session list (sidebar)
// ---------------------------------------------------------------
async function fetchSessions() {
  const res = await fetch('/api/sessions');
  sessions = await res.json();
  renderSessionList();
}

function renderSessionList() {
  sessionList.innerHTML = '';

  if (sessions.length === 0) {
    const empty = document.createElement('div');
    empty.className = 'empty-sessions';
    empty.textContent = 'No saved chats yet. Click "+ new" to start one.';
    sessionList.appendChild(empty);
    return;
  }

  sessions.forEach((s) => {
    const item = document.createElement('div');
    item.className = 'session-item' + (s.id === currentSessionId ? ' active' : '');
    item.tabIndex = 0;

    const title = document.createElement('span');
    title.className = 'title';
    title.textContent = s.title;

    const deleteBtn = document.createElement('button');
    deleteBtn.className = 'delete-btn';
    deleteBtn.textContent = '×';
    deleteBtn.title = 'Delete chat';
    deleteBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      deleteSession(s.id);
    });

    item.appendChild(title);
    item.appendChild(deleteBtn);
    item.addEventListener('click', () => loadSession(s.id));

    sessionList.appendChild(item);
  });
}

async function createSession() {
  const res = await fetch('/api/sessions', { method: 'POST' });
  const data = await res.json();
  await fetchSessions();
  await loadSession(data.id);
  closeSidebarOnMobile();
}

async function deleteSession(id) {
  await fetch(`/api/sessions/${id}`, { method: 'DELETE' });
  await fetchSessions();

  if (id === currentSessionId) {
    if (sessions.length > 0) {
      await loadSession(sessions[0].id);
    } else {
      await createSession();
    }
  }
}

async function loadSession(id) {
  currentSessionId = id;
  const res = await fetch(`/api/sessions/${id}`);
  const data = await res.json();

  clearLog();
  showSystemLine("Session loaded. Model: gemini-3.6-flash. Type a message below and press enter.");

  data.messages.forEach((msg) => {
    if (msg.role === 'user') {
      addLine('you', msg.text, 'user');
    } else {
      addLine('ai', msg.text, 'ai', true);
    }
  });

  sessionTitle.textContent = `~/my-first-ai-app — ${data.title}`;
  renderSessionList();
  closeSidebarOnMobile();
}

// ---------------------------------------------------------------
// Sending messages
// ---------------------------------------------------------------
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message || !currentSessionId) return;

  addLine('you', message, 'user');
  input.value = '';
  input.disabled = true;

  const thinkingLine = addLine('ai', '', 'ai thinking');

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: currentSessionId, message }),
    });
    const data = await res.json();

    thinkingLine.classList.remove('thinking');

    if (data.error) {
      thinkingLine.className = 'log-line error';
      thinkingLine.querySelector('.tag').textContent = 'error';
      thinkingLine.querySelector('.text').textContent = data.error;
    } else {
      thinkingLine.querySelector('.text').innerHTML = renderMarkdown(data.reply);
      if (data.title) {
        sessionTitle.textContent = `~/my-first-ai-app — ${data.title}`;
      }
      await fetchSessions();
    }
  } catch (err) {
    thinkingLine.classList.remove('thinking');
    thinkingLine.className = 'log-line error';
    thinkingLine.querySelector('.tag').textContent = 'error';
    thinkingLine.querySelector('.text').textContent =
      'Could not reach the server. Is it still running?';
  } finally {
    input.disabled = false;
    input.focus();
  }
});

// ---------------------------------------------------------------
// Sidebar toggle (mobile)
// ---------------------------------------------------------------
sidebarToggle.addEventListener('click', () => {
  sidebar.classList.toggle('open');
});

function closeSidebarOnMobile() {
  if (window.innerWidth <= 720) {
    sidebar.classList.remove('open');
  }
}

newChatBtn.addEventListener('click', createSession);

// ---------------------------------------------------------------
// Startup: load sessions, open the most recent one (or create one)
// ---------------------------------------------------------------
(async function init() {
  await fetchSessions();
  if (sessions.length > 0) {
    await loadSession(sessions[0].id);
  } else {
    await createSession();
  }
})();
