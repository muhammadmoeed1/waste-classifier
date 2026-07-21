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
const gradcamSection = document.getElementById('gradcamSection');
const gradcamImg = document.getElementById('gradcamImg');
const impactSection = document.getElementById('impactSection');
const impactHeadline = document.getElementById('impactHeadline');
const impactStats = document.getElementById('impactStats');
const impactFact = document.getElementById('impactFact');

const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const chatSend = document.getElementById('chatSend');
const micBtn = document.getElementById('micBtn');

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

  if (data.gradcam_image) {
    gradcamImg.src = data.gradcam_image;
    gradcamSection.style.display = 'block';
  } else {
    gradcamSection.style.display = 'none';
  }

  if (data.impact) {
    impactHeadline.textContent = data.impact.headline;
    impactStats.innerHTML = '';
    if (data.impact.co2_saved_per_kg != null) {
      impactStats.innerHTML += `
        <div class="impact-stat"><span class="val">${data.impact.co2_saved_per_kg} kg</span><span class="lbl">CO&#8322; saved / kg</span></div>`;
    }
    if (data.impact.energy_saved_pct != null) {
      impactStats.innerHTML += `
        <div class="impact-stat"><span class="val">${data.impact.energy_saved_pct}%</span><span class="lbl">Energy saved</span></div>`;
    }
    impactFact.textContent = data.impact.fact;
    impactSection.style.display = 'block';
  } else {
    impactSection.style.display = 'none';
  }

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

// --- Voice input (record -> Groq Whisper transcription -> fill chat input) ---
let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (e) => { if (e.data.size > 0) audioChunks.push(e.data); };
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach(track => track.stop());
      await transcribeAndFill();
    };
    mediaRecorder.start();
    isRecording = true;
    micBtn.classList.add('recording');
  } catch (err) {
    addAssistantMessage('Could not access your microphone: ' + (err.message || err));
  }
}

function stopRecording() {
  if (mediaRecorder && isRecording) {
    mediaRecorder.stop();
    isRecording = false;
    micBtn.classList.remove('recording');
  }
}

async function transcribeAndFill() {
  if (audioChunks.length === 0) return;
  const blob = new Blob(audioChunks, { type: 'audio/webm' });

  micBtn.disabled = true;
  micBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

  try {
    const formData = new FormData();
    formData.append('audio', blob, 'recording.webm');
    const res = await fetch('/api/transcribe', { method: 'POST', body: formData });
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail || `Request failed (${res.status})`);
    }
    const data = await res.json();
    chatInput.value = data.text;
    chatInput.focus();
  } catch (err) {
    addAssistantMessage('Voice transcription failed: ' + (err.message || 'something went wrong.'));
  } finally {
    micBtn.disabled = false;
    micBtn.innerHTML = '<i class="fas fa-microphone"></i>';
  }
}

micBtn.addEventListener('click', () => {
  if (!navigator.mediaDevices || !window.MediaRecorder) {
    addAssistantMessage('Voice input is not supported in this browser.');
    return;
  }
  if (isRecording) {
    stopRecording();
  } else {
    startRecording();
  }
});

// --- Mode tabs (Upload / Live Camera / Multi-Item) ---
const modeTabs = document.querySelectorAll('.mode-tab');
const modePanels = document.querySelectorAll('.mode-panel');

modeTabs.forEach((tab) => {
  tab.addEventListener('click', () => {
    const mode = tab.dataset.mode;
    modeTabs.forEach((t) => t.classList.toggle('active', t === tab));
    modePanels.forEach((p) => { p.style.display = p.dataset.mode === mode ? 'block' : 'none'; });
    if (mode !== 'camera') stopCamera();
  });
});

// --- Live camera mode ---
const cameraVideo = document.getElementById('cameraVideo');
const cameraCanvas = document.getElementById('cameraCanvas');
const cameraStartBtn = document.getElementById('cameraStartBtn');
const cameraStopBtn = document.getElementById('cameraStopBtn');
const cameraLiveBadge = document.getElementById('cameraLiveBadge');
const cameraLiveLabel = document.getElementById('cameraLiveLabel');
const cameraLiveConf = document.getElementById('cameraLiveConf');
const cameraPlaceholder = document.getElementById('cameraPlaceholder');
const cameraErrorMsg = document.getElementById('cameraErrorMsg');

let cameraStream = null;
let cameraLoopId = null;
let cameraBusy = false;
const CAMERA_INTERVAL_MS = 2000;

async function startCamera() {
  try {
    cameraStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment' },
    });
    cameraVideo.srcObject = cameraStream;
    cameraPlaceholder.style.display = 'none';
    cameraStartBtn.style.display = 'none';
    cameraStopBtn.style.display = 'flex';
    cameraErrorMsg.style.display = 'none';

    cameraLoopId = setInterval(captureAndClassifyFrame, CAMERA_INTERVAL_MS);
  } catch (err) {
    cameraErrorMsg.textContent = 'Could not access your camera: ' + (err.message || err);
    cameraErrorMsg.style.display = 'block';
  }
}

function stopCamera() {
  if (cameraLoopId) {
    clearInterval(cameraLoopId);
    cameraLoopId = null;
  }
  if (cameraStream) {
    cameraStream.getTracks().forEach((track) => track.stop());
    cameraStream = null;
  }
  cameraVideo.srcObject = null;
  cameraPlaceholder.style.display = 'flex';
  cameraStartBtn.style.display = 'flex';
  cameraStopBtn.style.display = 'none';
  cameraLiveBadge.style.display = 'none';
}

async function captureAndClassifyFrame() {
  if (cameraBusy || !cameraStream) return;
  cameraBusy = true;

  try {
    cameraCanvas.width = cameraVideo.videoWidth;
    cameraCanvas.height = cameraVideo.videoHeight;
    const ctx = cameraCanvas.getContext('2d');
    ctx.drawImage(cameraVideo, 0, 0);

    const blob = await new Promise((resolve) => cameraCanvas.toBlob(resolve, 'image/jpeg', 0.85));
    if (!blob) return;

    const formData = new FormData();
    formData.append('image', blob, 'frame.jpg');
    const res = await fetch('/api/predict?include_gradcam=false', { method: 'POST', body: formData });
    if (!res.ok) return;

    const data = await res.json();
    cameraLiveLabel.textContent = data.label;
    cameraLiveConf.textContent = data.confidence + '%';
    cameraLiveBadge.style.display = 'flex';
  } catch (err) {
    // Silently skip a failed frame — the next interval tick will retry.
  } finally {
    cameraBusy = false;
  }
}

cameraStartBtn.addEventListener('click', startCamera);
cameraStopBtn.addEventListener('click', stopCamera);
window.addEventListener('beforeunload', stopCamera);

// --- Multi-item detection mode ---
const multiUploadZone = document.getElementById('multiUploadZone');
const multiFileInput = document.getElementById('multiFileInput');
const multiDetectBtn = document.getElementById('multiDetectBtn');
const multiClearBtn = document.getElementById('multiClearBtn');
const multiErrorMsg = document.getElementById('multiErrorMsg');
const multiResultSection = document.getElementById('multiResultSection');
const multiAnnotatedImg = document.getElementById('multiAnnotatedImg');
const multiItemsList = document.getElementById('multiItemsList');

multiFileInput.addEventListener('change', () => {
  if (!multiFileInput.files[0]) return;
  multiDetectBtn.disabled = false;
  multiErrorMsg.style.display = 'none';
  multiResultSection.style.display = 'none';
});

multiClearBtn.addEventListener('click', () => {
  multiFileInput.value = '';
  multiDetectBtn.disabled = true;
  multiErrorMsg.style.display = 'none';
  multiResultSection.style.display = 'none';
});

multiDetectBtn.addEventListener('click', async () => {
  const file = multiFileInput.files[0];
  if (!file) return;

  multiDetectBtn.disabled = true;
  multiDetectBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Detecting...';
  multiErrorMsg.style.display = 'none';

  try {
    const formData = new FormData();
    formData.append('image', file);
    const res = await fetch('/api/detect', { method: 'POST', body: formData });
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail || `Request failed (${res.status})`);
    }
    const data = await res.json();

    multiAnnotatedImg.src = data.annotated_image;
    multiItemsList.innerHTML = '';
    if (data.detections.length === 0) {
      multiItemsList.innerHTML = '<p class="gradcam-hint">No distinct items detected — try a photo with more contrast between items and background.</p>';
    }
    for (const det of data.detections) {
      const row = document.createElement('div');
      row.className = 'multi-item-row';
      row.innerHTML = `
        <span class="mi-label">${det.label}</span>
        <span class="badge ${det.recyclable ? 'badge-rec' : 'badge-norec'}">
          <i class="fas fa-${det.recyclable ? 'check' : 'xmark'}"></i> ${det.recyclable ? 'Recyclable' : 'Not recyclable'}
        </span>
        <span class="mi-conf">${det.confidence}%</span>
      `;
      multiItemsList.appendChild(row);
    }
    multiResultSection.style.display = 'block';
  } catch (err) {
    multiErrorMsg.textContent = err.message || 'Something went wrong.';
    multiErrorMsg.style.display = 'block';
  } finally {
    multiDetectBtn.disabled = false;
    multiDetectBtn.innerHTML = '<i class="fas fa-layer-group"></i> Detect items';
  }
});

// --- PWA: register service worker ---
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/sw.js').catch(() => {
      // Non-fatal — the app works fine without offline support.
    });
  });
}
