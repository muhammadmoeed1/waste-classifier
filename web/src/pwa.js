export function registerServiceWorker() {
  if (!('serviceWorker' in navigator)) return;

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
