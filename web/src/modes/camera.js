import { t, catLabel } from '../i18n.js';
import { predictImage } from '../api/client.js';
import { UNCERTAINTY_THRESHOLD, CAMERA_INTERVAL_MS } from '../constants.js';

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
    cameraErrorMsg.innerHTML = cameraErrorHtml(err);
    cameraErrorMsg.style.display = 'block';
  }
}

function cameraErrorHtml(err) {
  if (err && err.name === 'NotAllowedError') {
    return (
      'Camera access was denied, so live classification can\'t run. This app needs it to classify what the camera sees in real time -- ' +
      'it never uploads or stores video, only single frames sent for classification. To re-enable it, look for a camera icon in your ' +
      'browser\'s address bar (or Settings &rarr; Site settings &rarr; Camera) and allow access for this site, then tap "Start camera" again.'
    );
  }
  if (err && err.name === 'NotFoundError') {
    return 'No camera was found on this device. Try Upload Photo instead.';
  }
  return 'Could not access your camera: ' + ((err && err.message) || err);
}

export function stopCamera() {
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

    const data = await predictImage(blob, { includeGradcam: false, mode: 'camera', filename: 'frame.jpg' });
    const uncertain = data.confidence < UNCERTAINTY_THRESHOLD;
    cameraLiveLabel.textContent = catLabel(data.label) + (uncertain ? ` ${t('uncertainTag')}` : '');
    cameraLiveConf.textContent = data.confidence + '%';
    cameraLiveBadge.style.display = 'flex';
  } catch {
    // Silently skip a failed frame — the next interval tick will retry.
  } finally {
    cameraBusy = false;
  }
}

cameraStartBtn.addEventListener('click', startCamera);
cameraStopBtn.addEventListener('click', stopCamera);
window.addEventListener('beforeunload', stopCamera);
