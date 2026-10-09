const express = require('express');

const router = express.Router();

// There's no pe_session cookie anymore (identity comes from the hub's own
// session) — kept only so the frontend's existing api.signOut() call, which
// still fires on sign-out as a courtesy, doesn't 404.
router.post('/signout', (req, res) => {
  res.status(200).json({ ok: true });
});

module.exports = router;
