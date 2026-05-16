// Reflection 首页交互
(function () {
  const conversationEl = document.getElementById('conversation');
  const userInput = document.getElementById('user-input');
  const sendBtn = document.getElementById('send-btn');
  const newSessionBtn = document.getElementById('new-session-btn');

  if (!conversationEl || !userInput || !sendBtn || !newSessionBtn) {
    document.body.innerHTML = '<p style="color:red;text-align:center;padding-top:40vh;">页面加载异常，请关闭浏览器重试。</p>';
    return;
  }

  let currentSessionId = null;
  let waiting = false;

  // ── 英雄屏 ────────────────────────────────
  function showHero() {
    conversationEl.innerHTML =
      '<div style="text-align:center;padding-top:20vh">' +
      '<div class="hero-text">今天，<br>什么在你<br>心里？</div>' +
      '<div class="divider"></div>' +
      '<div class="subtitle-text">俯 瞰 自 心</div>' +
      '</div>';
  }

  // ── 输入处理 ─────────────────────────────
  userInput.addEventListener('input', function () {
    sendBtn.classList.toggle('visible', userInput.value.trim().length > 0);
    userInput.style.height = 'auto';
    userInput.style.height = Math.min(userInput.scrollHeight, 200) + 'px';
  });

  userInput.addEventListener('keydown', function (e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      doSend();
    }
  });

  sendBtn.addEventListener('click', doSend);

  // ── 发送消息 ─────────────────────────────
  async function doSend() {
    if (waiting) return;
    var text = userInput.value.trim();
    if (!text) return;

    waiting = true;
    userInput.value = '';
    userInput.style.height = 'auto';
    sendBtn.classList.remove('visible');
    userInput.disabled = true;

    // 创建会话
    try {
      if (!currentSessionId) {
        var sResp = await fetch('/api/sessions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ tag: null })
        });
        var sData = await sResp.json();
        currentSessionId = sData.session_id;
      }
    } catch (e) {
      appendMsg('assistant', '无法创建会话。请确认应用正在运行。');
      waiting = false;
      userInput.disabled = false;
      userInput.focus();
      return;
    }

    // 清除英雄屏
    if (conversationEl.querySelector('.hero-text')) {
      conversationEl.innerHTML = '';
    }

    // 用户消息
    appendMsg('user', text);

    // 加载动画
    var loader = appendLoader();

    try {
      var resp = await fetch('/api/sessions/' + currentSessionId + '/messages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: text })
      });
      var data = await resp.json();
      loader.remove();
      appendMsg('assistant', data.reply || '(空回复)');

      if (data.reply && (data.reply.indexOf('带走') >= 0 || data.reply.indexOf('最值得') >= 0)) {
        newSessionBtn.classList.add('visible');
      }
    } catch (e) {
      loader.remove();
      appendMsg('assistant', '连接断开了，刷新页面试试。');
    }

    waiting = false;
    userInput.disabled = false;
    userInput.focus();
    conversationEl.scrollTop = conversationEl.scrollHeight;
  }

  // ── UI 辅助 ──────────────────────────────
  function appendMsg(role, content) {
    var div = document.createElement('div');
    div.className = 'message ' + role;
    div.textContent = content;
    conversationEl.appendChild(div);
    conversationEl.scrollTop = conversationEl.scrollHeight;
  }

  function appendLoader() {
    var div = document.createElement('div');
    div.className = 'typing-indicator';
    div.innerHTML = '<span></span><span></span><span></span>';
    conversationEl.appendChild(div);
    conversationEl.scrollTop = conversationEl.scrollHeight;
    return div;
  }

  // ── 新复盘 ──────────────────────────────
  newSessionBtn.addEventListener('click', function () {
    currentSessionId = null;
    newSessionBtn.classList.remove('visible');
    conversationEl.innerHTML = '';
    showHero();
    userInput.focus();
  });

  // ── 首次使用检查 ─────────────────────────
  fetch('/api/config')
    .then(function (r) { return r.json(); })
    .then(function (cfg) {
      if (cfg.first_run) window.location.href = '/history';
    })
    .catch(function () {});

  // ── 启动 ────────────────────────────────
  showHero();
  userInput.focus();
})();
