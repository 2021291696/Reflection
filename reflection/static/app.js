// Reflection 首页交互
const conversationEl = document.getElementById('conversation');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const newSessionBtn = document.getElementById('new-session-btn');

let currentSessionId = null;
let isWaitingForAI = false;

// ── 初始化 ───────────────────────────────
async function init() {
  showHeroScreen();
  userInput.addEventListener('input', onInput);
  userInput.addEventListener('keydown', onKeydown);
  sendBtn.addEventListener('click', sendMessage);
  newSessionBtn.addEventListener('click', startNewSession);
  checkFirstRun();
}

async function checkFirstRun() {
  try {
    const resp = await fetch('/api/config');
    const cfg = await resp.json();
    if (cfg.first_run) {
      window.location.href = '/history';
    }
  } catch (e) {
    // server not ready yet, ignore
  }
}

// ── 英雄屏 ────────────────────────────────
function showHeroScreen() {
  conversationEl.innerHTML = `
    <div style="text-align:center;padding-top:20vh">
      <div class="hero-text">今天，<br>什么在你<br>心里？</div>
      <div class="divider"></div>
      <div class="subtitle-text">俯 瞰 自 心</div>
    </div>`;
}

// ── 输入处理 ─────────────────────────────
function onInput() {
  const hasText = userInput.value.trim().length > 0;
  sendBtn.classList.toggle('visible', hasText);
  userInput.style.height = 'auto';
  userInput.style.height = Math.min(userInput.scrollHeight, 200) + 'px';
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    if (!isWaitingForAI) sendMessage();
  }
}

// ── 发送消息 ─────────────────────────────
async function sendMessage() {
  const text = userInput.value.trim();
  if (!text || isWaitingForAI) return;

  userInput.value = '';
  userInput.style.height = 'auto';
  sendBtn.classList.remove('visible');

  if (!currentSessionId) {
    await createSession();
  }

  clearHeroIfNeeded();
  appendMessage('user', text);

  const loader = appendLoader();
  isWaitingForAI = true;
  userInput.disabled = true;

  try {
    const resp = await fetch(`/api/sessions/${currentSessionId}/messages`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: text }),
    });
    const data = await resp.json();
    loader.remove();
    appendMessage('assistant', data.reply);

    if (data.reply.includes('带走') || data.reply.includes('最值得')) {
      newSessionBtn.classList.add('visible');
    }
  } catch (err) {
    loader.remove();
    appendMessage('assistant', '连接断开了，刷新页面试试。');
  }

  isWaitingForAI = false;
  userInput.disabled = false;
  userInput.focus();
  scrollToBottom();
}

async function createSession() {
  const resp = await fetch('/api/sessions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tag: null }),
  });
  const data = await resp.json();
  currentSessionId = data.session_id;
}

// ── UI 辅助 ──────────────────────────────
function clearHeroIfNeeded() {
  const hero = conversationEl.querySelector('.hero-text');
  if (hero) conversationEl.innerHTML = '';
}

function appendMessage(role, content) {
  const div = document.createElement('div');
  div.className = `message ${role}`;
  div.textContent = content;
  conversationEl.appendChild(div);
  scrollToBottom();
}

function appendLoader() {
  const div = document.createElement('div');
  div.className = 'typing-indicator';
  div.innerHTML = '<span></span><span></span><span></span>';
  conversationEl.appendChild(div);
  scrollToBottom();
  return div;
}

function scrollToBottom() {
  conversationEl.scrollTop = conversationEl.scrollHeight;
}

async function startNewSession() {
  currentSessionId = null;
  newSessionBtn.classList.remove('visible');
  conversationEl.innerHTML = '';
  showHeroScreen();
  userInput.focus();
}

document.addEventListener('DOMContentLoaded', init);
