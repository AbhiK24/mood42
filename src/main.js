// mood42 - Lo-fi scene with complete artwork
import { Application, Sprite, Container, Graphics, BlurFilter, Assets } from 'pixi.js'
import gsap from 'gsap'

import { simState, cycleMood, advanceTime } from './sim/state.js'
import { initTicker, startTicker, togglePause, worldTick, updateClock, updateMoodBar } from './sim/ticker.js'
import { triggerNextEvent } from './sim/events.js'
import { showToast } from './hud/hud.js'

const app = new Application()

// Complete scene images (character already in the scene)
const ASSETS = {
  sceneFocused: '/assets/scene_focused.png',
  sceneWithdrawn: '/assets/scene_withdrawn.png',
}

// Scene elements
let sceneFocused, sceneWithdrawn
let rainContainer, rainDrops = []
let effectsContainer

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
  console.log('Loading scenes...')
  await Assets.load(Object.values(ASSETS))
  console.log('Scenes loaded!')

  // Create scene layers
  createScenes()
  createEffects()

  // Start animation loop
  app.ticker.add(update)

  // Setup simulation
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

function createScenes() {
  // Focused scene (default visible)
  sceneFocused = Sprite.from(ASSETS.sceneFocused)
  sceneFocused.anchor.set(0.5)
  sceneFocused.label = 'scene-focused'
  app.stage.addChild(sceneFocused)

  // Withdrawn scene (fades in when mood changes)
  sceneWithdrawn = Sprite.from(ASSETS.sceneWithdrawn)
  sceneWithdrawn.anchor.set(0.5)
  sceneWithdrawn.label = 'scene-withdrawn'
  sceneWithdrawn.alpha = 0
  app.stage.addChild(sceneWithdrawn)

  // Subtle breathing/sway animation on both scenes
  gsap.to([sceneFocused, sceneWithdrawn], {
    scaleX: 1.002,
    scaleY: 1.001,
    duration: 4,
    ease: 'sine.inOut',
    yoyo: true,
    repeat: -1,
  })
}

function createEffects() {
  effectsContainer = new Container()
  effectsContainer.label = 'effects'
  app.stage.addChild(effectsContainer)

  // Rain container
  rainContainer = new Container()
  rainContainer.label = 'rain'
  effectsContainer.addChild(rainContainer)

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

  // Vignette overlay
  const vignette = new Graphics()
  vignette.label = 'vignette'
  effectsContainer.addChild(vignette)

  // Neon glow overlay
  const neonGlow = new Graphics()
  neonGlow.label = 'neon-glow'
  neonGlow.filters = [new BlurFilter({ strength: 40 })]
  effectsContainer.addChild(neonGlow)
}

function update(ticker) {
  const W = app.screen.width
  const H = app.screen.height

  // Update scene visibility based on mood
  updateSceneMood()

  // Update rain
  updateRain(W, H)

  // Update overlays
  updateOverlays(W, H)
}

function updateSceneMood() {
  const mood = simState.characterMood
  const targetFocused = (mood === 'FOCUSED' || mood === 'GOOD') ? 1 : 0
  const targetWithdrawn = (mood === 'WITHDRAWN' || mood === 'ANXIOUS') ? 1 : 0

  // Smooth crossfade between scenes
  sceneFocused.alpha += (targetFocused - sceneFocused.alpha) * 0.03
  sceneWithdrawn.alpha += (targetWithdrawn - sceneWithdrawn.alpha) * 0.03
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

function updateOverlays(W, H) {
  // Update vignette
  const vignette = effectsContainer.children.find(c => c.label === 'vignette')
  if (vignette) {
    vignette.clear()
    // Dark edges for cinematic feel
    for (let i = 0; i < 5; i++) {
      const alpha = 0.12 * (1 - i / 5)
      vignette.rect(0, 0, W, H * 0.08 * (5 - i) / 5)
      vignette.fill({ color: 0x000000, alpha })
      vignette.rect(0, H - H * 0.12 * (5 - i) / 5, W, H * 0.12 * (5 - i) / 5)
      vignette.fill({ color: 0x000000, alpha: alpha * 0.7 })
    }
  }

  // Update neon glow
  const neonGlow = effectsContainer.children.find(c => c.label === 'neon-glow')
  if (neonGlow) {
    const time = performance.now() * 0.001
    const flicker = 0.7 + 0.3 * Math.sin(time * 5)

    neonGlow.clear()
    // Red neon glow (upper right)
    neonGlow.circle(W * 0.8, H * 0.25, W * 0.1)
    neonGlow.fill({ color: 0xff4d6d, alpha: 0.06 * flicker })

    // Blue neon glow (upper left)
    neonGlow.circle(W * 0.15, H * 0.2, W * 0.08)
    neonGlow.fill({ color: 0x4d9fff, alpha: 0.04 * flicker })
  }
}

function handleResize() {
  const W = window.innerWidth
  const H = window.innerHeight

  // Scale scenes to cover viewport
  const scaleScene = (sprite) => {
    if (!sprite || !sprite.texture) return
    const scale = Math.max(W / sprite.texture.width, H / sprite.texture.height)
    sprite.scale.set(scale * 1.02) // Slight overscale for animation headroom
    sprite.position.set(W / 2, H / 2)
  }

  scaleScene(sceneFocused)
  scaleScene(sceneWithdrawn)

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
