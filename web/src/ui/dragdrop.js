// Reusable drag-and-drop visual feedback + drop handling for an upload zone.
export function setupDragAndDrop(zoneEl, inputEl) {
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
