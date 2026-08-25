const CACHE_NAME = 'waste-classifier-v5';
const APP_SHELL = [
  '/',
  '/index.html',
  '/style.css',
  '/manifest.json',
  '/favicon.svg',
  '/icons/icon-192.png',
  '/icons/icon-512.png',
  '/vendor/fontawesome/css/fontawesome.min.css',
  '/vendor/fontawesome/css/solid.min.css',
  '/vendor/fontawesome/webfonts/fa-solid-900.woff2',
  '/vendor/fonts/noto-nastaliq-urdu.css',
  '/vendor/fonts/noto-nastaliq-urdu.woff2',
  '/src/main.js',
  '/src/state.js',
  '/src/constants.js',
  '/src/i18n.js',
  '/src/theme.js',
  '/src/pwa.js',
  '/src/api/client.js',
  '/src/ui/markdown.js',
  '/src/ui/dragdrop.js',
  '/src/modes/upload.js',
  '/src/modes/camera.js',
  '/src/modes/multi.js',
  '/src/chat/chat.js',
  '/src/chat/voice.js',
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL))
  );
  self.skipWaiting();
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

// Network-first for the app shell, falling back to cache only when offline —
// this way every deploy is picked up immediately instead of being masked by a
// stale cached copy of index.html/app.js/style.css. Never touch API calls,
// since predictions/chat/transcription must always hit the live backend.
self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);
  if (url.pathname.startsWith('/api/')) return;
  if (event.request.method !== 'GET') return;

  event.respondWith(
    fetch(event.request)
      .then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
