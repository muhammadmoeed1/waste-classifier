import { initTheme } from '../theme.js';

initTheme();

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function reasonChipsHtml(reason) {
  return reason
    .split('+')
    .map((r) => {
      const label = r === 'low_confidence' ? 'Low confidence' : 'Corrected';
      const cls = r === 'corrected' ? 'reason-chip corrected' : 'reason-chip';
      return `<span class="${cls}">${label}</span>`;
    })
    .join(' ');
}

async function init() {
  const reviewEmpty = document.getElementById('reviewEmpty');
  const reviewTableCard = document.getElementById('reviewTableCard');
  const wrap = document.getElementById('reviewTableWrap');

  let data;
  try {
    const res = await fetch('/api/scans/review');
    if (!res.ok) throw new Error(`Request failed (${res.status})`);
    data = await res.json();
  } catch {
    reviewEmpty.innerHTML = '<i class="fas fa-triangle-exclamation"></i><p>Could not load the review queue. Try refreshing.</p>';
    reviewEmpty.style.display = 'flex';
    return;
  }

  if (data.scans.length === 0) {
    reviewEmpty.style.display = 'flex';
    return;
  }

  reviewTableCard.style.display = 'block';
  const rows = data.scans
    .map(
      (s) => `
      <tr>
        <td>${new Date(s.created_at).toLocaleString()}</td>
        <td>${escapeHtml(s.mode)}</td>
        <td>${escapeHtml(s.predicted_label)}</td>
        <td class="num-cell">${s.confidence.toFixed(1)}%</td>
        <td>${s.feedback_label ? escapeHtml(s.feedback_label) : '&mdash;'}</td>
        <td>${reasonChipsHtml(s.reason)}</td>
      </tr>`
    )
    .join('');

  wrap.innerHTML = `
    <table class="data-table">
      <thead>
        <tr><th>When</th><th>Mode</th><th>Predicted</th><th>Confidence</th><th>Corrected to</th><th>Reason</th></tr>
      </thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}

init();
