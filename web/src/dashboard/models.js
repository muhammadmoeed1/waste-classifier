import { initTheme } from '../theme.js';

initTheme();

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

function renderDrift(drift) {
  const card = document.getElementById('driftCard');
  if (drift.baseline_accuracy == null || drift.rolling_7day_mean_confidence == null) {
    card.innerHTML = `
      <div class="drift-status ok"><i class="fas fa-circle-info"></i> Not enough data yet to check for drift (need scans from the last 7 days).</div>
    `;
    return;
  }

  const baselinePct = (drift.baseline_accuracy * 100).toFixed(1);
  const rollingPct = (drift.rolling_7day_mean_confidence * 100).toFixed(1);

  if (drift.is_drifting) {
    card.innerHTML = `
      <div class="drift-status warn"><i class="fas fa-triangle-exclamation"></i> Possible drift: last-7-day confidence is meaningfully below baseline.</div>
      <div class="drift-detail">Training-time validation accuracy: ${baselinePct}% &nbsp;&middot;&nbsp; Rolling 7-day mean confidence: ${rollingPct}%</div>
    `;
  } else {
    card.innerHTML = `
      <div class="drift-status ok"><i class="fas fa-circle-check"></i> No drift detected.</div>
      <div class="drift-detail">Training-time validation accuracy: ${baselinePct}% &nbsp;&middot;&nbsp; Rolling 7-day mean confidence: ${rollingPct}%</div>
    `;
  }
}

function renderVersionsTable(versions) {
  const classNames = ['cardboard', 'glass', 'metal', 'paper', 'plastic', 'trash'];
  const wrap = document.getElementById('modelsTableWrap');

  const header = `<th>Version</th>${classNames.map((c) => `<th>${c}</th>`).join('')}<th>Overall acc.</th><th>Corrections used</th>`;
  const rows = versions
    .map((v) => {
      const cells = classNames
        .map((c) => `<td class="num-cell">${v.per_class_f1[c] != null ? v.per_class_f1[c].toFixed(3) : '&mdash;'}</td>`)
        .join('');
      const activeBadge = v.is_active ? '<span class="version-badge">active</span>' : '';
      const overall = v.overall_accuracy != null ? `${(v.overall_accuracy * 100).toFixed(2)}%` : '&mdash;';
      const corrections = v.num_correction_examples != null ? v.num_correction_examples : '&mdash;';
      return `<tr><td>${escapeHtml(v.version)}${activeBadge}</td>${cells}<td class="num-cell">${overall}</td><td class="num-cell">${corrections}</td></tr>`;
    })
    .join('');

  wrap.innerHTML = `<table class="data-table"><thead><tr>${header}</tr></thead><tbody>${rows}</tbody></table>`;
}

async function init() {
  let data;
  try {
    const res = await fetch('/api/models');
    if (!res.ok) throw new Error(`Request failed (${res.status})`);
    data = await res.json();
  } catch {
    document.getElementById('driftCard').innerHTML =
      '<div class="drift-status warn"><i class="fas fa-triangle-exclamation"></i> Could not load model data. Try refreshing.</div>';
    return;
  }

  renderDrift(data.drift);
  renderVersionsTable(data.versions);
}

init();
