const express = require('express');
const { getSql } = require('../db');

const router = express.Router();

router.get('/', async (req, res) => {
  try {
    const sql = getSql();
    const rows = await sql`
      SELECT u.display_name, p.points
      FROM progress p
      JOIN users u ON u.id = p.user_id
      ORDER BY p.points DESC, u.created_at ASC
      LIMIT 25
    `;

    res.status(200).json({
      entries: rows.map((r) => ({ displayName: r.display_name, points: r.points })),
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
