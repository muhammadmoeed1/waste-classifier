// Single shared app-state object. Modules mutate its fields in place (rather
// than reassigning `state` itself) so every importer sees live updates.

function getOrCreateSessionId() {
  // Anonymous per-browser session id, used only to group a user's own
  // scans/chat turns for /api/stats aggregates -- never tied to an account
  // or identity.
  let id = localStorage.getItem('sessionId');
  if (!id) {
    id = crypto.randomUUID();
    localStorage.setItem('sessionId', id);
  }
  return id;
}

export const state = {
  currentLang: localStorage.getItem('lang') || 'en',
  sessionId: getOrCreateSessionId(),
  lastClassificationLabel: null,
  lastScanId: null,
  chatHistory: [],
};
