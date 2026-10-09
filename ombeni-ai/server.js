const express = require('express');
const session = require('express-session');
const path = require('path');
const env = require('./config/env');
const store = require('./data/store');
const { verifyHubUser, nameFromEmail } = require('./services/hubTrust');

const app = express();
const PORT = env.PORT;

app.use(express.json());
app.use(session({
  // Named explicitly (not the express-session default "connect.sid") so it
  // can't collide with the hub's own session cookie once this app is
  // reverse-proxied under the hub's origin.
  name: 'ombeni_ai.sid',
  secret: env.SESSION_SECRET,
  resave: false,
  saveUninitialized: false,
  cookie: { httpOnly: true, sameSite: 'lax', maxAge: 1000 * 60 * 60 * 24 * 7 }
}));

// Trusts the Zawadie Hub's already-completed login (see services/hubTrust.js)
// so this app never needs its own login gate for identity. Runs on every
// request, not just page loads, so a session started before the user had
// hub access still picks up admin/role changes made at the hub.
app.use((req, res, next) => {
  const hubUser = verifyHubUser(req);
  if (hubUser && (!req.session.user || req.session.user.email !== hubUser.email)) {
    req.session.user = { email: hubUser.email, name: nameFromEmail(hubUser.email), picture: null };
  }
  next();
});

app.use(express.static(path.join(__dirname, 'public')));

app.use('/auth', require('./routes/auth'));
app.use('/api', require('./routes/api'));

store.refreshMeetings()
  .then(() => console.log(store.isUsingNotetaker() ? '✅ Loaded real meetings from Monday Notetaker' : 'ℹ️ Monday not configured — using demo meeting data'))
  .catch(err => console.error('⚠️ Failed to load Notetaker meetings, falling back to demo data:', err.message))
  .finally(() => {
    app.listen(PORT, () => {
      console.log(`🚀 Ombeni AI running locally at http://localhost:${PORT}`);
    });
  });

// Without this, the in-memory meeting list only updates on server restart or
// a manual "Refresh from Notetaker" click — so a meeting that just finished
// recording wouldn't show up (or match against today's calendar events) until
// someone happened to click refresh. Keep it modest: Notetaker recordings
// don't appear instantly anyway, and this only needs to run a few times an hour.
setInterval(() => {
  store.refreshMeetings().catch(err => console.error('⚠️ Background meeting refresh failed:', err.message));
}, 5 * 60 * 1000);