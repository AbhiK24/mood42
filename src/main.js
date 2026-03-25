// mood42 - The Building: Living apartments with AI characters
import { Application, Sprite, Container, Graphics, BlurFilter, Text, Assets } from 'pixi.js'
import gsap from 'gsap'

// Simulation imports
import {
  initSimulation,
  simulationTick,
  getBuildingView,
  getCharacterDetail,
  setActiveCharacter,
  getActiveCharacter,
  world,
  initLLM,
  // Music
  initMusic as initMusicLib,
  toggleMusic as toggleMusicLib,
  nextTrack as nextTrackLib,
  getMusicState,
  playTrack,
} from './sim/index.js'

// HUD
import { showToast } from './hud/hud.js'

const app = new Application()

// Scene assets
const ASSETS = {
  sceneFocused: '/assets/scene_focused.png',
  sceneWithdrawn: '/assets/scene_withdrawn.png',
}

// State
let currentView = 'building' // 'building' or 'apartment'
let activeApartment = null
let sceneFocused, sceneWithdrawn
let buildingContainer, apartmentContainer, hudContainer
let rainContainer, rainDrops = []
let memoryPanel, eventLog = []
let simulationRunning = false

// LLM Config - DEFAULT TO MOCK MODE IN DEV
const MOONSHOT_API_KEY = 'sk-lbkA0bF4jCQfMP41ddC9Uax6Mry5ehtRmO0dTWyFr4ASTlJL'
let useLiveLLM = false // Start with mock mode to save tokens
let autoSimulation = false // Don't auto-start simulation

// Music state (managed by sim/music.js)
let musicPlaying = false

async function init() {
  await app.init({
    resizeTo: window,
    backgroundColor: 0x0a0a12,
    antialias: true,
    resolution: Math.min(window.devicePixelRatio, 2),
    autoDensity: true,
  })

  document.getElementById('app').appendChild(app.canvas)

  // Load assets
  console.log('Loading assets...')
  await Assets.load(Object.values(ASSETS))

  // Initialize simulation - mock mode by default (no API calls)
  initSimulation(useLiveLLM ? MOONSHOT_API_KEY : null)

  // Create layers
  createBuildingView()
  createApartmentView()
  createHUD()
  createRain()

  // Start in building view
  showBuildingView()

  // Animation loop
  app.ticker.add(update)

  // Keyboard controls
  setupKeyboard()

  // Handle resize
  window.addEventListener('resize', handleResize)
  handleResize()

  // Initialize music library
  initMusicLib()

  // Initial toast
  setTimeout(() => {
    showToast('the building', '11 PM · NYC · RAINING')
    addEvent('You approach the building on 2nd Avenue...')
    addEvent('[S] sim · [L] llm · [M] music · [N] next track')
  }, 500)

  // DON'T auto-start simulation - wait for user to press S
  // This saves API tokens during development
}

function toggleMusic() {
  toggleMusicLib().then(playing => {
    musicPlaying = playing
    const state = getMusicState()
    if (playing && state.currentTrack) {
      addEvent(`Playing: ${state.currentTrack.name}`)
    } else {
      addEvent('Music paused')
    }
  }).catch(() => {
    addEvent('Click anywhere first to enable audio')
  })
}

function nextTrack() {
  nextTrackLib().then(() => {
    const state = getMusicState()
    if (state.currentTrack) {
      addEvent(`Now playing: ${state.currentTrack.name}`)
    }
  })
}

function createBuildingView() {
  buildingContainer = new Container()
  buildingContainer.label = 'building'
  app.stage.addChild(buildingContainer)

  // Building background
  const buildingBg = new Graphics()
  buildingBg.label = 'building-bg'
  buildingContainer.addChild(buildingBg)

  // Windows container
  const windowsContainer = new Container()
  windowsContainer.label = 'windows'
  buildingContainer.addChild(windowsContainer)
}

function createApartmentView() {
  apartmentContainer = new Container()
  apartmentContainer.label = 'apartment'
  apartmentContainer.visible = false
  app.stage.addChild(apartmentContainer)

  // Scene sprites
  sceneFocused = Sprite.from(ASSETS.sceneFocused)
  sceneFocused.anchor.set(0.5)
  apartmentContainer.addChild(sceneFocused)

  sceneWithdrawn = Sprite.from(ASSETS.sceneWithdrawn)
  sceneWithdrawn.anchor.set(0.5)
  sceneWithdrawn.alpha = 0
  apartmentContainer.addChild(sceneWithdrawn)

  // Breathing animation
  gsap.to([sceneFocused, sceneWithdrawn], {
    scaleX: 1.008,
    scaleY: 1.005,
    duration: 3.5,
    ease: 'sine.inOut',
    yoyo: true,
    repeat: -1,
  })
}

function createHUD() {
  hudContainer = new Container()
  hudContainer.label = 'hud'
  app.stage.addChild(hudContainer)

  // Memory panel (right side)
  memoryPanel = new Container()
  memoryPanel.label = 'memory-panel'
  hudContainer.addChild(memoryPanel)
}

function createRain() {
  rainContainer = new Container()
  rainContainer.label = 'rain'
  app.stage.addChild(rainContainer)

  const rainGraphics = new Graphics()
  rainContainer.addChild(rainGraphics)

  for (let i = 0; i < 200; i++) {
    rainDrops.push({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      speed: 6 + Math.random() * 10,
      length: 12 + Math.random() * 20,
      opacity: 0.1 + Math.random() * 0.25,
    })
  }
}

function showBuildingView() {
  currentView = 'building'
  buildingContainer.visible = true
  apartmentContainer.visible = false
  drawBuilding()
}

function showApartmentView(apartment) {
  currentView = 'apartment'
  activeApartment = apartment
  buildingContainer.visible = false
  apartmentContainer.visible = true

  // Set active character in simulation
  const charMap = { '3B': 'maya_3b', '2A': 'daniel_2a', '4C': 'iris_4c' }
  if (charMap[apartment]) {
    setActiveCharacter(charMap[apartment])
    const char = getActiveCharacter()
    if (char) {
      showToast(`apt ${apartment}`, `${char.name.toUpperCase()} · ${char.state.mood.toUpperCase()}`)
      addEvent(`You peer into ${char.name}'s window...`)
    }
  }

  handleResize()
}

function drawBuilding() {
  const W = app.screen.width
  const H = app.screen.height

  const buildingBg = buildingContainer.children.find(c => c.label === 'building-bg')
  const windowsContainer = buildingContainer.children.find(c => c.label === 'windows')

  // Clear previous
  buildingBg.clear()
  windowsContainer.removeChildren()

  // Building dimensions
  const buildingWidth = Math.min(W * 0.6, 500)
  const buildingHeight = H * 0.75
  const buildingX = (W - buildingWidth) / 2
  const buildingY = H * 0.12

  // Building facade
  buildingBg.rect(buildingX - 20, buildingY - 20, buildingWidth + 40, buildingHeight + 40)
  buildingBg.fill({ color: 0x1a1a24 })

  buildingBg.rect(buildingX, buildingY, buildingWidth, buildingHeight)
  buildingBg.fill({ color: 0x12121a })

  // Get building state
  const buildingView = getBuildingView()

  // Window layout
  const floors = [
    { y: 0, apartments: ['4A', '4B', '4C'] },
    { y: 1, apartments: ['3A', '3B', '3C'] },
    { y: 2, apartments: ['2A', '2B', '2C'] },
  ]

  const windowWidth = buildingWidth * 0.25
  const windowHeight = buildingHeight * 0.22
  const gapX = (buildingWidth - windowWidth * 3) / 4
  const gapY = (buildingHeight - windowHeight * 3) / 4

  floors.forEach((floor, floorIdx) => {
    floor.apartments.forEach((apt, aptIdx) => {
      const wx = buildingX + gapX + aptIdx * (windowWidth + gapX)
      const wy = buildingY + gapY + floorIdx * (windowHeight + gapY)

      // Find if this apartment is occupied
      const occupied = ['3B', '2A', '4C'].includes(apt)
      const charMap = { '3B': 'maya_3b', '2A': 'daniel_2a', '4C': 'iris_4c' }
      const charId = charMap[apt]
      const char = charId ? world.characters.get(charId) : null

      // Window frame
      const windowG = new Graphics()
      windowG.rect(wx, wy, windowWidth, windowHeight)
      windowG.fill({ color: 0x0a0a10 })

      // Window glow if occupied and lit
      if (char && char.state.energy > 0.2) {
        const glowColor = char.state.mood === 'focused' ? 0xe8c89a :
                          char.state.mood === 'anxious' ? 0x8888ff :
                          char.state.mood === 'lonely' ? 0x6688aa : 0xccaa77

        // Inner glow
        windowG.rect(wx + 4, wy + 4, windowWidth - 8, windowHeight - 8)
        windowG.fill({ color: glowColor, alpha: 0.3 + char.state.energy * 0.3 })

        // Silhouette hint
        const silhouette = new Graphics()
        silhouette.circle(wx + windowWidth / 2, wy + windowHeight * 0.6, windowWidth * 0.15)
        silhouette.fill({ color: 0x000000, alpha: 0.4 })
        windowsContainer.addChild(silhouette)
      }

      windowsContainer.addChild(windowG)

      // Label
      const label = new Text({
        text: apt,
        style: {
          fontFamily: 'monospace',
          fontSize: 12,
          fill: occupied ? 0x888899 : 0x444455,
        }
      })
      label.x = wx + 6
      label.y = wy + 6
      windowsContainer.addChild(label)

      // Character name if occupied
      if (char) {
        const nameLabel = new Text({
          text: char.name.toLowerCase(),
          style: {
            fontFamily: 'monospace',
            fontSize: 10,
            fill: 0x666677,
          }
        })
        nameLabel.x = wx + 6
        nameLabel.y = wy + windowHeight - 18
        windowsContainer.addChild(nameLabel)
      }

      // Click handler
      if (occupied) {
        windowG.eventMode = 'static'
        windowG.cursor = 'pointer'
        windowG.on('pointerdown', () => {
          showApartmentView(apt)
        })
      }
    })
  })

  // Building address
  const address = new Text({
    text: '127 2ND AVE',
    style: {
      fontFamily: 'monospace',
      fontSize: 14,
      fill: 0x555566,
      letterSpacing: 2,
    }
  })
  address.x = buildingX
  address.y = buildingY + buildingHeight + 15
  windowsContainer.addChild(address)
}

function update() {
  const W = app.screen.width
  const H = app.screen.height

  // Update rain
  updateRain(W, H)

  // Update apartment view if active
  if (currentView === 'apartment') {
    updateApartmentView()
  }

  // Update memory panel
  updateMemoryPanel()
}

function updateRain(W, H) {
  rainContainer.alpha = 0.6

  const rainGraphics = rainContainer.children[0]
  rainGraphics.clear()

  rainDrops.forEach(drop => {
    drop.y += drop.speed
    drop.x -= drop.speed * 0.1

    if (drop.y > H) {
      drop.y = -20
      drop.x = Math.random() * W
    }

    rainGraphics.moveTo(drop.x, drop.y)
    rainGraphics.lineTo(drop.x - drop.length * 0.1, drop.y + drop.length)
    rainGraphics.stroke({
      color: 0x8899bb,
      alpha: drop.opacity,
      width: 1,
    })
  })
}

function updateApartmentView() {
  const char = getActiveCharacter()
  if (!char) return

  // Crossfade based on mood
  const isFocused = char.state.mood === 'focused' || char.state.mood === 'content'
  const targetFocused = isFocused ? 1 : 0
  const targetWithdrawn = isFocused ? 0 : 1

  sceneFocused.alpha += (targetFocused - sceneFocused.alpha) * 0.03
  sceneWithdrawn.alpha += (targetWithdrawn - sceneWithdrawn.alpha) * 0.03
}

function updateMemoryPanel() {
  const W = app.screen.width
  const H = app.screen.height

  memoryPanel.removeChildren()

  // Background
  const panelBg = new Graphics()
  panelBg.rect(W - 320, 0, 320, H)
  panelBg.fill({ color: 0x000000, alpha: 0.7 })
  memoryPanel.addChild(panelBg)

  // Title
  let y = 20
  const title = new Text({
    text: currentView === 'building' ? 'THE BUILDING' : `APT ${activeApartment}`,
    style: { fontFamily: 'monospace', fontSize: 14, fill: 0x888899, letterSpacing: 2 }
  })
  title.x = W - 300
  title.y = y
  memoryPanel.addChild(title)
  y += 30

  // Time
  const timeText = new Text({
    text: `${formatTime(world.timeOfDay)} · DAY ${world.day}`,
    style: { fontFamily: 'monospace', fontSize: 12, fill: 0x666677 }
  })
  timeText.x = W - 300
  timeText.y = y
  memoryPanel.addChild(timeText)
  y += 40

  // Character info if in apartment
  if (currentView === 'apartment') {
    const char = getActiveCharacter()
    if (char) {
      // Name and mood
      const charInfo = new Text({
        text: `${char.name.toUpperCase()}\n${char.state.mood} · ${Math.round(char.state.energy * 100)}% energy`,
        style: { fontFamily: 'monospace', fontSize: 12, fill: 0xaaaaaa, lineHeight: 18 }
      })
      charInfo.x = W - 300
      charInfo.y = y
      memoryPanel.addChild(charInfo)
      y += 50

      // Current action
      if (char.state.currentAction) {
        const action = new Text({
          text: `→ ${char.state.currentAction}`,
          style: { fontFamily: 'monospace', fontSize: 11, fill: 0x88aa88, wordWrap: true, wordWrapWidth: 280 }
        })
        action.x = W - 300
        action.y = y
        memoryPanel.addChild(action)
        y += 30
      }

      // Recent memories
      const memTitle = new Text({
        text: 'MEMORIES',
        style: { fontFamily: 'monospace', fontSize: 10, fill: 0x555566, letterSpacing: 1 }
      })
      memTitle.x = W - 300
      memTitle.y = y
      memoryPanel.addChild(memTitle)
      y += 20

      const recentMems = char.memories.slice(-6).reverse()
      recentMems.forEach(mem => {
        const memText = new Text({
          text: `· ${mem.text}`,
          style: {
            fontFamily: 'monospace',
            fontSize: 10,
            fill: mem.type === 'reflection' ? 0xaaaacc : 0x777788,
            wordWrap: true,
            wordWrapWidth: 280,
          }
        })
        memText.x = W - 300
        memText.y = y
        memoryPanel.addChild(memText)
        y += memText.height + 8
      })
    }
  }

  // Event log at bottom
  y = H - 180
  const logTitle = new Text({
    text: 'EVENTS',
    style: { fontFamily: 'monospace', fontSize: 10, fill: 0x555566, letterSpacing: 1 }
  })
  logTitle.x = W - 300
  logTitle.y = y
  memoryPanel.addChild(logTitle)
  y += 20

  eventLog.slice(-5).forEach(evt => {
    const evtText = new Text({
      text: evt,
      style: { fontFamily: 'monospace', fontSize: 10, fill: 0x666677, wordWrap: true, wordWrapWidth: 280 }
    })
    evtText.x = W - 300
    evtText.y = y
    memoryPanel.addChild(evtText)
    y += evtText.height + 6
  })

  // Controls hint
  const controlsText = `[S] sim · [M] music · [L] llm · ${currentView === 'apartment' ? '[ESC] back' : '[1-3] enter'}`

  const controls = new Text({
    text: controlsText,
    style: { fontFamily: 'monospace', fontSize: 10, fill: 0x444455 }
  })
  controls.x = W - 300
  controls.y = H - 30
  memoryPanel.addChild(controls)

  // Status indicators
  const llmStatus = new Text({
    text: `${useLiveLLM ? '● LIVE' : '○ MOCK'} ${simulationRunning ? '▶ SIM' : '■ STOP'} ${musicPlaying ? '♪ MUSIC' : '♪ -'}`,
    style: { fontFamily: 'monospace', fontSize: 9, fill: useLiveLLM ? 0x88ff88 : 0x888888 }
  })
  llmStatus.x = W - 300
  llmStatus.y = H - 45
  memoryPanel.addChild(llmStatus)
}

function addEvent(text) {
  const time = formatTime(world.timeOfDay)
  eventLog.push(`[${time}] ${text}`)
  if (eventLog.length > 20) eventLog.shift()
}

function formatTime(minutes) {
  const h = Math.floor(minutes / 60) % 24
  const m = minutes % 60
  const period = h >= 12 ? 'PM' : 'AM'
  const h12 = h % 12 || 12
  return `${h12}:${m.toString().padStart(2, '0')} ${period}`
}

function startSimulation() {
  simulationRunning = true
  addEvent(`Simulation started (${useLiveLLM ? 'LIVE LLM' : 'MOCK MODE'})`)
  runSimulationLoop()
}

async function runSimulationLoop() {
  if (!simulationRunning) return

  try {
    const state = await simulationTick({ verbose: false })

    // Check for new memories/events
    for (const [id, char] of world.characters) {
      const lastMem = char.memories[char.memories.length - 1]
      if (lastMem && lastMem.tick === world.tick) {
        if (lastMem.type === 'reflection') {
          addEvent(`${char.name} reflects: "${lastMem.text.slice(0, 60)}..."`)
        } else if (lastMem.type === 'dialogue') {
          addEvent(`${char.name}: ${lastMem.text.slice(0, 50)}...`)
        }
      }
    }

    // Redraw building if in building view
    if (currentView === 'building') {
      drawBuilding()
    }
  } catch (err) {
    console.error('Tick error:', err)
    addEvent(`Error: ${err.message}`)
  }

  // Next tick (only if still running)
  if (simulationRunning) {
    setTimeout(runSimulationLoop, 3000)
  }
}

function handleResize() {
  const W = window.innerWidth
  const H = window.innerHeight

  if (currentView === 'building') {
    drawBuilding()
  } else {
    // Scale apartment scenes
    const scaleScene = (sprite) => {
      if (!sprite?.texture) return
      const scale = Math.max((W - 320) / sprite.texture.width, H / sprite.texture.height)
      sprite.scale.set(scale * 1.02)
      sprite.position.set((W - 320) / 2, H / 2)
    }
    scaleScene(sceneFocused)
    scaleScene(sceneWithdrawn)
  }

  // Reset rain
  rainDrops.forEach(drop => {
    drop.x = Math.random() * W
    drop.y = Math.random() * H
  })
}

function setupKeyboard() {
  window.addEventListener('keydown', (e) => {
    switch (e.key) {
      case 'Escape':
        if (currentView === 'apartment') {
          showBuildingView()
          showToast('the building', 'NYC · RAINING')
        }
        break

      case 's':
      case 'S':
        // Toggle simulation on/off
        if (simulationRunning) {
          simulationRunning = false
          addEvent('Simulation STOPPED')
          showToast('paused', 'SIMULATION STOPPED')
        } else {
          startSimulation()
          showToast('running', useLiveLLM ? 'LIVE LLM MODE' : 'MOCK MODE')
        }
        break

      case 'l':
      case 'L':
        // Toggle live LLM mode
        useLiveLLM = !useLiveLLM
        // Reinitialize with new mode
        initSimulation(useLiveLLM ? MOONSHOT_API_KEY : null)
        addEvent(`LLM mode: ${useLiveLLM ? 'LIVE (uses tokens)' : 'MOCK (free)'}`)
        showToast(useLiveLLM ? 'live llm' : 'mock mode', useLiveLLM ? 'KIMI K2 · USES TOKENS' : 'NO API CALLS')
        break

      case ' ':
        e.preventDefault()
        // Pause/resume (only if already running)
        if (simulationRunning) {
          simulationRunning = false
          addEvent('Paused')
        } else if (eventLog.some(e => e.includes('Simulation started'))) {
          // Only resume if previously started
          simulationRunning = true
          addEvent('Resumed')
          runSimulationLoop()
        }
        break

      case 't':
      case 'T':
        // Advance time by 1 hour (12 ticks) - uses current LLM mode
        addEvent('Advancing 1 hour...')
        for (let i = 0; i < 12; i++) {
          simulationTick({ verbose: false })
        }
        addEvent('Time advanced 1 hour')
        if (currentView === 'building') drawBuilding()
        break

      case 'm':
      case 'M':
        toggleMusic()
        break

      case 'n':
      case 'N':
        nextTrack()
        break

      case '1':
        showApartmentView('2A') // Daniel
        break
      case '2':
        showApartmentView('3B') // Maya
        break
      case '3':
        showApartmentView('4C') // Iris
        break
    }
  })

  // Enable audio on first click (browser autoplay policy)
  document.addEventListener('click', () => {
    if (musicPlaying) {
      toggleMusicLib().catch(() => {})
    }
  }, { once: true })
}

// Start
init().catch(console.error)
