// mood42 - Lo-fi scene with generated artwork
import { Application, Sprite, Container, Graphics, BlurFilter, Assets } from 'pixi.js'
import gsap from 'gsap'

import { simState, cycleMood, advanceTime } from './sim/state.js'
import { initTicker, startTicker, togglePause, worldTick, updateClock, updateMoodBar } from './sim/ticker.js'
import { triggerNextEvent } from './sim/events.js'
import { showToast } from './hud/hud.js'

const app = new Application()

// Asset URLs
const ASSETS = {
  background: '/assets/scene_background.png',
  characterFocused: '/assets/character_focused.png',
  characterWithdrawn: '/assets/character_withdrawn.png',
}

// Scene elements
let background, characterFocused, characterWithdrawn
let rainContainer, rainDrops = []
let breatheTimeline

async function init() {
  await app.init({
    resizeTo: window,
    backgroundColor: 0x080810,
    antialias: true,
    resolution: Math.min(window.devicePixelRatio, 2),
    autoDensity: true,
  })

  document.getElementById('app').appendChild(app.canvas)

  // Load assets
  console.log('Loading assets...')
  await Assets.load(Object.values(ASSETS))
  console.log('Assets loaded!')

  // Create scene layers
  createBackground()
  createCharacter()
  createRain()
  createOverlays()

  // Start animation loop
  app.ticker.add(update)

  // Setup
  initTicker(() => {}, () => {
    showToast('the light\ngoes off.', 'APT ACROSS · 1:00AM · ALWAYS')
  })
  startTicker(5000)
  setupKeyboard()

  // Initial toast
  setTimeout(() => {
    showToast('apt 4F,\n2nd ave.', 'MOOD42 · WORLD RUNNING · NYC')
  }, 1000)

  setTimeout(worldTick, 1500)

  // Handle resize
  window.addEventListener('resize', handleResize)
  handleResize()
}

function createBackground() {
  background = Sprite.from(ASSETS.background)
  background.anchor.set(0.5)
  app.stage.addChild(background)
}

function createCharacter() {
  // Container for character sprites
  const characterContainer = new Container()
  characterContainer.label = 'character'
  app.stage.addChild(characterContainer)

  // Focused pose
  characterFocused = Sprite.from(ASSETS.characterFocused)
  characterFocused.anchor.set(0.5, 1) // Bottom center
  characterFocused.label = 'focused'
  characterContainer.addChild(characterFocused)

  // Withdrawn pose
  characterWithdrawn = Sprite.from(ASSETS.characterWithdrawn)
  characterWithdrawn.anchor.set(0.5, 1)
  characterWithdrawn.label = 'withdrawn'
  characterWithdrawn.alpha = 0
  characterContainer.addChild(characterWithdrawn)

  // Breathing animation
  breatheTimeline = gsap.timeline({ repeat: -1, yoyo: true })
  breatheTimeline.to([characterFocused, characterWithdrawn], {
    scaleY: 1.003,
    scaleX: 0.998,
    duration: 2,
    ease: 'sine.inOut',
  })
}

function createRain() {
  rainContainer = new Container()
  rainContainer.label = 'rain'
  app.stage.addChild(rainContainer)

  // Create rain graphics
  const rainGraphics = new Graphics()
  rainContainer.addChild(rainGraphics)

  // Initialize raindrops
  for (let i = 0; i < 300; i++) {
    rainDrops.push({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      speed: 8 + Math.random() * 12,
      length: 15 + Math.random() * 25,
      opacity: 0.1 + Math.random() * 0.3,
    })
  }
}

function createOverlays() {
  // Vignette overlay
  const vignette = new Graphics()
  vignette.label = 'vignette'
  app.stage.addChild(vignette)

  // Neon glow overlay
  const neonGlow = new Graphics()
  neonGlow.label = 'neon-glow'
  neonGlow.filters = [new BlurFilter({ strength: 40 })]
  app.stage.addChild(neonGlow)
}

function update(ticker) {
  const W = app.screen.width
  const H = app.screen.height

  // Update rain
  updateRain(W, H)

  // Update character visibility based on mood
  updateCharacterMood()

  // Update overlays
  updateOverlays(W, H)
}

function updateRain(W, H) {
  if (!simState.raining) {
    rainContainer.alpha = Math.max(0, rainContainer.alpha - 0.02)
    return
  }

  rainContainer.alpha = Math.min(simState.rainIntensity, rainContainer.alpha + 0.02)

  const rainGraphics = rainContainer.children[0]
  rainGraphics.clear()

  rainDrops.forEach(drop => {
    drop.y += drop.speed
    drop.x -= drop.speed * 0.12

    if (drop.y > H) {
      drop.y = -20
      drop.x = Math.random() * W
    }

    rainGraphics.moveTo(drop.x, drop.y)
    rainGraphics.lineTo(drop.x - drop.length * 0.12, drop.y + drop.length)
    rainGraphics.stroke({
      color: 0xa0b9dc,
      alpha: drop.opacity * simState.rainIntensity,
      width: 1,
    })
  })
}

function updateCharacterMood() {
  const mood = simState.characterMood
  const targetFocused = (mood === 'FOCUSED' || mood === 'GOOD') ? 1 : 0
  const targetWithdrawn = (mood === 'WITHDRAWN' || mood === 'ANXIOUS') ? 1 : 0

  // Smooth transition between character poses
  characterFocused.alpha += (targetFocused - characterFocused.alpha) * 0.05
  characterWithdrawn.alpha += (targetWithdrawn - characterWithdrawn.alpha) * 0.05
}

function updateOverlays(W, H) {
  // Update vignette
  const vignette = app.stage.children.find(c => c.label === 'vignette')
  if (vignette) {
    vignette.clear()
    // Dark edges
    const gradient = vignette
    gradient.rect(0, 0, W, H)
    gradient.fill({ color: 0x000000, alpha: 0 })

    // Top/bottom darkening
    for (let i = 0; i < 5; i++) {
      const alpha = 0.15 * (1 - i / 5)
      gradient.rect(0, 0, W, H * 0.1 * (5 - i) / 5)
      gradient.fill({ color: 0x000000, alpha })
      gradient.rect(0, H - H * 0.15 * (5 - i) / 5, W, H * 0.15 * (5 - i) / 5)
      gradient.fill({ color: 0x000000, alpha: alpha * 0.7 })
    }
  }

  // Update neon glow
  const neonGlow = app.stage.children.find(c => c.label === 'neon-glow')
  if (neonGlow) {
    const time = performance.now() * 0.001
    const flicker = 0.7 + 0.3 * Math.sin(time * 5)

    neonGlow.clear()
    // Red neon glow (upper right)
    neonGlow.circle(W * 0.75, H * 0.3, W * 0.15)
    neonGlow.fill({ color: 0xff4d6d, alpha: 0.08 * flicker })

    // Blue neon glow (upper left)
    neonGlow.circle(W * 0.2, H * 0.25, W * 0.12)
    neonGlow.fill({ color: 0x4d9fff, alpha: 0.06 * flicker })
  }
}

function handleResize() {
  const W = window.innerWidth
  const H = window.innerHeight

  // Scale background to cover
  if (background) {
    const bgScale = Math.max(W / background.texture.width, H / background.texture.height)
    background.scale.set(bgScale * 1.05) // Slight overscale for movement
    background.position.set(W / 2, H / 2)
  }

  // Position character
  if (characterFocused) {
    const charScale = H / characterFocused.texture.height * 0.85
    characterFocused.scale.set(charScale)
    characterFocused.position.set(W * 0.5, H * 0.95)
  }

  if (characterWithdrawn) {
    const charScale = H / characterWithdrawn.texture.height * 0.85
    characterWithdrawn.scale.set(charScale)
    characterWithdrawn.position.set(W * 0.5, H * 0.95)
  }

  // Reinit rain for new dimensions
  rainDrops.forEach(drop => {
    drop.x = Math.random() * W
    drop.y = Math.random() * H
  })
}

function setupKeyboard() {
  window.addEventListener('keydown', (e) => {
    switch (e.key.toLowerCase()) {
      case 'e':
        const evt = triggerNextEvent()
        showToast(evt.name, evt.sub)
        updateMoodBar()
        break

      case 't':
        advanceTime(60)
        if (simState.time % (24 * 60) < 60) {
          simState.oneAmLightOff = false
        }
        updateClock()
        break

      case 'r':
        simState.raining = !simState.raining
        if (simState.raining) {
          gsap.to(simState, { rainIntensity: 0.7, duration: 3 })
        } else {
          gsap.to(simState, { rainIntensity: 0, duration: 2 })
        }
        break

      case 'm':
        cycleMood()
        updateMoodBar()
        break

      case ' ':
        e.preventDefault()
        togglePause()
        break
    }
  })
}

// Start
init().catch(console.error)
