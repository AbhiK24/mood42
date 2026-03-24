// HUD management for mood42

import { simState, getTimeDisplay, getMoodLevel, getMoodType } from '../sim/state.js'

export function showToast(title, sub) {
  const toast = document.getElementById('event-toast')
  const titleEl = document.getElementById('toast-title')
  const subEl = document.getElementById('toast-sub')

  if (toast && titleEl && subEl) {
    titleEl.textContent = title
    subEl.textContent = sub
    toast.classList.add('show')
    setTimeout(() => toast.classList.remove('show'), 3500)
  }
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

export function initHUD() {
  updateClock()
  updateMoodBar()
}
