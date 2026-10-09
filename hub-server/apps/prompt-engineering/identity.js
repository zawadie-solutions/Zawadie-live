// Ported from api/_lib/auth.ts. Mounted in-process behind the hub's own
// login now, so there's no signed-header verification or pe_session cookie
// to check — req.session.user is already the hub's authenticated user.
const { getSql } = require('./db');
const { nameFromEmail } = require('../../lib/identity');

// Finds the account for a hub-verified email, creating one on first sight.
// Reuses any row already created back when this app had its own signup, so
// existing progress/leaderboard history for that email carries forward.
async function getOrCreateHubUser(email) {
  const sql = getSql();
  const existing = await sql`SELECT id, email, display_name FROM users WHERE email = ${email}`;
  if (existing[0]) return existing[0];

  const inserted = await sql`
    INSERT INTO users (email, display_name)
    VALUES (${email}, ${nameFromEmail(email)})
    ON CONFLICT (email) DO UPDATE SET email = EXCLUDED.email
    RETURNING id, email, display_name
  `;
  return inserted[0];
}

async function getUserFromSession(req) {
  if (!req.session.user) return null;
  return getOrCreateHubUser(req.session.user.email.toLowerCase());
}

module.exports = { getOrCreateHubUser, getUserFromSession };
