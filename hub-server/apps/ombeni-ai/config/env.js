// override: true makes this project's .env win over any same-named variable
// already sitting in the OS environment (e.g. a stale OPENAI_API_KEY set at
// the Windows user/system level) — otherwise dotenv silently keeps the OS
// value and .env changes appear to do nothing.
require('dotenv').config({ override: true });

const env = {
  OPENAI_API_KEY: process.env.OPENAI_API_KEY || '',
  MONDAY_API_KEY: process.env.MONDAY_API_KEY || '',
  MONDAY_BOARD_ID: process.env.MONDAY_BOARD_ID || '',
  // Recorded meetings can live under more than one Monday.com/Notetaker
  // account (e.g. a teammate's own Notetaker bot that isn't shared into the
  // primary account) — MONDAY_API_KEY_2, _3, etc. let the Notetaker fetch
  // pull from all of them and merge the results, so a recording that's
  // "missing" from one account's view still shows up. Task creation
  // (mondayService) intentionally keeps using MONDAY_API_KEY only.
  MONDAY_API_KEYS: Object.keys(process.env)
    .filter(k => /^MONDAY_API_KEY(_\d+)?$/.test(k))
    .sort((a, b) => (a === 'MONDAY_API_KEY' ? 0 : Number(a.slice('MONDAY_API_KEY_'.length)))
      - (b === 'MONDAY_API_KEY' ? 0 : Number(b.slice('MONDAY_API_KEY_'.length))))
    .map(k => process.env[k])
    .filter(Boolean),
  SLACK_BOT_TOKEN: process.env.SLACK_BOT_TOKEN || '',
  SLACK_CHANNEL: process.env.SLACK_CHANNEL || '',
  GOOGLE_CLIENT_ID: process.env.GOOGLE_CLIENT_ID || '',
  GOOGLE_CLIENT_SECRET: process.env.GOOGLE_CLIENT_SECRET || '',
  GOOGLE_REDIRECT_URI: process.env.GOOGLE_REDIRECT_URI || '',
  // The login screen tells users sign-in is restricted to @zawadie.com — this
  // is what actually enforces that; without it, exchangeCodeForUser accepted
  // any Google account with a verified email, from any domain.
  GOOGLE_ALLOWED_DOMAIN: process.env.GOOGLE_ALLOWED_DOMAIN || 'zawadie.com',
  // No longer used to verify anything (this app is mounted in-process behind
  // the hub's own login now) — kept only as the "is an identity source
  // configured at all" flag read by routes/api.js's hasIdentitySource().
  SSO_SHARED_SECRET: process.env.ZAWADIE_SSO_SECRET || ''
};

env.isOpenAIConfigured = Boolean(env.OPENAI_API_KEY);
env.isMondayConfigured = Boolean(env.MONDAY_API_KEY && env.MONDAY_BOARD_ID);
env.isSlackConfigured = Boolean(env.SLACK_BOT_TOKEN && env.SLACK_CHANNEL);
env.isNotetakerConfigured = env.MONDAY_API_KEYS.length > 0;
env.isGoogleConfigured = Boolean(env.GOOGLE_CLIENT_ID && env.GOOGLE_CLIENT_SECRET);

module.exports = env;
