// mood42 — agentically programmed tv
import { Application, Container, Graphics, Text, Sprite, Assets, BlurFilter } from 'pixi.js'
import gsap from 'gsap'

// Simulation imports
import { world } from './sim/world.js'
import { initSimulation } from './sim/bridge.js'
import {
  CHANNELS,
  WALL_LAYOUT,
  getAllChannels,
  getChannel,
  getChannelState,
  updateChannelState,
  initChannels,
  getAgentProgrammingPrompt,
} from './sim/channels.js'
import {
  initMusic as initMusicLib,
  toggle as toggleMusicLib,
  getState as getMusicState,
  playTrack,
  setVolume,
  getTracksForChannel,
  playChannelMusic,
  TRACKS,
} from './sim/music.js'
import {
  getVisualsForChannel,
  getRandomVisualForChannel,
  VISUALS,
} from './sim/visuals.js'
import {
  initAllChannelAgents,
  generateProgrammingDecision,
  recordTrackPlayed,
  recordVisualShown,
  recordMoodShift,
  getRecentMemories,
  getChannelHistory,
  addChannelMemory,
} from './sim/channelAgent.js'
import { callKimi } from './sim/llm.js'
import { showToast } from './hud/hud.js'

const app = new Application()

// Assets
const ASSETS = {
  sceneFocused: '/assets/scene_focused.png',
  sceneWithdrawn: '/assets/scene_withdrawn.png',
}

// State
let currentView = 'wall' // 'wall' or 'channel'
let currentChannel = null
let wallContainer, channelContainer, hudContainer
let rainContainer, rainDrops = []
let musicPlaying = false
let simulationRunning = false
let useLiveLLM = false

// API Key
const MOONSHOT_API_KEY = 'sk-lbkA0bF4jCQfMP41ddC9Uax6Mry5ehtRmO0dTWyFr4ASTlJL'

async function init() {
  await app.init({
    resizeTo: window,
    backgroundColor: 0x0a0a0f,
    antialias: true,
    resolution: Math.min(window.devicePixelRatio, 2),
    autoDensity: true,
  })

  document.getElementById('app').appendChild(app.canvas)

  // Load assets
  await Assets.load(Object.values(ASSETS))

  // Initialize systems
  initChannels()
  initAllChannelAgents()
  initMusicLib()
  initSimulation(useLiveLLM ? MOONSHOT_API_KEY : null)

  // Create views
  createWallView()
  createChannelView()
  createRain()
  createHUD()

  // Start with wall
  showWall()

  // Animation loop
  app.ticker.add(update)

  // Controls
  setupKeyboard()
  window.addEventListener('resize', handleResize)
  handleResize()

  // Welcome
  setTimeout(() => {
    showToast('mood42.tv', 'AGENTICALLY PROGRAMMED TV')
  }, 500)
}

// ============ WALL VIEW ============

function createWallView() {
  wallContainer = new Container()
  wallContainer.label = 'wall'
  app.stage.addChild(wallContainer)
}

function showWall() {
  currentView = 'wall'
  currentChannel = null
  wallContainer.visible = true
  channelContainer.visible = false
  drawWall()
}

function drawWall() {
  const W = app.screen.width
  const H = app.screen.height

  wallContainer.removeChildren()

  // Background
  const bg = new Graphics()
  bg.rect(0, 0, W, H)
  bg.fill({ color: 0x0a0a0f })
  wallContainer.addChild(bg)

  // Title
  const title = new Text({
    text: 'mood42.tv',
    style: { fontFamily: 'monospace', fontSize: 24, fill: 0x888899, letterSpacing: 4 }
  })
  title.x = W / 2 - title.width / 2
  title.y = 30
  wallContainer.addChild(title)

  const subtitle = new Text({
    text: 'agentically programmed tv',
    style: { fontFamily: 'monospace', fontSize: 12, fill: 0x555566, letterSpacing: 2 }
  })
  subtitle.x = W / 2 - subtitle.width / 2
  subtitle.y = 60
  wallContainer.addChild(subtitle)

  // Channel grid
  const gridW = Math.min(W * 0.9, 1200)
  const gridH = H * 0.65
  const gridX = (W - gridW) / 2
  const gridY = 100

  const cols = WALL_LAYOUT.cols
  const rows = WALL_LAYOUT.rows
  const gap = 15
  const cellW = (gridW - gap * (cols - 1)) / cols
  const cellH = (gridH - gap * (rows - 1)) / rows

  WALL_LAYOUT.channels.forEach((row, rowIdx) => {
    row.forEach((channelId, colIdx) => {
      const channel = getChannel(channelId)
      if (!channel) return

      const x = gridX + colIdx * (cellW + gap)
      const y = gridY + rowIdx * (cellH + gap)

      // Channel card
      const card = new Container()
      card.x = x
      card.y = y
      wallContainer.addChild(card)

      // Background
      const cardBg = new Graphics()
      cardBg.roundRect(0, 0, cellW, cellH, 8)
      cardBg.fill({ color: 0x15151f })
      card.addChild(cardBg)

      // Color accent bar
      const accent = new Graphics()
      accent.roundRect(0, 0, cellW, 4, 2)
      accent.fill({ color: channel.color })
      card.addChild(accent)

      // Glow effect (animated)
      const glow = new Graphics()
      glow.roundRect(2, 2, cellW - 4, cellH - 4, 6)
      glow.fill({ color: channel.color, alpha: 0.05 })
      card.addChild(glow)

      // Channel number
      const chNum = new Text({
        text: channelId.replace('ch', 'CH '),
        style: { fontFamily: 'monospace', fontSize: 10, fill: 0x444455 }
      })
      chNum.x = 10
      chNum.y = 12
      card.addChild(chNum)

      // Channel name
      const name = new Text({
        text: channel.name,
        style: { fontFamily: 'monospace', fontSize: 14, fill: 0xaaaaaa, fontWeight: 'bold' }
      })
      name.x = 10
      name.y = cellH / 2 - 15
      card.addChild(name)

      // Agent name
      const agent = new Text({
        text: `by ${channel.agent.name}`,
        style: { fontFamily: 'monospace', fontSize: 10, fill: 0x666677 }
      })
      agent.x = 10
      agent.y = cellH / 2 + 5
      card.addChild(agent)

      // Mood indicator
      const mood = new Text({
        text: `● ${channel.currentMood}`,
        style: { fontFamily: 'monospace', fontSize: 9, fill: channel.color }
      })
      mood.x = 10
      mood.y = cellH - 25
      card.addChild(mood)

      // Interaction
      cardBg.eventMode = 'static'
      cardBg.cursor = 'pointer'

      cardBg.on('pointerover', () => {
        gsap.to(card, { y: y - 5, duration: 0.2 })
        gsap.to(glow, { alpha: 0.15, duration: 0.2 })
      })

      cardBg.on('pointerout', () => {
        gsap.to(card, { y: y, duration: 0.2 })
        gsap.to(glow, { alpha: 0.05, duration: 0.2 })
      })

      cardBg.on('pointerdown', () => {
        tuneIn(channelId)
      })
    })
  })

  // Footer
  const footer = new Text({
    text: '[M] music · [1-0] channels · click to tune in',
    style: { fontFamily: 'monospace', fontSize: 11, fill: 0x444455 }
  })
  footer.x = W / 2 - footer.width / 2
  footer.y = H - 40
  wallContainer.addChild(footer)
}

// ============ CHANNEL VIEW ============

function createChannelView() {
  channelContainer = new Container()
  channelContainer.label = 'channel'
  channelContainer.visible = false
  app.stage.addChild(channelContainer)
}

function tuneIn(channelId) {
  const channel = getChannel(channelId)
  if (!channel) return

  currentView = 'channel'
  currentChannel = channel
  wallContainer.visible = false
  channelContainer.visible = true

  // Record tune-in as viewer interaction
  addChannelMemory(channelId, {
    type: 'viewer_interaction',
    content: 'A viewer tuned in',
    importance: 2,
  })

  drawChannel()
  showToast(channel.name, `TUNED IN · ${channel.agent.name.toUpperCase()}`)

  // Start channel programming (mock or live)
  programChannel(channelId)
}

function drawChannel() {
  if (!currentChannel) return

  const W = app.screen.width
  const H = app.screen.height

  channelContainer.removeChildren()

  // Background with channel color tint
  const bg = new Graphics()
  bg.rect(0, 0, W, H)
  bg.fill({ color: 0x080810 })
  channelContainer.addChild(bg)

  // Get current visual from channel state
  const state = getChannelState(currentChannel.id)
  const visualId = state?.currentVisual || currentChannel.defaultVisual
  const visualAsset = VISUALS[visualId]?.asset || ASSETS.sceneFocused

  // Visual (using scene assets)
  const visual = Sprite.from(visualAsset)
  visual.anchor.set(0.5)
  const scale = Math.max(W / visual.texture.width, H / visual.texture.height)
  visual.scale.set(scale * 1.05)
  visual.position.set(W / 2, H / 2)
  channelContainer.addChild(visual)

  // Breathing animation
  gsap.to(visual, {
    scaleX: scale * 1.06,
    scaleY: scale * 1.055,
    duration: 4,
    ease: 'sine.inOut',
    yoyo: true,
    repeat: -1,
  })

  // Overlay gradient
  const overlay = new Graphics()
  overlay.rect(0, 0, W, H * 0.3)
  overlay.fill({ color: 0x000000, alpha: 0.6 })
  overlay.rect(0, H * 0.75, W, H * 0.25)
  overlay.fill({ color: 0x000000, alpha: 0.7 })
  channelContainer.addChild(overlay)

  // Channel info (top left)
  const chLabel = new Text({
    text: currentChannel.id.replace('ch', 'CH '),
    style: { fontFamily: 'monospace', fontSize: 12, fill: currentChannel.color }
  })
  chLabel.x = 30
  chLabel.y = 30
  channelContainer.addChild(chLabel)

  const chName = new Text({
    text: currentChannel.name.toUpperCase(),
    style: { fontFamily: 'monospace', fontSize: 28, fill: 0xffffff, letterSpacing: 3 }
  })
  chName.x = 30
  chName.y = 50
  channelContainer.addChild(chName)

  const agentInfo = new Text({
    text: `programmed by ${currentChannel.agent.name}`,
    style: { fontFamily: 'monospace', fontSize: 11, fill: 0x888899 }
  })
  agentInfo.x = 30
  agentInfo.y = 85
  channelContainer.addChild(agentInfo)

  // Agent persona snippet
  const personaSnippet = currentChannel.agent.persona.split('.')[0] + '.'
  const persona = new Text({
    text: personaSnippet,
    style: {
      fontFamily: 'monospace',
      fontSize: 10,
      fill: 0x555566,
      fontStyle: 'italic',
      wordWrap: true,
      wordWrapWidth: Math.min(W * 0.4, 400),
    }
  })
  persona.x = 30
  persona.y = 105
  channelContainer.addChild(persona)

  // Current mood/vibe (bottom left)
  const currentMood = state?.mood || currentChannel.currentMood
  const moodText = new Text({
    text: `● ${currentMood}`,
    style: { fontFamily: 'monospace', fontSize: 14, fill: currentChannel.color }
  })
  moodText.x = 30
  moodText.y = H - 100
  channelContainer.addChild(moodText)

  // Now playing (from music state)
  const musicState = getMusicState()
  if (musicState.currentTrack) {
    const nowPlaying = new Text({
      text: `♪ ${musicState.currentTrack.name}`,
      style: { fontFamily: 'monospace', fontSize: 11, fill: 0x888899 }
    })
    nowPlaying.x = 30
    nowPlaying.y = H - 78
    channelContainer.addChild(nowPlaying)
  }

  // Agent thought (if available)
  if (state && state.lastThought) {
    const thought = new Text({
      text: `"${state.lastThought}"`,
      style: {
        fontFamily: 'monospace',
        fontSize: 12,
        fill: 0x666677,
        fontStyle: 'italic',
        wordWrap: true,
        wordWrapWidth: W * 0.5,
      }
    })
    thought.x = 30
    thought.y = H - 55
    channelContainer.addChild(thought)
  }

  // Recent memory stream (right side, subtle)
  const memories = getRecentMemories(currentChannel.id, 5)
  if (memories.length > 0) {
    const memoryTitle = new Text({
      text: 'MEMORY STREAM',
      style: { fontFamily: 'monospace', fontSize: 9, fill: 0x333344, letterSpacing: 1 }
    })
    memoryTitle.x = W - 280
    memoryTitle.y = 70
    channelContainer.addChild(memoryTitle)

    memories.slice().reverse().forEach((mem, i) => {
      const timeAgo = Math.floor((Date.now() - mem.timestamp) / 60000)
      const memText = new Text({
        text: `${timeAgo}m · ${mem.content.substring(0, 35)}${mem.content.length > 35 ? '...' : ''}`,
        style: { fontFamily: 'monospace', fontSize: 9, fill: 0x444455 }
      })
      memText.x = W - 280
      memText.y = 90 + i * 16
      channelContainer.addChild(memText)
    })
  }

  // Controls hint
  const controls = new Text({
    text: '[ESC] wall · [M] music · [N/P] channels · [L] live ai · [R] reprogram',
    style: { fontFamily: 'monospace', fontSize: 10, fill: 0x444455 }
  })
  controls.x = W - controls.width - 30
  controls.y = H - 30
  channelContainer.addChild(controls)

  // Status indicator
  const status = new Text({
    text: `${useLiveLLM ? '● LIVE' : '○ MOCK'} ${musicState.isPlaying ? '♪' : ''}`,
    style: { fontFamily: 'monospace', fontSize: 10, fill: useLiveLLM ? 0x88ff88 : 0x666666 }
  })
  status.x = W - status.width - 30
  status.y = 30
  channelContainer.addChild(status)
}

async function programChannel(channelId) {
  const channel = CHANNELS[channelId]
  if (!channel) return

  // Get available content for this channel
  const availableTracks = getTracksForChannel(channelId)
  const availableVisuals = getVisualsForChannel(channelId)

  if (useLiveLLM) {
    // Use AI to make programming decision
    try {
      const decision = await generateProgrammingDecision(
        channelId,
        availableTracks,
        availableVisuals
      )

      if (decision) {
        const oldMood = channel.currentMood

        // Update channel state
        updateChannelState(channelId, {
          mood: decision.mood || oldMood,
          lastThought: decision.thought,
          musicVibe: decision.musicVibe,
          visualDesc: decision.visualDesc,
          currentVisual: decision.visualId || channel.defaultVisual,
        })

        // Record mood shift if changed
        if (decision.mood && decision.mood !== oldMood) {
          recordMoodShift(channelId, oldMood, decision.mood, decision.thought)
        }

        // Play selected track
        if (decision.trackId && TRACKS[decision.trackId]) {
          playTrack(decision.trackId)
          recordTrackPlayed(channelId, TRACKS[decision.trackId])
        }

        // Record visual selection
        if (decision.visualId && VISUALS[decision.visualId]) {
          recordVisualShown(channelId, VISUALS[decision.visualId])
        }
      }
    } catch (err) {
      console.error('AI Programming error:', err)
      // Fallback to random selection
      fallbackProgramming(channelId)
    }
  } else {
    // Mock mode: random selection
    fallbackProgramming(channelId)
  }

  // Redraw if still on this channel
  if (currentChannel && currentChannel.id === channelId) {
    drawChannel()
  }
}

function fallbackProgramming(channelId) {
  const channel = CHANNELS[channelId]
  if (!channel) return

  // Random track selection
  const tracks = getTracksForChannel(channelId)
  const track = tracks[Math.floor(Math.random() * tracks.length)]
  if (track) {
    playTrack(track.id)
    recordTrackPlayed(channelId, track)
  }

  // Random visual selection
  const visual = getRandomVisualForChannel(channelId)
  if (visual) {
    recordVisualShown(channelId, visual)
    updateChannelState(channelId, {
      currentVisual: visual.id,
    })
  }

  // Generate a mock thought
  const mockThoughts = [
    `Setting the mood for ${channel.name}...`,
    `${channel.agent.pacing} vibes tonight.`,
    `Time for some ${channel.agent.taste[0]} sounds.`,
    `The ${channel.currentMood} energy continues.`,
  ]
  updateChannelState(channelId, {
    lastThought: mockThoughts[Math.floor(Math.random() * mockThoughts.length)],
  })
}

// ============ RAIN EFFECT ============

function createRain() {
  rainContainer = new Container()
  rainContainer.label = 'rain'
  app.stage.addChild(rainContainer)

  const rainGraphics = new Graphics()
  rainContainer.addChild(rainGraphics)

  for (let i = 0; i < 150; i++) {
    rainDrops.push({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      speed: 5 + Math.random() * 8,
      length: 10 + Math.random() * 15,
      opacity: 0.08 + Math.random() * 0.15,
    })
  }
}

// ============ HUD ============

function createHUD() {
  hudContainer = new Container()
  hudContainer.label = 'hud'
  app.stage.addChild(hudContainer)
}

// ============ UPDATE LOOP ============

function update() {
  const W = app.screen.width
  const H = app.screen.height

  // Rain
  rainContainer.alpha = currentView === 'channel' ? 0.4 : 0.2
  const rainGraphics = rainContainer.children[0]
  rainGraphics.clear()

  rainDrops.forEach(drop => {
    drop.y += drop.speed
    drop.x -= drop.speed * 0.08

    if (drop.y > H) {
      drop.y = -20
      drop.x = Math.random() * W
    }

    rainGraphics.moveTo(drop.x, drop.y)
    rainGraphics.lineTo(drop.x - drop.length * 0.08, drop.y + drop.length)
    rainGraphics.stroke({ color: 0x6688aa, alpha: drop.opacity, width: 1 })
  })
}

// ============ CONTROLS ============

function setupKeyboard() {
  window.addEventListener('keydown', (e) => {
    const channels = Object.keys(CHANNELS)

    switch (e.key) {
      case 'Escape':
        if (currentView === 'channel') showWall()
        break

      case 'm':
      case 'M':
        toggleMusicLib().then(playing => {
          musicPlaying = playing
          showToast(playing ? 'playing' : 'paused', 'MUSIC')
        })
        break

      case 'l':
      case 'L':
        useLiveLLM = !useLiveLLM
        showToast(useLiveLLM ? 'live ai' : 'mock mode', useLiveLLM ? 'KIMI K2 ACTIVE' : 'NO API CALLS')
        if (useLiveLLM && currentChannel) {
          programChannel(currentChannel.id)
        }
        break

      case 'n':
      case 'N':
        if (currentView === 'channel' && currentChannel) {
          const idx = channels.indexOf(currentChannel.id)
          const nextId = channels[(idx + 1) % channels.length]
          tuneIn(nextId)
        }
        break

      case 'p':
      case 'P':
        if (currentView === 'channel' && currentChannel) {
          const idx = channels.indexOf(currentChannel.id)
          const prevId = channels[(idx - 1 + channels.length) % channels.length]
          tuneIn(prevId)
        }
        break

      case 'r':
      case 'R':
        // Reprogram current channel
        if (currentView === 'channel' && currentChannel) {
          showToast('reprogramming...', `${currentChannel.agent.name.toUpperCase()} IS THINKING`)
          programChannel(currentChannel.id)
        }
        break

      // Number keys 1-0 for channels
      case '1': tuneIn('ch01'); break
      case '2': tuneIn('ch02'); break
      case '3': tuneIn('ch03'); break
      case '4': tuneIn('ch04'); break
      case '5': tuneIn('ch05'); break
      case '6': tuneIn('ch06'); break
      case '7': tuneIn('ch07'); break
      case '8': tuneIn('ch08'); break
      case '9': tuneIn('ch09'); break
      case '0': tuneIn('ch10'); break
    }
  })
}

function handleResize() {
  const W = window.innerWidth
  const H = window.innerHeight

  if (currentView === 'wall') {
    drawWall()
  } else {
    drawChannel()
  }

  rainDrops.forEach(drop => {
    drop.x = Math.random() * W
    drop.y = Math.random() * H
  })
}

// Start
init().catch(console.error)
