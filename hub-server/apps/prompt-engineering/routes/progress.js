const express = require('express');
const { getSql } = require('../db');
const { getUserFromSession } = require('../identity');

const router = express.Router();
router.use(express.json());

router.get('/', async (req, res) => {
  try {
    const user = await getUserFromSession(req);
    if (!user) return res.status(401).json({ error: 'Not signed in' });

    const sql = getSql();
    const rows = await sql`
      SELECT points, streak, last_active_date::text AS last_active_date, completed_exercises, quiz_passed, badges
      FROM progress WHERE user_id = ${user.id}
    `;
    const progress = rows[0];
    res.status(200).json({
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

router.put('/', async (req, res) => {
  try {
    const user = await getUserFromSession(req);
    if (!user) return res.status(401).json({ error: 'Not signed in' });

    const sql = getSql();
    const body = req.body ?? {};
    const points = Number.isFinite(body.points) ? Math.trunc(body.points) : 0;
    const streak = Number.isFinite(body.streak) ? Math.trunc(body.streak) : 0;
    const lastActiveDate = typeof body.lastActiveDate === 'string' ? body.lastActiveDate : null;
    const completedExercises =
      body.completedExercises && typeof body.completedExercises === 'object' ? body.completedExercises : {};
    const quizPassed = body.quizPassed && typeof body.quizPassed === 'object' ? body.quizPassed : {};
    const badges = Array.isArray(body.badges) ? body.badges : [];

    await sql`
      INSERT INTO progress (user_id, points, streak, last_active_date, completed_exercises, quiz_passed, badges, updated_at)
      VALUES (${user.id}, ${points}, ${streak}, ${lastActiveDate}, ${JSON.stringify(completedExercises)}, ${JSON.stringify(quizPassed)}, ${JSON.stringify(badges)}, now())
      ON CONFLICT (user_id) DO UPDATE SET
        points = EXCLUDED.points,
        streak = EXCLUDED.streak,
        last_active_date = EXCLUDED.last_active_date,
        completed_exercises = EXCLUDED.completed_exercises,
        quiz_passed = EXCLUDED.quiz_passed,
        badges = EXCLUDED.badges,
        updated_at = now()
    `;
    res.status(200).json({ ok: true });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

module.exports = router;
