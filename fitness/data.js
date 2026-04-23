// ─────────────────────────────────────────────────────────────────
// VDOT pace tables (Jack Daniels) — pace in seconds per mile & km
// Keyed by VDOT. Covers 28 → 45 which spans 33:00 → 22:30 for 5k.
// ─────────────────────────────────────────────────────────────────
const VDOT_TABLE = {
  // 5k time in seconds, and pace zones in sec/mi
  28: { fiveK: 2100, E: [518, 560], M: 478, T: 441, I: 406, R: 93 },
  29: { fiveK: 2034, E: [505, 546], M: 464, T: 429, I: 395, R: 90 },
  30: { fiveK: 1980, E: [497, 538], M: 461, T: 423, I: 389, R: 89 },
  31: { fiveK: 1920, E: [485, 525], M: 449, T: 413, I: 381, R: 87 },
  32: { fiveK: 1860, E: [473, 513], M: 438, T: 403, I: 372, R: 85 },
  33: { fiveK: 1800, E: [462, 500], M: 427, T: 393, I: 363, R: 83 },
  34: { fiveK: 1746, E: [451, 489], M: 417, T: 383, I: 354, R: 80 },
  35: { fiveK: 1695, E: [441, 478], M: 407, T: 374, I: 346, R: 78 },
  36: { fiveK: 1647, E: [431, 467], M: 398, T: 365, I: 338, R: 77 },
  37: { fiveK: 1602, E: [421, 457], M: 389, T: 357, I: 330, R: 75 },
  38: { fiveK: 1560, E: [412, 447], M: 380, T: 349, I: 323, R: 73 },
  39: { fiveK: 1521, E: [403, 437], M: 372, T: 342, I: 316, R: 72 },
  40: { fiveK: 1485, E: [395, 428], M: 364, T: 334, I: 309, R: 70 },
  41: { fiveK: 1452, E: [387, 420], M: 357, T: 327, I: 302, R: 69 },
  42: { fiveK: 1420, E: [379, 411], M: 349, T: 320, I: 296, R: 67 },
  43: { fiveK: 1390, E: [372, 403], M: 342, T: 314, I: 290, R: 66 },
  44: { fiveK: 1362, E: [365, 396], M: 335, T: 308, I: 285, R: 65 },
  45: { fiveK: 1335, E: [358, 388], M: 329, T: 302, I: 279, R: 63 }
};

// Nearest VDOT for a given 5k time (seconds).
function vdotFor5k(seconds) {
  let best = 30;
  let bestDiff = Infinity;
  for (const v of Object.keys(VDOT_TABLE)) {
    const d = Math.abs(VDOT_TABLE[v].fiveK - seconds);
    if (d < bestDiff) { bestDiff = d; best = +v; }
  }
  return best;
}

function formatPace(secPerMile, unit = 'mi') {
  const sec = unit === 'km' ? secPerMile / 1.609 : secPerMile;
  const m = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
}

function formatTime(seconds) {
  const m = Math.floor(seconds / 60);
  const s = Math.round(seconds % 60);
  return `${m}:${String(s).padStart(2, '0')}`;
}

function parseTime(str) {
  if (!str) return 0;
  const parts = str.split(':').map((x) => +x);
  if (parts.length === 2) return parts[0] * 60 + parts[1];
  if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
  return +str || 0;
}

// ─────────────────────────────────────────────────────────────────
// 16-week periodised running plan.
// Base (1-4) — aerobic foundation, strides
// Build (5-9) — intervals + tempo extending
// Peak (10-14) — race-specific, 5k-pace work
// Taper (15-16) — sharpen, time trial
// Each week: Mon easy, Wed quality, Fri tempo/moderate, Sat long
// VDOT ramps 30 → 40 over 16 weeks (aggressive — coach flags if behind).
// ─────────────────────────────────────────────────────────────────
const RUN_PLAN = [
  // Week 1 — Base
  { week: 1, phase: 'Base', vdot: 30, mon: { type: 'easy', miles: 3, desc: 'Easy 3mi — conversational pace' }, wed: { type: 'easy+strides', miles: 3, desc: 'Easy 3mi + 4×20s strides' }, fri: { type: 'easy', miles: 3, desc: 'Easy 3mi' }, sat: { type: 'long', miles: 4, desc: 'Long 4mi — all easy pace' } },
  { week: 2, phase: 'Base', vdot: 30, mon: { type: 'easy', miles: 3.5, desc: 'Easy 3.5mi' }, wed: { type: 'easy+strides', miles: 3.5, desc: 'Easy 3.5mi + 5×20s strides' }, fri: { type: 'easy', miles: 3, desc: 'Easy 3mi' }, sat: { type: 'long', miles: 5, desc: 'Long 5mi — all easy' } },
  { week: 3, phase: 'Base', vdot: 31, mon: { type: 'easy', miles: 4, desc: 'Easy 4mi' }, wed: { type: 'tempo', miles: 4, desc: '1mi warmup, 2mi @ tempo, 1mi cooldown' }, fri: { type: 'easy', miles: 3, desc: 'Easy 3mi' }, sat: { type: 'long', miles: 5.5, desc: 'Long 5.5mi easy' } },
  { week: 4, phase: 'Base', vdot: 31, mon: { type: 'easy', miles: 3, desc: 'Easy 3mi recovery (cutback week)' }, wed: { type: 'easy+strides', miles: 3, desc: 'Easy 3mi + 6×20s strides' }, fri: { type: 'easy', miles: 3, desc: 'Easy 3mi' }, sat: { type: 'long', miles: 4, desc: 'Long 4mi — cutback' } },
  // Weeks 5-9 Build
  { week: 5, phase: 'Build', vdot: 32, mon: { type: 'easy', miles: 4, desc: 'Easy 4mi' }, wed: { type: 'intervals', miles: 4, desc: '1mi wu, 6×400m @ I-pace (200m jog), 1mi cd', reps: { count: 6, distance: 400, pace: 'I', rest: '200m jog' } }, fri: { type: 'tempo', miles: 4, desc: '1mi wu, 2mi @ T-pace, 1mi cd' }, sat: { type: 'long', miles: 6, desc: 'Long 6mi easy' } },
  { week: 6, phase: 'Build', vdot: 33, mon: { type: 'easy', miles: 4, desc: 'Easy 4mi' }, wed: { type: 'intervals', miles: 4.5, desc: '1mi wu, 4×800m @ I-pace (400m jog), 1mi cd', reps: { count: 4, distance: 800, pace: 'I', rest: '400m jog' } }, fri: { type: 'tempo', miles: 4.5, desc: '1mi wu, 2.5mi @ T-pace, 1mi cd' }, sat: { type: 'long', miles: 6.5, desc: 'Long 6.5mi easy' } },
  { week: 7, phase: 'Build', vdot: 33, mon: { type: 'easy', miles: 4, desc: 'Easy 4mi' }, wed: { type: 'intervals', miles: 5, desc: '1mi wu, 5×800m @ I-pace (400m jog), 1mi cd', reps: { count: 5, distance: 800, pace: 'I', rest: '400m jog' } }, fri: { type: 'tempo', miles: 5, desc: '1mi wu, 3mi @ T-pace, 1mi cd' }, sat: { type: 'long', miles: 7, desc: 'Long 7mi easy' } },
  { week: 8, phase: 'Build', vdot: 34, mon: { type: 'easy', miles: 3, desc: 'Easy 3mi (cutback)' }, wed: { type: 'intervals', miles: 4, desc: '1mi wu, 6×400m @ I-pace (200m jog), 1mi cd', reps: { count: 6, distance: 400, pace: 'I', rest: '200m jog' } }, fri: { type: 'easy', miles: 3, desc: 'Easy 3mi' }, sat: { type: 'long', miles: 5, desc: 'Long 5mi — cutback' } },
  { week: 9, phase: 'Build', vdot: 35, mon: { type: 'easy', miles: 4, desc: 'Easy 4mi' }, wed: { type: 'intervals', miles: 5.5, desc: '1mi wu, 5×1k @ I-pace (400m jog), 1mi cd', reps: { count: 5, distance: 1000, pace: 'I', rest: '400m jog' } }, fri: { type: 'tempo', miles: 5, desc: '1mi wu, 3mi @ T-pace, 1mi cd' }, sat: { type: 'long', miles: 7.5, desc: 'Long 7.5mi easy' } },
  // Weeks 10-14 Peak
  { week: 10, phase: 'Peak', vdot: 36, mon: { type: 'easy', miles: 4, desc: 'Easy 4mi' }, wed: { type: 'intervals', miles: 6, desc: '1mi wu, 4×1k @ 5k-pace (400m jog), 1mi cd', reps: { count: 4, distance: 1000, pace: 'I', rest: '400m jog' } }, fri: { type: 'tempo', miles: 5.5, desc: '1mi wu, 3.5mi @ T-pace, 1mi cd' }, sat: { type: 'long', miles: 8, desc: 'Long 8mi easy' } },
  { week: 11, phase: 'Peak', vdot: 37, mon: { type: 'easy', miles: 4, desc: 'Easy 4mi' }, wed: { type: 'intervals', miles: 6, desc: '1mi wu, 5×1k @ 5k-pace (400m jog), 1mi cd', reps: { count: 5, distance: 1000, pace: 'I', rest: '400m jog' } }, fri: { type: 'tempo', miles: 6, desc: '1mi wu, 4mi @ T-pace, 1mi cd' }, sat: { type: 'long', miles: 8.5, desc: 'Long 8.5mi easy' } },
  { week: 12, phase: 'Peak', vdot: 37, mon: { type: 'easy', miles: 3, desc: 'Easy 3mi (cutback)' }, wed: { type: 'intervals', miles: 5, desc: '1mi wu, 3×1mi @ T-pace (400m jog), 1mi cd', reps: { count: 3, distance: 1609, pace: 'T', rest: '400m jog' } }, fri: { type: 'easy', miles: 4, desc: 'Easy 4mi' }, sat: { type: 'long', miles: 6, desc: 'Long 6mi — cutback' } },
  { week: 13, phase: 'Peak', vdot: 38, mon: { type: 'easy', miles: 4, desc: 'Easy 4mi' }, wed: { type: 'intervals', miles: 6, desc: '1mi wu, 6×800m @ 5k-pace (400m jog), 1mi cd', reps: { count: 6, distance: 800, pace: 'I', rest: '400m jog' } }, fri: { type: 'tempo', miles: 6, desc: '1mi wu, 4mi @ T-pace, 1mi cd' }, sat: { type: 'long', miles: 9, desc: 'Long 9mi easy' } },
  { week: 14, phase: 'Peak', vdot: 39, mon: { type: 'easy', miles: 4, desc: 'Easy 4mi' }, wed: { type: 'intervals', miles: 6, desc: '1mi wu, 8×400m @ R-pace (400m jog), 1mi cd', reps: { count: 8, distance: 400, pace: 'R' } }, fri: { type: 'tempo', miles: 5, desc: '1mi wu, 3mi @ T-pace, 1mi cd' }, sat: { type: 'long', miles: 7, desc: 'Long 7mi easy' } },
  // Weeks 15-16 Taper + Race
  { week: 15, phase: 'Taper', vdot: 39, mon: { type: 'easy', miles: 3, desc: 'Easy 3mi' }, wed: { type: 'intervals', miles: 4, desc: '1mi wu, 4×400m @ 5k-pace (400m jog), 1mi cd', reps: { count: 4, distance: 400, pace: 'I', rest: '400m jog' } }, fri: { type: 'easy+strides', miles: 3, desc: 'Easy 3mi + 4×20s strides' }, sat: { type: 'long', miles: 5, desc: 'Easy 5mi — stay fresh' } },
  { week: 16, phase: 'Race', vdot: 40, mon: { type: 'easy', miles: 2, desc: 'Easy 2mi shakeout' }, wed: { type: 'easy+strides', miles: 3, desc: 'Easy 2mi + 4×100m strides' }, fri: { type: 'rest', miles: 0, desc: 'REST — race day is close' }, sat: { type: 'race', miles: 3.1, desc: '🏁 5k TIME TRIAL / RACE — aim for sub-25' } }
];

// ─────────────────────────────────────────────────────────────────
// Gym program — 4 days/week, aesthetics + strength
// Mon: Upper Push | Wed: Upper Pull | Fri: Lower (run-friendly) | Sat: Arms + Core (light)
// Progressive overload: +2.5kg when all sets hit top of rep range
// ─────────────────────────────────────────────────────────────────
const GYM_DAYS = {
  mon: {
    name: 'Upper Push',
    emoji: '💥',
    focus: 'Chest • Shoulders • Triceps',
    exercises: [
      { name: 'Barbell Bench Press', sets: 4, reps: '6-8', rest: '2-3 min', note: 'Primary strength lift — push weight' },
      { name: 'Incline DB Press', sets: 3, reps: '8-10', rest: '90s', note: 'Upper chest — aesthetics focus' },
      { name: 'Standing Overhead Press', sets: 3, reps: '6-8', rest: '2 min', note: 'Strict form, full ROM' },
      { name: 'Cable Lateral Raise', sets: 4, reps: '12-15', rest: '60s', note: 'Wider shoulders — shredded look' },
      { name: 'Dips (weighted)', sets: 3, reps: '8-10', rest: '90s', note: 'Chest+triceps compound' },
      { name: 'Tricep Rope Pushdown', sets: 3, reps: '12-15', rest: '60s', note: 'Arm finisher' }
    ]
  },
  wed: {
    name: 'Upper Pull',
    emoji: '🪢',
    focus: 'Back • Biceps • Rear Delts',
    exercises: [
      { name: 'Pull-ups (weighted if able)', sets: 4, reps: '6-10', rest: '2 min', note: 'King of back — width' },
      { name: 'Barbell Row', sets: 4, reps: '6-8', rest: '2 min', note: 'Thickness, heavy' },
      { name: 'Lat Pulldown (wide)', sets: 3, reps: '10-12', rest: '90s', note: 'Back width pump' },
      { name: 'Seated Cable Row', sets: 3, reps: '10-12', rest: '90s', note: 'Squeeze mid-back' },
      { name: 'Face Pulls', sets: 3, reps: '15-20', rest: '60s', note: 'Rear delts + posture (critical for runners)' },
      { name: 'DB Hammer Curl', sets: 3, reps: '10-12', rest: '60s', note: 'Brachialis — arm thickness' },
      { name: 'Barbell Curl', sets: 3, reps: '8-10', rest: '60s', note: 'Biceps mass' }
    ],
    postRun: true
  },
  fri: {
    name: 'Lower (Run-Friendly)',
    emoji: '🦵',
    focus: 'Posterior Chain • Glutes • Core',
    warning: 'Long run tomorrow — avoid max-effort squats. Prioritise hip hinge.',
    exercises: [
      { name: 'Romanian Deadlift', sets: 4, reps: '6-8', rest: '2 min', note: 'Hamstrings + glutes — crucial for running economy' },
      { name: 'Bulgarian Split Squat', sets: 3, reps: '8-10 each', rest: '90s', note: 'Single-leg strength — running specific' },
      { name: 'Hip Thrust', sets: 4, reps: '8-12', rest: '90s', note: 'Glute power' },
      { name: 'Goblet Squat (moderate)', sets: 3, reps: '10-12', rest: '90s', note: 'Moderate load only — save legs for Sat' },
      { name: 'Standing Calf Raise', sets: 4, reps: '12-15', rest: '60s', note: 'Achilles resilience' },
      { name: 'Hanging Leg Raise', sets: 3, reps: '10-15', rest: '60s', note: 'Core — running posture' },
      { name: 'Plank', sets: 3, reps: '45-60s', rest: '45s', note: 'Anti-extension core' }
    ]
  },
  sat: {
    name: 'Arms + Core (Light)',
    emoji: '💪',
    focus: 'Arms • Core • Weak Points',
    warning: 'After long run — keep intensity moderate, focus on pump and recovery.',
    exercises: [
      { name: 'EZ Bar Preacher Curl', sets: 3, reps: '10-12', rest: '60s', note: 'Biceps peak' },
      { name: 'Incline DB Curl', sets: 3, reps: '10-12', rest: '60s', note: 'Long head of biceps' },
      { name: 'Skull Crushers', sets: 3, reps: '10-12', rest: '60s', note: 'Long head of triceps' },
      { name: 'Overhead Cable Extension', sets: 3, reps: '12-15', rest: '60s', note: 'Tricep stretch' },
      { name: 'Cable Crunch', sets: 3, reps: '15-20', rest: '60s', note: 'Upper abs' },
      { name: 'Russian Twist', sets: 3, reps: '20 total', rest: '45s', note: 'Obliques — V-taper' },
      { name: 'DB Shrug', sets: 3, reps: '12-15', rest: '60s', note: 'Traps — shredded yoke look' }
    ],
    postRun: true
  }
};

// Day-of-week schedule
const WEEK_SCHEDULE = [
  { day: 'Sun', key: 'sun', sessions: ['rest'] },
  { day: 'Mon', key: 'mon', sessions: ['gym', 'run'] },
  { day: 'Tue', key: 'tue', sessions: ['boxing'] },
  { day: 'Wed', key: 'wed', sessions: ['run', 'gym'] },
  { day: 'Thu', key: 'thu', sessions: ['boxing'] },
  { day: 'Fri', key: 'fri', sessions: ['run', 'gym'] },
  { day: 'Sat', key: 'sat', sessions: ['run', 'gym'] }
];
