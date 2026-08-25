import { state } from '../state.js';

async function ensureOk(res) {
  if (!res.ok) {
    const errBody = await res.json().catch(() => ({}));
    throw new Error(errBody.detail || `Request failed (${res.status})`);
  }
}

export async function predictImage(file, { includeGradcam = true, mode = 'upload', filename } = {}) {
  const formData = new FormData();
  if (filename) formData.append('image', file, filename);
  else formData.append('image', file);
  const params = new URLSearchParams({ include_gradcam: String(includeGradcam), mode });
  const res = await fetch(`/api/predict?${params}`, {
    method: 'POST',
    headers: { 'X-Session-Id': state.sessionId },
    body: formData,
  });
  await ensureOk(res);
  return res.json();
}

export async function detectImage(file) {
  const formData = new FormData();
  formData.append('image', file);
  const res = await fetch('/api/detect', {
    method: 'POST',
    headers: { 'X-Session-Id': state.sessionId },
    body: formData,
  });
  await ensureOk(res);
  return res.json();
}

export async function sendAgentChat(question, classificationLabel, history, language) {
  const res = await fetch('/api/agent', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Session-Id': state.sessionId },
    body: JSON.stringify({ question, classification_label: classificationLabel, history, language }),
  });
  await ensureOk(res);
  return res.json();
}

// Real SSE framing: "event: <type>\ndata: <json>\n\n". A single reader chunk
// can split a frame mid-way, so accumulate into `buffer` and only process
// complete frames (up to the next blank-line separator). Yields parsed
// {type, payload} events -- callers own all DOM rendering.
export async function* streamChat(question, classificationLabel, history, language) {
  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'X-Session-Id': state.sessionId },
    body: JSON.stringify({ question, classification_label: classificationLabel, history, language }),
  });

  if (!res.ok || !res.body) {
    const errBody = await res.json().catch(() => ({}));
    throw new Error(errBody.detail || `Request failed (${res.status})`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

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
      yield { type: eventType, payload };
    }
  }
}

export async function transcribeAudio(blob) {
  const formData = new FormData();
  formData.append('audio', blob, 'recording.webm');
  const res = await fetch('/api/transcribe', { method: 'POST', body: formData });
  await ensureOk(res);
  return res.json();
}

export async function submitFeedback(scanId, correctedLabel) {
  const res = await fetch(`/api/scans/${scanId}/feedback`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ corrected_label: correctedLabel }),
  });
  return res.ok;
}
