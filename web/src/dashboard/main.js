import { initTheme } from '../theme.js';
import { fetchStats } from './stats.js';
import {
  renderClassDistributionChart,
  renderConfidenceChart,
  renderLatencyChart,
  renderToolUsageChart,
  renderConfusionTable,
} from './charts.js';

initTheme();

// Animates a hero stat from 0 to its final value over ~600ms.
function countUp(el, target, { decimals = 0, suffix = '' } = {}) {
  const duration = 600;
  const start = performance.now();

  function frame(now) {
    const progress = Math.min((now - start) / duration, 1);
    // cubic-bezier-ish ease-out
    const eased = 1 - (1 - progress) ** 3;
    const value = target * eased;
    el.textContent = value.toFixed(decimals) + suffix;
    if (progress < 1) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

let activeCharts = [];
let latestStats = null;

// Chart.js reads colors from CSS custom properties once, at creation time --
// toggling the theme doesn't repaint an existing chart. Rather than leave
// stale (and on some browsers, visually collapsed -- a ResizeObserver quirk
// when a chart's container reflows without a real size change) charts on
// screen, destroy and fully re-render them with the new theme's colors.
function renderAllCharts(stats) {
  activeCharts.forEach((c) => c.destroy());
  activeCharts = [];

  activeCharts.push(
    renderClassDistributionChart(
      document.getElementById('classDistChart'),
      stats.class_distribution,
      stats.training_distribution_pct
    )
  );
  activeCharts.push(renderConfidenceChart(document.getElementById('confidenceChart'), stats.confidence_histogram));
  activeCharts.push(renderLatencyChart(document.getElementById('latencyChart'), stats.latency_points));

  if (Object.keys(stats.agent_tool_usage).length > 0) {
    const canvas = document.getElementById('toolUsageChart');
    if (canvas) activeCharts.push(renderToolUsageChart(canvas, stats.agent_tool_usage));
  }
}

document.getElementById('themeToggle').addEventListener('click', () => {
  // Runs after theme.js's own listener (registered first, since main.js
  // imports it before this) has already applied the new data-theme.
  if (latestStats) renderAllCharts(latestStats);
});

async function init() {
  const dashEmpty = document.getElementById('dashEmpty');
  const dashContent = document.getElementById('dashContent');

  let stats;
  try {
    stats = await fetchStats();
  } catch {
    dashEmpty.innerHTML = '<i class="fas fa-triangle-exclamation"></i><p>Could not load dashboard data. Try refreshing.</p>';
    dashEmpty.style.display = 'flex';
    return;
  }

  if (stats.total_scans === 0) {
    dashEmpty.style.display = 'flex';
    return;
  }

  latestStats = stats;
  dashContent.style.display = 'block';

  countUp(document.getElementById('statTotalScans'), stats.total_scans);
  countUp(document.getElementById('statMeanConfidence'), stats.mean_confidence, { decimals: 1, suffix: '%' });
  countUp(document.getElementById('statRecyclablePct'), stats.recyclable_pct, { decimals: 1, suffix: '%' });
  countUp(document.getElementById('statLatencyP50'), stats.latency_p50_ms, { decimals: 0, suffix: 'ms' });
  countUp(document.getElementById('statLatencyP95'), stats.latency_p95_ms, { decimals: 0, suffix: 'ms' });

  renderConfusionTable(document.getElementById('confusionTableWrap'), stats.confusion_matrix);

  if (Object.keys(stats.agent_tool_usage).length === 0) {
    document.getElementById('toolUsageChart').replaceWith(
      Object.assign(document.createElement('p'), {
        className: 'confusion-empty',
        textContent: 'No agent-mode chats yet — turn on 🤖 Agent mode in the chat to see tool usage here.',
      })
    );
  }

  renderAllCharts(stats);
}

init();
