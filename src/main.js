// Main entry point for mood42

import { Application } from 'pixi.js'
import gsap from 'gsap'

import { simState, cycleMood, advanceTime } from './sim/state.js'
import { initTicker, startTicker, togglePause, worldTick, updateClock, updateMoodBar } from './sim/ticker.js'
import { triggerNextEvent } from './sim/events.js'
import { showToast, initHUD } from './hud/hud.js'

import { Sky, Rain, Condensation } from './scene/sky.js'
import { WindowFrame } from './scene/window.js'
import { Room, Desk, DeskObjects, Plant, Steam } from './scene/room.js'
import { Character } from './scene/character.js'
import { NeonLighting, LampLight, CandleLight, ScreenGlow } from './scene/lighting.js'

// Initialize Pixi Application
const app = new Application()

async function init() {
  await app.init({
    resizeTo: window,
    backgroundColor: 0x080810,
    antialias: true,
    resolution: Math.min(window.devicePixelRatio, 2),
    autoDensity: true,
  })

  document.getElementById('app').appendChild(app.canvas)

  // Create scene layers (back to front)
  const sky = new Sky(app)
  const rain = new Rain(app)
  const condensation = new Condensation(app)
  const neonLighting = new NeonLighting(app)
  const windowFrame = new WindowFrame(app)
  const room = new Room(app)
  const plant = new Plant(app)
  const lampLight = new LampLight(app)
  const screenGlow = new ScreenGlow(app)
  const desk = new Desk(app)
  const deskObjects = new DeskObjects(app)
  const candleLight = new CandleLight(app)
  const character = new Character(app)
  const steam = new Steam(app)

  // Add to stage in order
  app.stage.addChild(sky.container)
  app.stage.addChild(rain.container)
  app.stage.addChild(neonLighting.container)
  app.stage.addChild(condensation.container)
  app.stage.addChild(windowFrame.container)
  app.stage.addChild(room.container)
  app.stage.addChild(plant.container)
  app.stage.addChild(lampLight.container)
  app.stage.addChild(screenGlow.container)
  app.stage.addChild(desk.container)
  app.stage.addChild(deskObjects.container)
  app.stage.addChild(candleLight.container)
  app.stage.addChild(character.container)
  app.stage.addChild(steam.container)

  // Initial draw
  sky.draw()
  windowFrame.draw()
  room.draw()
  plant.draw()
  lampLight.draw()
  desk.draw()
  deskObjects.draw()
  condensation.draw()

  // Resize handler
  const handleResize = () => {
    sky.resize()
    rain.resize()
    condensation.resize()
    windowFrame.resize()
    room.resize()
    plant.resize()
    lampLight.resize()
    desk.resize()
    deskObjects.resize()
    character.resize()
    steam.resize()
  }

  window.addEventListener('resize', handleResize)

  // Animation loop
  let lastMood = simState.characterMood

  app.ticker.add((ticker) => {
    const time = performance.now()

    // Update all animated elements
    sky.update(time)
    rain.update()
    neonLighting.update(time)
    plant.update(time)
    lampLight.update()
    screenGlow.update()
    deskObjects.update()
    candleLight.update(time)
    character.update(time)
    steam.update()

    // Check for mood changes
    if (lastMood !== simState.characterMood) {
      character.updateMoodAnimation()
      lastMood = simState.characterMood
    }
  })

  // Initialize HUD
  initHUD()

  // Initialize ticker
  initTicker(
    (tick) => {
      // On tick callback
    },
    () => {
      // On 1am callback
      showToast('the light\ngoes off.', 'APT ACROSS · 1:00AM · ALWAYS')
    }
  )

  // Start world tick
  startTicker(5000)

  // Initial toast
  setTimeout(() => {
    showToast('apt 4F,\n2nd ave.', 'MOOD42 · WORLD RUNNING · NYC')
  }, 1000)

  // First tick
  setTimeout(worldTick, 1500)

  // Keyboard controls
  setupKeyboardControls(character)
}

function setupKeyboardControls(character) {
  window.addEventListener('keydown', (e) => {
    switch (e.key.toLowerCase()) {
      case 'e':
        // Trigger event
        const evt = triggerNextEvent()
        showToast(evt.name, evt.sub)
        character.updateMoodAnimation()
        updateMoodBar()
        break

      case 't':
        // Advance time by 1 hour
        advanceTime(60)
        // Reset 1am light if we go past midnight
        if (simState.time % (24 * 60) < 60) {
          simState.oneAmLightOff = false
        }
        updateClock()
        break

      case 'r':
        // Toggle rain
        simState.raining = !simState.raining
        if (simState.raining) {
          gsap.to(simState, { rainIntensity: 0.7, duration: 3, ease: 'sine.inOut' })
        } else {
          gsap.to(simState, { rainIntensity: 0, duration: 2, ease: 'sine.out' })
        }
        break

      case 'm':
        // Cycle mood
        cycleMood()
        character.updateMoodAnimation()
        updateMoodBar()
        break

      case ' ':
        // Pause/resume
        e.preventDefault()
        togglePause()
        break
    }
  })
}

// Start the app
init().catch(console.error)
