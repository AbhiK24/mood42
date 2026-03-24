// Simulation state for mood42

export const PALETTE = {
  nightInk: 0x080810,
  rainySky: 0x0d1f3c,
  lampOak: 0x1e1508,
  tungsten: 0xe8c89a,
  paper: 0xf2efe8,
  neonRed: 0xff4d6d,
  neonBlue: 0x4d9fff,
  exitGreen: 0x39ff8a,
  steam: 0x606078,
  skinWarm: 0xc39b78,
  hairDark: 0x23160c,
  cloth: 0x504b5a,
}

export const simState = {
  time: 23 * 60 + 47,       // minutes since midnight — starts 11:47pm
  raining: true,
  rainIntensity: 0.7,       // 0.0 → 1.0
  characterMood: 'FOCUSED', // FOCUSED | WITHDRAWN | GOOD | ANXIOUS | FLOOR
  lampOn: true,
  lampIntensity: 1.0,
  paused: false,
  objects: {
    laptopOpen: true,
    secondCup: false,
    candle: false,
    phoneGlowing: false,
    characterOnFloor: false,
  },
  tickCount: 0,
  oneAmLightOff: false,
  neonPhase: 0,
}

export const MOODS = {
  FOCUSED: { level: 6, type: 'active' },
  GOOD: { level: 8, type: 'high' },
  WITHDRAWN: { level: 3, type: 'low' },
  ANXIOUS: { level: 4, type: 'low' },
  FLOOR: { level: 2, type: 'low' },
}

export function getMoodLevel() {
  return MOODS[simState.characterMood]?.level || 5
}

export function getMoodType() {
  return MOODS[simState.characterMood]?.type || 'active'
}

export function setMood(mood) {
  if (MOODS[mood]) {
    simState.characterMood = mood
  }
}

export function cycleMood() {
  const moods = Object.keys(MOODS)
  const idx = moods.indexOf(simState.characterMood)
  simState.characterMood = moods[(idx + 1) % moods.length]
}

export function advanceTime(minutes = 2) {
  simState.time = (simState.time + minutes) % (24 * 60)
}

export function getTimeDisplay() {
  const totalMins = simState.time % (24 * 60)
  const h = Math.floor(totalMins / 60) % 24
  const m = totalMins % 60
  const h12 = h % 12 === 0 ? 12 : h % 12
  return `${h12}:${m.toString().padStart(2, '0')}`
}

export function isNightTime() {
  const h = Math.floor((simState.time % (24 * 60)) / 60)
  return h >= 20 || h <= 5
}
