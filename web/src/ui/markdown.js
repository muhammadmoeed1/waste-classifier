export function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// Minimal, safe markdown: escapes HTML first (so LLM output can never inject
// tags), then converts **bold** markers to real <strong> tags.
export function renderMarkdownLite(text) {
  return escapeHtml(text).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
}
