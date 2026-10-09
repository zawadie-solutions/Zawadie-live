const express = require('express');
const router = express.Router();

const authService = require('../services/authService');
const store = require('../data/store');
const admins = require('../data/admins');

router.get('/google', (req, res) => {
  if (!authService.isConfigured()) {
    return res.status(503).send('Google sign-in is not configured yet. Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env.');
  }
  res.redirect(authService.getAuthUrl());
});

router.get('/google/callback', async (req, res) => {
  try {
    if (!req.query.code) throw new Error('Missing authorization code');
    const { user, googleTokens } = await authService.exchangeCodeForUser(req.query.code);
    // This is now a "connect Google Calendar" action, not the sign-in gate
    // (that's the hub's job — see services/hubTrust.js). Merge Google's
    // richer profile (name, picture) onto whatever identity is already
    // there rather than replacing it, so a hub-sourced email can't be
    // swapped out by connecting a different Google account.
    req.session.user = { ...req.session.user, ...user };
    req.session.googleTokens = googleTokens; // server-side only, used for Calendar API calls
    store.logActivity({ user: req.session.user.name, action: 'Connected Google Calendar', source: 'Google', result: 'Success' });
    res.redirect('/');
  } catch (err) {
    res.status(401).send(`Sign-in failed: ${err.message}`);
  }
});

router.post('/logout', (req, res) => {
  const user = req.session.user;
  req.session.destroy(() => {
    if (user) store.logActivity({ user: user.name, action: 'Signed out', source: 'Google' });
    res.json({ success: true });
  });
});

router.get('/me', (req, res) => {
  const user = req.session.user || null;
  res.json({
    success: true,
    data: {
      googleConfigured: authService.isConfigured(),
      calendarConnected: Boolean(req.session.googleTokens),
      user,
      isAdmin: Boolean(user) && admins.isAdmin(user.email)
    }
  });
});

module.exports = router;
