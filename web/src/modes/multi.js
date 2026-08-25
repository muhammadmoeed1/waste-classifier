import { t, catLabel } from '../i18n.js';
import { detectImage } from '../api/client.js';
import { setupDragAndDrop } from '../ui/dragdrop.js';
import { UNCERTAINTY_THRESHOLD } from '../constants.js';

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
    const data = await detectImage(file);

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
