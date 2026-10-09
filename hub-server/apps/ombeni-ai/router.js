const express = require('express');
const path = require('path');
const store = require('./data/store');
const { nameFromEmail } = require('../../lib/identity');

const router = express.Router();

// Mounted in-process behind the hub's own login (hub-server/server.js), so
// req.session.user is already the hub's signed-in user — no separate
// session or identity-header verification needed here. The hub's session
// user only has { email, role, solutions }; backfill .name once since
// routes/api.js and routes/auth.js read it throughout.
router.use((req, res, next) => {
  if (req.session.user && !req.session.user.name) {
    req.session.user.name = nameFromEmail(req.session.user.email);
  }
  next();
});

router.use(express.json());
router.use(express.static(path.join(__dirname, 'public')));

router.use('/auth', require('./routes/auth'));
router.use('/api', require('./routes/api'));

// Without this, the in-memory meeting list only updates on server restart or
// a manual "Refresh from Notetaker" click — so a meeting that just finished
// recording wouldn't show up (or match against today's calendar events) until
// someone happened to click refresh. Keep it modest: Notetaker recordings
// don't appear instantly anyway, and this only needs to run a few times an hour.
function startBackgroundRefresh() {
  store.refreshMeetings()
    .then(() => console.log(store.isUsingNotetaker() ? '✅ Loaded real meetings from Monday Notetaker' : 'ℹ️ Monday not configured — using demo meeting data'))
    .catch((err) => console.error('⚠️ Failed to load Notetaker meetings, falling back to demo data:', err.message));

  setInterval(() => {
    store.refreshMeetings().catch((err) => console.error('⚠️ Background meeting refresh failed:', err.message));
  }, 5 * 60 * 1000);
}

module.exports = { router, startBackgroundRefresh };
