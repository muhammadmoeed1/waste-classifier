import { addAssistantMessage } from './chat.js';
import { transcribeAudio } from '../api/client.js';

const micBtn = document.getElementById('micBtn');
const chatInput = document.getElementById('chatInput');

let mediaRecorder = null;
let audioChunks = [];
let isRecording = false;

async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };
    mediaRecorder.onstop = async () => {
      stream.getTracks().forEach((track) => track.stop());
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
    const data = await transcribeAudio(blob);
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
