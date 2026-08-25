import { state } from '../state.js';
import { t, translations } from '../i18n.js';
import { renderMarkdownLite, escapeHtml } from '../ui/markdown.js';
import { sendAgentChat, streamChat } from '../api/client.js';

const chatMessages = document.getElementById('chatMessages');
const chatInput = document.getElementById('chatInput');
const chatSend = document.getElementById('chatSend');
const agentModeToggle = document.getElementById('agentModeToggle');

export function addUserMessage(text) {
  const div = document.createElement('div');
  div.className = 'chat-msg user';
  div.innerHTML = `<div class="bubble"></div>`;
  div.querySelector('.bubble').textContent = text;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

export function addAssistantMessage(text) {
  const div = document.createElement('div');
  div.className = 'chat-msg assistant';
  div.innerHTML = `<div class="bubble">${renderMarkdownLite(text)}</div>`;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return div.querySelector('.bubble');
}

function toolTraceHtml(toolsUsed) {
  if (!toolsUsed || toolsUsed.length === 0) return '';
  const names = translations[state.currentLang].toolNames || translations.en.toolNames;
  const chips = toolsUsed
    .map((tc) => `<span class="tool-chip"><i class="fas fa-wrench"></i> ${names[tc.name] || tc.name}</span>`)
    .join('');
  return `<div class="tool-trace">${chips}</div>`;
}

async function sendChatAgentMode(question, bubble) {
  const data = await sendAgentChat(question, state.lastClassificationLabel, state.chatHistory, state.currentLang);
  bubble.innerHTML = toolTraceHtml(data.tools_used) + `<span>${renderMarkdownLite(data.answer)}</span>`;

  state.chatHistory.push({ role: 'user', content: question });
  state.chatHistory.push({ role: 'assistant', content: data.answer });
}

async function sendChatStreamMode(question, bubble) {
  bubble.innerHTML = '';
  let fullText = '';
  let sawError = false;

  for await (const { type, payload } of streamChat(
    question,
    state.lastClassificationLabel,
    state.chatHistory,
    state.currentLang
  )) {
    if (type === 'token') {
      fullText += payload.text || '';
      bubble.innerHTML = renderMarkdownLite(fullText);
      chatMessages.scrollTop = chatMessages.scrollHeight;
    } else if (type === 'error') {
      sawError = true;
      const message = payload.detail || 'Something went wrong.';
      bubble.innerHTML = `<span class="chat-error-text">Error: ${escapeHtml(message)}</span>`;
    }
  }

  if (!sawError) {
    state.chatHistory.push({ role: 'user', content: question });
    state.chatHistory.push({ role: 'assistant', content: fullText });
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
