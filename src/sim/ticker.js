// World tick engine for mood42

import { simState, advanceTime, getTimeDisplay, getMoodLevel, getMoodType } from './state.js'

const tickPool = [
  { text: "she checks her phone. doesn't respond.", weight: 3, type: 'normal' },
  { text: "types for 3 minutes. deletes it all.", weight: 3, type: 'normal' },
  { text: "looks out the window. rain picks up.", weight: 2, type: 'normal' },
  { text: "reaches for coffee. it's cold.", weight: 3, type: 'normal' },
  { text: "opens a new tab. closes it immediately.", weight: 2, type: 'normal' },
  { text: "someone texts. she reads it twice.", weight: 1, type: 'event', trigger: 'phoneGlow' },
  { text: "the neon outside flickers.", weight: 2, type: 'normal' },
  { text: "she exhales. long. slow.", weight: 2, type: 'normal' },
  { text: "starts typing again. faster this time.", weight: 2, type: 'normal' },
  { text: "the building opposite — that light is still on.", weight: 2, type: 'normal' },
  { text: "she pulls her knees up on the chair.", weight: 1, type: 'normal' },
  { text: "a notification. ignored.", weight: 2, type: 'normal' },
  { text: "the rain intensifies.", weight: 1, type: 'normal' },
  { text: "she almost smiles at something on screen.", weight: 1, type: 'event' },
  { text: "she stands. stretches. sits back down.", weight: 2, type: 'normal' },
  { text: "refills coffee. still hot this time.", weight: 1, type: 'normal' },
  { text: "RELATIONSHIP_EVENT: message from riya", weight: 1, type: 'event', trigger: 'moodShift' },
  { text: "types. stops. types again. sends.", weight: 2, type: 'normal' },
  { text: "the city goes a little quieter.", weight: 2, type: 'normal' },
]

// Build weighted pool
const weightedPool = []
tickPool.forEach(item => {
  for (let i = 0; i < item.weight; i++) {
    weightedPool.push(item)
  }
})

let tickIndex = 0
let tickInterval = null
const feedItems = []
let onTickCallback = null
let onOneAmCallback = null

export function initTicker(onTick, onOneAm) {
  onTickCallback = onTick
  onOneAmCallback = onOneAm

  for (let i = 0; i < 5; i++) {
    feedItems.push(document.getElementById(`t${i}`))
  }
}

function getRandomTick() {
  return weightedPool[Math.floor(Math.random() * weightedPool.length)]
}

export function addTick(msg, type) {
  // Shift items up
  for (let i = 0; i < feedItems.length - 1; i++) {
    if (feedItems[i] && feedItems[i + 1]) {
      feedItems[i].textContent = feedItems[i + 1].textContent
      feedItems[i].className = 'tick-item dim'
    }
  }

  const last = feedItems[feedItems.length - 1]
  if (last) {
    last.textContent = msg
    last.className = `tick-item ${type} visible`
  }

  simState.tickCount++
  const tickCountEl = document.getElementById('tick-count')
  if (tickCountEl) {
    tickCountEl.textContent = simState.tickCount
  }

  // Dim after delay
  setTimeout(() => {
    feedItems.forEach((f, i) => {
      if (f && i < feedItems.length - 1) {
        f.classList.add('dim')
        f.classList.remove('visible', 'event')
      }
    })
  }, 4000)
}

export function worldTick() {
  if (simState.paused) return

  const tick = getRandomTick()
  addTick(tick.text, tick.type)

  // Handle triggers
  if (tick.trigger === 'phoneGlow') {
    simState.objects.phoneGlowing = true
    setTimeout(() => {
      simState.objects.phoneGlowing = false
    }, 3000)
  }

  // Check for 1am light
  const mins = simState.time % (24 * 60)
  if (mins >= 60 && mins < 80 && !simState.oneAmLightOff) {
    simState.oneAmLightOff = true
    if (onOneAmCallback) {
      onOneAmCallback()
    }
    addTick('1:00am. the light across the street goes off. always.', 'event')
  }

  // Advance time
  advanceTime(2)

  // Update clock display
  updateClock()
  updateMoodBar()

  if (onTickCallback) {
    onTickCallback(tick)
  }
}

export function startTicker(intervalMs = 5000) {
  if (tickInterval) clearInterval(tickInterval)
  tickInterval = setInterval(worldTick, intervalMs)
}

export function stopTicker() {
  if (tickInterval) {
    clearInterval(tickInterval)
    tickInterval = null
  }
}

export function togglePause() {
  simState.paused = !simState.paused
}

export function updateClock() {
  const timeEl = document.getElementById('time-display')
  if (timeEl) {
    timeEl.textContent = getTimeDisplay()
  }
}

export function updateMoodBar() {
  const bar = document.getElementById('mood-bar')
  if (!bar) return

  // Clear existing pips
  const existing = bar.querySelectorAll('.mood-pip')
  existing.forEach(p => p.remove())

  const level = getMoodLevel()
  const type = getMoodType()

  for (let i = 10; i > 0; i--) {
    const pip = document.createElement('div')
    pip.className = 'mood-pip'
    if (i <= level) {
      pip.classList.add(type)
    }
    bar.appendChild(pip)
  }

  const moodText = document.getElementById('mood-text')
  if (moodText) {
    moodText.textContent = `MOOD: ${simState.characterMood}`
  }
}
