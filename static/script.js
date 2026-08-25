const log = document.getElementById('log');
const form = document.getElementById('promptForm');
const input = document.getElementById('promptInput');
const statusEl = document.getElementById('status');

function addLine(tag, text, extraClass = '') {
  const line = document.createElement('div');
  line.className = `log-line ${extraClass || tag}`;
  line.innerHTML = `<span class="tag">${tag}</span><span class="text"></span>`;
  line.querySelector('.text').textContent = text;
  log.appendChild(line);
  log.scrollTop = log.scrollHeight;
  return line;
}

form.addEventListener('submit', async (e) => {
  e.preventDefault();
  const message = input.value.trim();
  if (!message) return;

  addLine('you', message, 'user');
  input.value = '';
  input.disabled = true;

  const thinkingLine = addLine('ai', '', 'ai thinking');

  try {
    const res = await fetch('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    });
    const data = await res.json();

    thinkingLine.classList.remove('thinking');

    if (data.error) {
      thinkingLine.className = 'log-line error';
      thinkingLine.querySelector('.tag').textContent = 'error';
      thinkingLine.querySelector('.text').textContent = data.error;
    } else {
      thinkingLine.querySelector('.text').textContent = data.reply;
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
