export async function fetchStats() {
  const res = await fetch('/api/stats');
  if (!res.ok) {
    throw new Error(`Failed to load stats (${res.status})`);
  }
  return res.json();
}
