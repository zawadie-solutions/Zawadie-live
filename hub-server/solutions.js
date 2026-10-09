// Single source of truth for every solution the hub knows about: its proxy
// target, its card copy, and the icon shown for it. Attendance Tracking
// System is intentionally absent — it's a desktop app, not a web app, and
// was pulled from the hub for now.
const fs = require('node:fs');
const path = require('node:path');

// Reads DASHBOARD_USER / DASHBOARD_PASSWORD straight from the sibling
// project's own .env instead of copying the secret into this repo too.
function readSiblingEnv(projectDir, keys) {
  const envPath = path.join(__dirname, '..', projectDir, '.env');
  const out = {};
  if (!fs.existsSync(envPath)) return out;
  for (const line of fs.readFileSync(envPath, 'utf8').split('\n')) {
    const match = /^\s*([A-Z0-9_]+)\s*=\s*(.*)\s*$/.exec(line);
    if (match && keys.includes(match[1])) out[match[1]] = match[2];
  }
  return out;
}

const reviewMonitorEnv = readSiblingEnv('google-review-monitor', ['DASHBOARD_USER', 'DASHBOARD_PASSWORD']);

module.exports = [
  {
    id: 'ombeni-ai',
    name: 'Ombeni AI',
    category: 'Company Assistant',
    description:
      "Zawadie's standalone AI employee — a company assistant that answers questions and gets work done by plugging into calendar, Slack, and Monday.com.",
    status: 'available',
    // Mounted in-process (see apps/ombeni-ai/router.js, wired in server.js) —
    // no separate process, no proxy target.
    mode: 'mounted',
    icon: 'bot',
  },
  {
    id: 'prompt-engineering',
    name: 'Prompt Engineering',
    category: 'Internal Training',
    description:
      'Zawadie PromptClass — internal prompt-engineering training for Zawadie Solutions agents, with lessons, exams, progress tracking, and a leaderboard.',
    status: 'available',
    // Mounted in-process (built frontend + hand-ported API routes under
    // apps/prompt-engineering/, wired in server.js) — the standalone Vercel
    // deployment this used to proxy to is no longer used by the hub.
    mode: 'mounted',
    icon: 'cap',
  },
  // Face-match-system is intentionally absent — it's a Python/FastAPI
  // (uvicorn) service, and Hostinger's Unlimited plan only runs Node.js Web
  // Apps, not arbitrary Python processes. Revisit once it has a host that
  // can run it (e.g. a VPS).
  {
    id: 'google-review-monitor',
    name: 'Google Review Monitor',
    category: 'Operations',
    description:
      'Watches Google review links tracked in Asana and flags when one disappears, so a bad review being removed by its author never goes unnoticed.',
    // Still being built out (see google-review-monitor/README.md) — listed
    // so the team can see it coming, but not yet promoted to "available".
    status: 'development',
    // Its own ESM/TypeScript cron-worker process (own Postgres DB, no build
    // step) — not a candidate for in-process merging; stays reverse-proxied.
    mode: 'proxy',
    target: process.env.GOOGLE_REVIEW_MONITOR_URL || 'http://localhost:3002',
    stripPrefix: true,
    icon: 'star',
    // The app's own Basic Auth (defense in depth behind the hub's login).
    // The hub injects these credentials when proxying, so a signed-in
    // employee never sees a second login prompt.
    basicAuth: { user: reviewMonitorEnv.DASHBOARD_USER, pass: reviewMonitorEnv.DASHBOARD_PASSWORD },
  },
  {
    id: 'bam-comment-review',
    name: 'BAM Comment Review',
    category: 'Social Media',
    description:
      'Reviews and manages comments on our locations’ social pages, with AI-drafted replies and an admin portal for staff.',
    status: 'available',
    // Hosted separately on Vercel, so the hub just links out to it instead
    // of proxying a local server.
    mode: 'external',
    externalUrl: 'https://cm-system-sable.vercel.app/',
    icon: 'chat',
  },
];
