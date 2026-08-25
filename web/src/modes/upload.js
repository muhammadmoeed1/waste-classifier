import { state } from '../state.js';
import { t, catLabel } from '../i18n.js';
import { predictImage, submitFeedback } from '../api/client.js';
import { addAssistantMessage } from '../chat/chat.js';
import { setupDragAndDrop } from '../ui/dragdrop.js';
import { UNCERTAINTY_THRESHOLD } from '../constants.js';

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
// Scoped to the read-only category legend only -- the feedback grid below
// reuses the same .cat-item class for its buttons and must not be matched
// here, or a correction toggles the legend's "active" highlight too.
const catItems = document.querySelectorAll('#catsGrid .cat-item');
const gradcamSection = document.getElementById('gradcamSection');
const gradcamImg = document.getElementById('gradcamImg');
const impactSection = document.getElementById('impactSection');
const impactHeadline = document.getElementById('impactHeadline');
const impactStats = document.getElementById('impactStats');
const impactFact = document.getElementById('impactFact');
const feedbackGrid = document.getElementById('feedbackGrid');
const feedbackConfirm = document.getElementById('feedbackConfirm');

function resetFeedbackUI() {
  feedbackConfirm.style.display = 'none';
  feedbackGrid.querySelectorAll('.feedback-pill').forEach((el) => el.classList.remove('submitted'));
}

feedbackGrid.addEventListener('click', async (e) => {
  const pill = e.target.closest('.feedback-pill');
  if (!pill || state.lastScanId == null) return;

  const correctedLabel = pill.dataset.cat;
  try {
    const ok = await submitFeedback(state.lastScanId, correctedLabel);
    if (!ok) return;

    feedbackGrid.querySelectorAll('.feedback-pill').forEach((el) => el.classList.remove('submitted'));
    pill.classList.add('submitted');
    feedbackConfirm.style.display = 'flex';
  } catch {
    // Best-effort: feedback is a nice-to-have, not worth surfacing an error for.
  }
});

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
  catItems.forEach((el) => el.classList.remove('active'));
  state.lastClassificationLabel = null;
  state.lastScanId = null;
  resetFeedbackUI();
});

classifyBtn.addEventListener('click', async () => {
  const file = fileInput.files[0];
  if (!file) return;

  classifyBtn.disabled = true;
  classifyBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Classifying...';
  hideError();

  try {
    const data = await predictImage(file, { includeGradcam: true, mode: 'upload' });
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
  state.lastClassificationLabel = data.label;
  state.lastScanId = data.scan_id ?? null;
  resetFeedbackUI();

  resultLabel.textContent = catLabel(data.label);
  resultBadge.className = 'badge ' + (data.recyclable ? 'badge-rec' : 'badge-norec');
  resultBadge.innerHTML = data.recyclable
    ? `<i class="fas fa-check"></i> ${t('recyclable')}`
    : `<i class="fas fa-xmark"></i> ${t('notRecyclable')}`;

  confVal.textContent = data.confidence + '%';
  confBar.style.width = '0%';
  setTimeout(() => {
    confBar.style.width = data.confidence + '%';
  }, 50);

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

  catItems.forEach((el) => el.classList.toggle('active', el.dataset.cat === data.label));
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
