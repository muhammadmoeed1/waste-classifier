const fileInput = document.getElementById('fileInput');
const uploadZone = document.getElementById('uploadZone');
const previewWrap = document.getElementById('previewWrap');
const previewImg = document.getElementById('previewImg');
const fname = document.getElementById('fname');
const fnameText = document.getElementById('fnameText');
const classifyBtn = document.getElementById('classifyBtn');
const clearBtn = document.getElementById('clearBtn');
const errorMsg = document.getElementById('errorMsg');
const resultSection = document.getElementById('resultSection');
const resultLabel = document.getElementById('resultLabel');
const resultBadge = document.getElementById('resultBadge');
const confVal = document.getElementById('confVal');
const confBar = document.getElementById('confBar');
const probsList = document.getElementById('probsList');
const catItems = document.querySelectorAll('.cat-item');

const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const chatSend = document.getElementById('chatSend');

let lastClassificationLabel = null;
let chatHistory = [];

fileInput.addEventListener('change', () => {
  const file = fileInput.files[0];
  if (!file) return;
  previewImg.src = URL.createObjectURL(file);
  previewWrap.style.display = 'block';
  fname.style.display = 'block';
  fnameText.textContent = ' ' + file.name;
  classifyBtn.disabled = false;
  hideError();
  hideResult();
});

clearBtn.addEventListener('click', () => {
  fileInput.value = '';
  previewImg.src = '';
  previewWrap.style.display = 'none';
  fname.style.display = 'none';
  fnameText.textContent = '';
  classifyBtn.disabled = true;
  hideError();
  hideResult();
  catItems.forEach(el => el.classList.remove('active'));
  lastClassificationLabel = null;
});

classifyBtn.addEventListener('click', async () => {
  const file = fileInput.files[0];
  if (!file) return;

  classifyBtn.disabled = true;
  classifyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Classifying...';
  hideError();

  try {
    const formData = new FormData();
    formData.append('image', file);
    const res = await fetch('/api/predict', { method: 'POST', body: formData });
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail || `Request failed (${res.status})`);
    }
    const data = await res.json();
    showResult(data);
  } catch (err) {
    showError(err.message || 'Something went wrong.');
  } finally {
    classifyBtn.disabled = false;
    classifyBtn.innerHTML = '<i class="fas fa-magnifying-glass"></i> Classify waste';
  }
});

function showError(msg) {
  errorMsg.textContent = msg;
  errorMsg.style.display = 'block';
}
function hideError() {
  errorMsg.style.display = 'none';
}
function hideResult() {
  resultSection.style.display = 'none';
}

function showResult(data) {
  lastClassificationLabel = data.label;

  resultLabel.textContent = data.label;
  resultBadge.className = 'badge ' + (data.recyclable ? 'badge-rec' : 'badge-norec');
  resultBadge.innerHTML = data.recyclable
    ? '<i class="fas fa-check"></i> Recyclable'
    : '<i class="fas fa-xmark"></i> Not recyclable';

  confVal.textContent = data.confidence + '%';
  confBar.style.width = '0%';
  setTimeout(() => { confBar.style.width = data.confidence + '%'; }, 50);

  probsList.innerHTML = '';
  const sorted = Object.entries(data.probabilities).sort((a, b) => b[1] - a[1]);
  for (const [name, pct] of sorted) {
    const row = document.createElement('div');
    row.className = 'prob-row';
    row.innerHTML = `
      <span class="prob-name">${name}</span>
      <span class="prob-bar-bg"><span class="prob-bar-fill" style="width:${pct}%"></span></span>
      <span class="prob-pct">${pct}%</span>
    `;
    probsList.appendChild(row);
  }

  catItems.forEach(el => el.classList.toggle('active', el.dataset.cat === data.label));
  resultSection.style.display = 'block';

  addAssistantMessage(
    `I classified this as **${data.label}** (${data.confidence}% confidence). Ask me anything about how to recycle it!`
  );
}

function addUserMessage(text) {
  const div = document.createElement('div');
  div.className = 'chat-msg user';
  div.innerHTML = `<div class="bubble"></div>`;
  div.querySelector('.bubble').textContent = text;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function addAssistantMessage(text) {
  const div = document.createElement('div');
  div.className = 'chat-msg assistant';
  div.innerHTML = `<div class="bubble"></div>`;
  div.querySelector('.bubble').textContent = text;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return div.querySelector('.bubble');
}

async function sendChat() {
  const question = chatInput.value.trim();
  if (!question) return;

  addUserMessage(question);
  chatInput.value = '';
  chatSend.disabled = true;

  const bubble = addAssistantMessage('');
  bubble.innerHTML = '<i class="fas fa-ellipsis fa-fade"></i>';

  try {
    const res = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        question,
        classification_label: lastClassificationLabel,
        history: chatHistory,
      }),
    });

    if (!res.ok || !res.body) {
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail || `Request failed (${res.status})`);
    }

    bubble.textContent = '';
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let fullText = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, { stream: true });
      fullText += chunk;
      bubble.textContent = fullText;
      chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    chatHistory.push({ role: 'user', content: question });
    chatHistory.push({ role: 'assistant', content: fullText });
  } catch (err) {
    bubble.textContent = 'Error: ' + (err.message || 'something went wrong.');
  } finally {
    chatSend.disabled = false;
  }
}

chatSend.addEventListener('click', sendChat);
chatInput.addEventListener('keydown', (e) => {
  if (e.key === 'Enter') sendChat();
});
