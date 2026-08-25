// Chart.js is loaded globally via a classic <script> tag in dashboard.html
// (before this module script), so `Chart` is available as a global here.
/* global Chart */

function cssVar(name) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim();
}

function hexToRgba(hex, alpha) {
  const clean = hex.replace('#', '');
  const bigint = parseInt(clean, 16);
  const r = (bigint >> 16) & 255;
  const g = (bigint >> 8) & 255;
  const b = bigint & 255;
  return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

const CATEGORY_ORDER = ['cardboard', 'glass', 'metal', 'paper', 'plastic', 'trash'];

function categoryColor(name) {
  return cssVar(`--cat-${name}`) || cssVar('--accent');
}

function themeColors() {
  return {
    muted: cssVar('--muted'),
    grid: cssVar('--border'),
    fg: cssVar('--fg'),
  };
}

export function renderClassDistributionChart(canvas, classDistribution, trainingDistributionPct) {
  const totalScans = Object.values(classDistribution).reduce((a, b) => a + b, 0);
  const livePct = CATEGORY_ORDER.map((c) =>
    totalScans ? Math.round(((classDistribution[c] || 0) / totalScans) * 1000) / 10 : 0
  );
  const refPct = CATEGORY_ORDER.map((c) => trainingDistributionPct[c] || 0);
  const { muted, grid } = themeColors();

  return new Chart(canvas, {
    type: 'bar',
    data: {
      labels: CATEGORY_ORDER.map((c) => c[0].toUpperCase() + c.slice(1)),
      datasets: [
        {
          label: 'Live traffic %',
          data: livePct,
          backgroundColor: CATEGORY_ORDER.map((c) => categoryColor(c)),
        },
        {
          label: 'TrashNet validation set %',
          data: refPct,
          backgroundColor: CATEGORY_ORDER.map((c) => hexToRgba(categoryColor(c), 0.3)),
        },
      ],
    },
    options: {
      scales: {
        x: { ticks: { color: muted }, grid: { color: grid } },
        y: { beginAtZero: true, ticks: { color: muted }, grid: { color: grid } },
      },
      plugins: { legend: { labels: { color: muted } } },
    },
  });
}

export function renderConfidenceChart(canvas, histogram) {
  const labels = histogram.map((_, i) => `${i * 10}-${i * 10 + 10}%`);
  const { muted, grid } = themeColors();
  const accent = cssVar('--accent');

  return new Chart(canvas, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Scans',
          data: histogram,
          // Below the 60% uncertainty threshold (buckets 0-5) shown muted;
          // at/above it (buckets 6-9) shown in the accent color.
          backgroundColor: histogram.map((_, i) => (i < 6 ? hexToRgba(muted, 0.5) : accent)),
        },
      ],
    },
    options: {
      scales: {
        x: { ticks: { color: muted }, grid: { color: grid } },
        y: { beginAtZero: true, ticks: { color: muted, precision: 0 }, grid: { color: grid } },
      },
      plugins: { legend: { display: false } },
    },
  });
}

export function renderLatencyChart(canvas, latencyPoints) {
  const chronological = [...latencyPoints].reverse(); // API returns newest-first
  const modeColors = { upload: cssVar('--accent'), camera: categoryColor('glass'), multi: categoryColor('cardboard') };
  const { muted, grid } = themeColors();

  const datasets = Object.keys(modeColors).map((mode) => ({
    label: mode,
    data: chronological
      .map((p, i) => ({ x: i, y: p.latency_ms, mode: p.mode }))
      .filter((p) => p.mode === mode)
      .map(({ x, y }) => ({ x, y })),
    backgroundColor: modeColors[mode],
    showLine: false,
  }));

  return new Chart(canvas, {
    type: 'scatter',
    data: { datasets },
    options: {
      scales: {
        x: {
          title: { display: true, text: 'Scan # (chronological, most recent 200)', color: muted },
          ticks: { color: muted },
          grid: { color: grid },
        },
        y: {
          title: { display: true, text: 'Latency (ms)', color: muted },
          ticks: { color: muted },
          grid: { color: grid },
        },
      },
      plugins: { legend: { labels: { color: muted } } },
    },
  });
}

export function renderToolUsageChart(canvas, toolUsage) {
  const entries = Object.entries(toolUsage).sort((a, b) => b[1] - a[1]);
  const { muted, grid } = themeColors();

  return new Chart(canvas, {
    type: 'bar',
    data: {
      labels: entries.map(([name]) => name.replace(/_/g, ' ')),
      datasets: [
        {
          label: 'Calls',
          data: entries.map(([, count]) => count),
          backgroundColor: cssVar('--accent'),
        },
      ],
    },
    options: {
      indexAxis: 'y',
      scales: {
        x: { beginAtZero: true, ticks: { color: muted, precision: 0 }, grid: { color: grid } },
        y: { ticks: { color: muted }, grid: { color: grid } },
      },
      plugins: { legend: { display: false } },
    },
  });
}

export function renderConfusionTable(container, confusionMatrix) {
  if (!confusionMatrix.length) {
    container.innerHTML = '<p class="confusion-empty">No corrections submitted yet — the "Wrong? Tap the right category" control on a result feeds this table.</p>';
    return;
  }
  const sorted = [...confusionMatrix].sort((a, b) => b.count - a.count);
  const rows = sorted
    .map(
      (c) => `
      <tr>
        <td>${c.predicted}</td>
        <td>${c.corrected}</td>
        <td class="conf-count">${c.count}</td>
      </tr>`
    )
    .join('');
  container.innerHTML = `
    <table class="confusion-table">
      <thead><tr><th>Model predicted</th><th>User corrected to</th><th>Times</th></tr></thead>
      <tbody>${rows}</tbody>
    </table>
  `;
}
