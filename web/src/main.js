import { initTheme } from './theme.js';
import { initI18n } from './i18n.js';
import { stopCamera } from './modes/camera.js';
import { registerServiceWorker } from './pwa.js';

// Side-effecting modules: importing them wires up their DOM event listeners.
import './modes/upload.js';
import './modes/multi.js';
import './chat/chat.js';
import './chat/voice.js';

initTheme();
initI18n();

// --- Mode tabs (Upload / Live Camera / Multi-Item) ---
const modeTabs = document.querySelectorAll('.mode-tab');
const modePanels = document.querySelectorAll('.mode-panel');

modeTabs.forEach((tab) => {
  tab.addEventListener('click', () => {
    const mode = tab.dataset.mode;
    modeTabs.forEach((t) => t.classList.toggle('active', t === tab));
    modePanels.forEach((p) => {
      p.style.display = p.dataset.mode === mode ? 'block' : 'none';
    });
    if (mode !== 'camera') stopCamera();
  });
});

registerServiceWorker();
