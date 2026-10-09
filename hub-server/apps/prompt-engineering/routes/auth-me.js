const express = require('express');
const { getSql } = require('../db');
const { getUserFromSession } = require('../identity');

const router = express.Router();

router.get('/me', async (req, res) => {
  try {
    const user = await getUserFromSession(req);
    if (!user) return res.status(200).json({ user: null, progress: null });

    const sql = getSql();
    const rows = await sql`
      SELECT points, streak, last_active_date::text AS last_active_date, completed_exercises, quiz_passed, badges
      FROM progress WHERE user_id = ${user.id}
    `;
    const progress = rows[0];

    res.status(200).json({
      user: { id: user.id, email: user.email, displayName: user.display_name },
      progress: progress && {
        points: progress.points,
        streak: progress.streak,
        lastActiveDate: progress.last_active_date,
        completedExercises: progress.completed_exercises,
        quizPassed: progress.quiz_passed,
        badges: progress.badges,
      },
    });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
