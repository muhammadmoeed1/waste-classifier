// --- i18n: English / Urdu ---
const translations = {
  en: {
    tagline: 'Upload a photo to identify its waste category, then ask the AI assistant<br>anything about how to recycle it.',
    tabUpload: 'Upload Photo',
    tabCamera: 'Live Camera',
    tabMulti: 'Multi-Item',
    dropTitle: 'Drop an image here',
    dropSub: 'or click to browse &mdash; JPG, PNG, WEBP',
    classifyBtn: 'Classify waste',
    clearBtn: 'Clear',
    confidence: 'Confidence',
    gradcamLabel: 'Where the model looked (Grad-CAM)',
    gradcamHint: 'Warmer colors (red/yellow) show the regions the AI focused on most to make this prediction.',
    impactLabel: 'Environmental impact',
    feedbackPrompt: 'Wrong? Tap the right category',
    feedbackThanks: 'Thanks — feedback recorded.',
    cameraOff: 'Camera is off',
    cameraStart: 'Start camera',
    cameraStop: 'Stop',
    cameraHint: 'Classifies automatically about every 2 seconds while the camera is on (heatmap/impact are skipped here for speed &mdash; use Upload Photo for the full analysis).',
    multiDropTitle: 'Drop a photo with multiple items',
    multiDropSub: 'e.g. several items laid out on a table &mdash; JPG, PNG, WEBP',
    detectBtn: 'Detect items',
    catsLabel: 'Detectable categories',
    cat_cardboard: 'Cardboard',
    cat_glass: 'Glass',
    cat_metal: 'Metal',
    cat_paper: 'Paper',
    cat_plastic: 'Plastic',
    cat_trash: 'Trash',
    chatTitle: 'Recycling Assistant',
    chatSub: 'Powered by Groq &middot; ask about recycling rules, contamination, or your uploaded item',
    chatWelcome: 'Hi! Upload an image or just ask me a recycling question &mdash; e.g. "Can I recycle a greasy pizza box?"',
    chatPlaceholder: 'Ask about recycling...',
    agentModeLabel: '🤖 Agent',
    toolNames: {
      lookup_recycling_guide: 'looked up recycling guide',
      estimate_environmental_impact: 'calculated CO2 impact',
      check_recyclability: 'checked recyclability',
    },
    recyclable: 'Recyclable',
    notRecyclable: 'Not recyclable',
    noItemsDetected: 'No distinct items detected — try a photo with more contrast between items and background.',
    uncertainPrefix: 'Not fully sure — this might also be',
    uncertainSuffix: '. Try a clearer or closer photo for a more confident result.',
    uncertainTag: '(uncertain)',
    classifiedMsg: (label, conf) =>
      `I classified this as **${label}** (${conf}% confidence). Ask me anything about how to recycle it!`,
  },
  ur: {
    tagline: 'تصویر اپ لوڈ کریں تاکہ اس کی کچرے کی قسم معلوم ہو، پھر AI اسسٹنٹ سے<br>ری سائیکلنگ کے بارے میں کچھ بھی پوچھیں۔',
    tabUpload: 'تصویر اپ لوڈ کریں',
    tabCamera: 'لائیو کیمرہ',
    tabMulti: 'متعدد اشیاء',
    dropTitle: 'یہاں تصویر ڈراپ کریں',
    dropSub: 'یا منتخب کرنے کے لیے کلک کریں — JPG, PNG, WEBP',
    classifyBtn: 'کچرے کی شناخت کریں',
    clearBtn: 'صاف کریں',
    confidence: 'اعتماد',
    gradcamLabel: 'ماڈل نے کہاں دیکھا (Grad-CAM)',
    gradcamHint: 'زیادہ گرم رنگ (سرخ/پیلا) ان حصوں کو ظاہر کرتے ہیں جن پر AI نے سب سے زیادہ توجہ دی۔',
    impactLabel: 'ماحولیاتی اثر',
    feedbackPrompt: 'غلط ہے؟ درست قسم پر ٹیپ کریں',
    feedbackThanks: 'شکریہ — رائے محفوظ کر لی گئی۔',
    cameraOff: 'کیمرہ بند ہے',
    cameraStart: 'کیمرہ شروع کریں',
    cameraStop: 'روکیں',
    cameraHint: 'کیمرہ آن ہونے پر ہر تقریباً 2 سیکنڈ بعد خودکار شناخت ہوتی ہے (رفتار کے لیے ہیٹ میپ/اثر یہاں شامل نہیں — مکمل تجزیے کے لیے "تصویر اپ لوڈ کریں" استعمال کریں)۔',
    multiDropTitle: 'متعدد اشیاء والی تصویر ڈراپ کریں',
    multiDropSub: 'مثلاً میز پر رکھی گئی کئی اشیاء — JPG, PNG, WEBP',
    detectBtn: 'اشیاء کی شناخت کریں',
    catsLabel: 'قابلِ شناخت اقسام',
    cat_cardboard: 'کارڈ بورڈ',
    cat_glass: 'شیشہ',
    cat_metal: 'دھات',
    cat_paper: 'کاغذ',
    cat_plastic: 'پلاسٹک',
    cat_trash: 'کچرا',
    chatTitle: 'ری سائیکلنگ اسسٹنٹ',
    chatSub: 'Groq کی طاقت سے · ری سائیکلنگ کے اصولوں، آلودگی، یا اپ لوڈ کردہ چیز کے بارے میں پوچھیں',
    chatWelcome: 'السلام علیکم! تصویر اپ لوڈ کریں یا مجھ سے کوئی سوال پوچھیں — مثلاً "کیا میں تیل والا پیزا باکس ری سائیکل کر سکتا ہوں؟"',
    chatPlaceholder: 'ری سائیکلنگ کے بارے میں پوچھیں...',
    agentModeLabel: '🤖 ایجنٹ',
    toolNames: {
      lookup_recycling_guide: 'ری سائیکلنگ گائیڈ دیکھی',
      estimate_environmental_impact: 'CO2 اثر شمار کیا',
      check_recyclability: 'ری سائیکل ایبلٹی چیک کی',
    },
    recyclable: 'قابلِ ری سائیکل',
    notRecyclable: 'ناقابلِ ری سائیکل',
    noItemsDetected: 'کوئی الگ چیز نہیں ملی — پس منظر اور اشیاء کے درمیان زیادہ فرق والی تصویر آزمائیں۔',
    uncertainPrefix: 'پورا یقین نہیں — یہ',
    uncertainSuffix: 'بھی ہو سکتا ہے۔ زیادہ واضح یا قریبی تصویر آزمائیں۔',
    uncertainTag: '(غیر یقینی)',
    classifiedMsg: (label, conf) =>
      `میں نے اسے **${label}** کے طور پر شناخت کیا (${conf}% اعتماد)۔ اسے ری سائیکل کرنے کے بارے میں کچھ بھی پوچھیں!`,
  },
};

let currentLang = localStorage.getItem('lang') || 'en';

// Anonymous per-browser session id, used only to group a user's own scans/chat
// turns for /api/stats aggregates -- never tied to an account or identity.
let sessionId = localStorage.getItem('sessionId');
if (!sessionId) {
  sessionId = crypto.randomUUID();
  localStorage.setItem('sessionId', sessionId);
}

function t(key) {
  return (translations[currentLang] && translations[currentLang][key]) || translations.en[key] || key;
}

function catLabel(key) {
  return t('cat_' + key);
}

function applyLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('lang', lang);
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === 'ur' ? 'rtl' : 'ltr';
  document.body.classList.toggle('lang-ur', lang === 'ur');

  document.querySelectorAll('[data-i18n]').forEach((el) => {
    el.innerHTML = t(el.dataset.i18n);
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
    el.placeholder = t(el.dataset.i18nPlaceholder);
  });

  const langToggle = document.getElementById('langToggle');
  if (langToggle) langToggle.textContent = lang === 'en' ? 'اردو' : 'English';
}

document.getElementById('langToggle').addEventListener('click', () => {
  applyLanguage(currentLang === 'en' ? 'ur' : 'en');
});

// --- Dark mode toggle ---
const themeToggle = document.getElementById('themeToggle');

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  localStorage.setItem('theme', theme);
  themeToggle.innerHTML = theme === 'dark' ? '<i class="fas fa-sun"></i>' : '<i class="fas fa-moon"></i>';
}

themeToggle.addEventListener('click', () => {
  const current = document.documentElement.getAttribute('data-theme') || 'light';
  applyTheme(current === 'dark' ? 'light' : 'dark');
});

(function initPreferences() {
  const savedTheme =
    localStorage.getItem('theme') ||
    (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  applyTheme(savedTheme);
  applyLanguage(currentLang);
})();

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
const uncertaintyWarning = document.getElementById('uncertaintyWarning');
const uncertaintyText = document.getElementById('uncertaintyText');
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
const feedbackGrid = document.getElementById('feedbackGrid');
const feedbackConfirm = document.getElementById('feedbackConfirm');

const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const chatSend = document.getElementById('chatSend');
const micBtn = document.getElementById('micBtn');
const agentModeToggle = document.getElementById('agentModeToggle');

let lastClassificationLabel = null;
let lastScanId = null;
let chatHistory = [];

function resetFeedbackUI() {
  feedbackConfirm.style.display = 'none';
  feedbackGrid.querySelectorAll('.feedback-pill').forEach((el) => el.classList.remove('submitted'));
}

feedbackGrid.addEventListener('click', async (e) => {
  const pill = e.target.closest('.feedback-pill');
  if (!pill || lastScanId == null) return;

  const correctedLabel = pill.dataset.cat;
  try {
    const res = await fetch(`/api/scans/${lastScanId}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ corrected_label: correctedLabel }),
    });
    if (!res.ok) return;

    feedbackGrid.querySelectorAll('.feedback-pill').forEach((el) => el.classList.remove('submitted'));
    pill.classList.add('submitted');
    feedbackConfirm.style.display = 'flex';
  } catch {
    // Best-effort: feedback is a nice-to-have, not worth surfacing an error for.
  }
});

// Reusable drag-and-drop visual feedback + drop handling for an upload zone.
function setupDragAndDrop(zoneEl, inputEl) {
  ['dragenter', 'dragover'].forEach((evt) => {
    zoneEl.addEventListener(evt, (e) => {
      e.preventDefault();
      zoneEl.classList.add('drag-over');
    });
  });

  ['dragleave', 'dragend'].forEach((evt) => {
    zoneEl.addEventListener(evt, (e) => {
      e.preventDefault();
      zoneEl.classList.remove('drag-over');
    });
  });

  zoneEl.addEventListener('drop', (e) => {
    e.preventDefault();
    zoneEl.classList.remove('drag-over');
    const dropped = e.dataTransfer.files;
    if (dropped && dropped.length > 0) {
      inputEl.files = dropped;
      inputEl.dispatchEvent(new Event('change'));
    }
  });
}

setupDragAndDrop(uploadZone, fileInput);

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
  lastScanId = null;
  resetFeedbackUI();
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
    const res = await fetch('/api/predict', {
      method: 'POST',
      headers: { 'X-Session-Id': sessionId },
      body: formData,
    });
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

const UNCERTAINTY_THRESHOLD = 60;

function showResult(data) {
  lastClassificationLabel = data.label;
  lastScanId = data.scan_id ?? null;
  resetFeedbackUI();

  resultLabel.textContent = catLabel(data.label);
  resultBadge.className = 'badge ' + (data.recyclable ? 'badge-rec' : 'badge-norec');
  resultBadge.innerHTML = data.recyclable
    ? `<i class="fas fa-check"></i> ${t('recyclable')}`
    : `<i class="fas fa-xmark"></i> ${t('notRecyclable')}`;

  confVal.textContent = data.confidence + '%';
  confBar.style.width = '0%';
  setTimeout(() => { confBar.style.width = data.confidence + '%'; }, 50);

  probsList.innerHTML = '';
  const sorted = Object.entries(data.probabilities).sort((a, b) => b[1] - a[1]);
  for (const [name, pct] of sorted) {
    const row = document.createElement('div');
    row.className = 'prob-row';
    row.innerHTML = `
      <span class="prob-name">${catLabel(name)}</span>
      <span class="prob-bar-bg"><span class="prob-bar-fill" style="width:${pct}%"></span></span>
      <span class="prob-pct">${pct}%</span>
    `;
    probsList.appendChild(row);
  }

  if (data.confidence < UNCERTAINTY_THRESHOLD && sorted.length > 1) {
    const runnerUp = sorted[1][0];
    uncertaintyText.textContent = `${t('uncertainPrefix')} ${catLabel(runnerUp)}${t('uncertainSuffix')}`;
    uncertaintyWarning.style.display = 'flex';
  } else {
    uncertaintyWarning.style.display = 'none';
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

  addAssistantMessage(t('classifiedMsg')(catLabel(data.label), data.confidence));
}

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// Minimal, safe markdown: escapes HTML first (so LLM output can never inject
// tags), then converts **bold** markers to real <strong> tags.
function renderMarkdownLite(text) {
  return escapeHtml(text).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
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
  div.innerHTML = `<div class="bubble">${renderMarkdownLite(text)}</div>`;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return div.querySelector('.bubble');
}

function toolTraceHtml(toolsUsed) {
  if (!toolsUsed || toolsUsed.length === 0) return '';
  const names = translations[currentLang].toolNames || translations.en.toolNames;
  const chips = toolsUsed
    .map((tc) => `<span class="tool-chip"><i class="fas fa-wrench"></i> ${names[tc.name] || tc.name}</span>`)
    .join('');
  return `<div class="tool-trace">${chips}</div>`;
}

async function sendChatAgentMode(question, bubble) {
  const res = await fetch('/api/agent', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Session-Id': sessionId },
    body: JSON.stringify({
      question,
      classification_label: lastClassificationLabel,
      history: chatHistory,
      language: currentLang,
    }),
  });

  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    throw new Error(errBody.detail || `Request failed (${res.status})`);
  }

  const data = await res.json();
  bubble.innerHTML = toolTraceHtml(data.tools_used) + `<span>${renderMarkdownLite(data.answer)}</span>`;

  chatHistory.push({ role: 'user', content: question });
  chatHistory.push({ role: 'assistant', content: data.answer });
}

async function sendChatStreamMode(question, bubble) {
  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Session-Id': sessionId },
    body: JSON.stringify({
      question,
      classification_label: lastClassificationLabel,
      history: chatHistory,
      language: currentLang,
    }),
  });

  if (!res.ok || !res.body) {
    const errBody = await res.json().catch(() => ({}));
    throw new Error(errBody.detail || `Request failed (${res.status})`);
  }

  bubble.innerHTML = '';
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let fullText = '';
  let buffer = '';
  let sawError = false;

  // Real SSE framing: "event: <type>\ndata: <json>\n\n". A single reader
  // chunk can split a frame mid-way, so accumulate into `buffer` and only
  // process complete frames (up to the next blank-line separator).
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    let boundary;
    while ((boundary = buffer.indexOf('\n\n')) !== -1) {
      const rawFrame = buffer.slice(0, boundary);
      buffer = buffer.slice(boundary + 2);

      let eventType = 'message';
      let dataLine = '';
      for (const line of rawFrame.split('\n')) {
        if (line.startsWith('event:')) eventType = line.slice(6).trim();
        else if (line.startsWith('data:')) dataLine = line.slice(5).trim();
      }
      if (!dataLine) continue;

      let payload;
      try {
        payload = JSON.parse(dataLine);
      } catch {
        continue;
      }

      if (eventType === 'token') {
        fullText += payload.text || '';
        bubble.innerHTML = renderMarkdownLite(fullText);
        chatMessages.scrollTop = chatMessages.scrollHeight;
      } else if (eventType === 'error') {
        sawError = true;
        const message = payload.detail || 'Something went wrong.';
        bubble.innerHTML = `<span class="chat-error-text">Error: ${escapeHtml(message)}</span>`;
      }
    }
  }

  if (!sawError) {
    chatHistory.push({ role: 'user', content: question });
    chatHistory.push({ role: 'assistant', content: fullText });
  }
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
    if (agentModeToggle.checked) {
      await sendChatAgentMode(question, bubble);
    } else {
      await sendChatStreamMode(question, bubble);
    }
    chatMessages.scrollTop = chatMessages.scrollHeight;
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
    const res = await fetch('/api/predict?include_gradcam=false&mode=camera', {
      method: 'POST',
      headers: { 'X-Session-Id': sessionId },
      body: formData,
    });
    if (!res.ok) return;

    const data = await res.json();
    const uncertain = data.confidence < UNCERTAINTY_THRESHOLD;
    cameraLiveLabel.textContent = catLabel(data.label) + (uncertain ? ` ${t('uncertainTag')}` : '');
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
const multiPreviewWrap = document.getElementById('multiPreviewWrap');
const multiPreviewImg = document.getElementById('multiPreviewImg');
const multiFname = document.getElementById('multiFname');
const multiFnameText = document.getElementById('multiFnameText');
const multiDetectBtn = document.getElementById('multiDetectBtn');
const multiClearBtn = document.getElementById('multiClearBtn');
const multiErrorMsg = document.getElementById('multiErrorMsg');
const multiResultSection = document.getElementById('multiResultSection');
const multiAnnotatedImg = document.getElementById('multiAnnotatedImg');
const multiItemsList = document.getElementById('multiItemsList');

setupDragAndDrop(multiUploadZone, multiFileInput);

multiFileInput.addEventListener('change', () => {
  const file = multiFileInput.files[0];
  if (!file) return;
  multiPreviewImg.src = URL.createObjectURL(file);
  multiPreviewWrap.style.display = 'block';
  multiFname.style.display = 'block';
  multiFnameText.textContent = ' ' + file.name;
  multiDetectBtn.disabled = false;
  multiErrorMsg.style.display = 'none';
  multiResultSection.style.display = 'none';
});

multiClearBtn.addEventListener('click', () => {
  multiFileInput.value = '';
  multiPreviewImg.src = '';
  multiPreviewWrap.style.display = 'none';
  multiFname.style.display = 'none';
  multiFnameText.textContent = '';
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
    const res = await fetch('/api/detect', {
      method: 'POST',
      headers: { 'X-Session-Id': sessionId },
      body: formData,
    });
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.detail || `Request failed (${res.status})`);
    }
    const data = await res.json();

    multiAnnotatedImg.src = data.annotated_image;
    multiItemsList.innerHTML = '';
    if (data.detections.length === 0) {
      multiItemsList.innerHTML = `<p class="gradcam-hint">${t('noItemsDetected')}</p>`;
    }
    for (const det of data.detections) {
      const row = document.createElement('div');
      row.className = 'multi-item-row';
      const uncertain = det.confidence < UNCERTAINTY_THRESHOLD;
      row.innerHTML = `
        <span class="mi-label">${catLabel(det.label)}${uncertain ? ` <span class="mi-uncertain">${t('uncertainTag')}</span>` : ''}</span>
        <span class="badge ${det.recyclable ? 'badge-rec' : 'badge-norec'}">
          <i class="fas fa-${det.recyclable ? 'check' : 'xmark'}"></i> ${det.recyclable ? t('recyclable') : t('notRecyclable')}
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
    navigator.serviceWorker
      .register('/sw.js')
      .then((registration) => {
        // Force an immediate check for a new sw.js on every load, instead of
        // waiting for the browser's normal (up to 24h) update-check throttle
        // — this app iterates fast enough during development/demo use that
        // stale-cache surprises are worse than the extra network request.
        registration.update();
      })
      .catch(() => {
        // Non-fatal — the app works fine without offline support.
      });
  });
}
