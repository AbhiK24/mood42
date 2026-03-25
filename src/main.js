// mood42 — tune in. zone out.
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
  getChannelAsset,
  VISUALS,
  CHANNEL_ASSETS,
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

// Channel color palettes for procedural backgrounds
const CHANNEL_PALETTES = {
  ch01: { primary: 0x1a1520, secondary: 0x2d2235, accent: 0xe8c89a, name: 'Late Night' },
  ch02: { primary: 0x1a1812, secondary: 0x2d2820, accent: 0x8b7355, name: 'Rain Café' },
  ch03: { primary: 0x12121a, secondary: 0x1e1e2d, accent: 0x4a4a6a, name: 'Jazz Noir' },
  ch04: { primary: 0x1a0a1a, secondary: 0x2d1030, accent: 0xff00ff, name: 'Synthwave' },
  ch05: { primary: 0x08080f, secondary: 0x0f0f1a, accent: 0x1a1a3a, name: 'Deep Space' },
  ch06: { primary: 0x1a0a12, secondary: 0x2d1520, accent: 0xff4d6d, name: 'Tokyo Drift' },
  ch07: { primary: 0x1a1810, secondary: 0x2d2818, accent: 0xffd700, name: 'Sunday Morning' },
  ch08: { primary: 0x101418, secondary: 0x182028, accent: 0x4a9fff, name: 'Focus' },
  ch09: { primary: 0x101520, secondary: 0x182030, accent: 0x6688aa, name: 'Melancholy' },
  ch10: { primary: 0x1a1208, secondary: 0x2d2010, accent: 0xffa500, name: 'Golden Hour' },
}

// Assets - legacy scenes + all channel-specific scenes
const ASSETS = {
  sceneFocused: '/assets/scene_focused.png',
  sceneWithdrawn: '/assets/scene_withdrawn.png',
  // Channel-specific assets
  ch01: '/assets/channels/ch01_late_night.png',
  ch02: '/assets/channels/ch02_rain_cafe.png',
  ch03: '/assets/channels/ch03_jazz_noir.png',
  ch04: '/assets/channels/ch04_synthwave.png',
  ch05: '/assets/channels/ch05_deep_space.png',
  ch06: '/assets/channels/ch06_tokyo_drift.png',
  ch07: '/assets/channels/ch07_sunday_morning.png',
  ch08: '/assets/channels/ch08_focus.png',
  ch09: '/assets/channels/ch09_melancholy.png',
  ch10: '/assets/channels/ch10_golden_hour.png',
}

// State
let currentView = 'wall'
let currentChannel = null
let wallContainer, channelContainer, hudContainer
let rainContainer, rainDrops = []
let particleContainer, particles = []
let musicPlaying = false
let simulationRunning = false
let useLiveLLM = false
let clockText = null

// API Key
const MOONSHOT_API_KEY = 'sk-lbkA0bF4jCQfMP41ddC9Uax6Mry5ehtRmO0dTWyFr4ASTlJL'

/**
 * Get user's local time formatted
 */
function getLocalTime() {
  const now = new Date()
  const hours = now.getHours().toString().padStart(2, '0')
  const minutes = now.getMinutes().toString().padStart(2, '0')
  return `${hours}:${minutes}`
}

/**
 * Get time period description
 */
function getTimePeriod() {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 12) return 'morning'
  if (hour >= 12 && hour < 17) return 'afternoon'
  if (hour >= 17 && hour < 21) return 'evening'
  return 'late night'
}

async function init() {
  await app.init({
    resizeTo: window,
    backgroundColor: 0x08080c,
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
  createParticles()
  createRain()
  createHUD()

  // Start with wall
  showWall()

  // Animation loop
  app.ticker.add(update)

  // Update clock every minute
  setInterval(() => {
    if (clockText && currentView === 'wall') {
      clockText.text = getLocalTime()
    }
  }, 1000)

  // Controls
  setupKeyboard()
  window.addEventListener('resize', handleResize)
  handleResize()
}

// ============ PARTICLES (ambient floating dots) ============

function createParticles() {
  particleContainer = new Container()
  particleContainer.label = 'particles'
  app.stage.addChild(particleContainer)

  for (let i = 0; i < 50; i++) {
    particles.push({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      size: 1 + Math.random() * 2,
      alpha: 0.1 + Math.random() * 0.2,
    })
  }
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

  // Gradient background
  const bg = new Graphics()
  bg.rect(0, 0, W, H)
  bg.fill({ color: 0x08080c })
  wallContainer.addChild(bg)

  // Subtle gradient overlay
  const gradientOverlay = new Graphics()
  gradientOverlay.rect(0, 0, W, H * 0.4)
  gradientOverlay.fill({ color: 0x12121a, alpha: 0.5 })
  wallContainer.addChild(gradientOverlay)

  // Header section
  const headerY = H * 0.08

  // Logo / Title
  const logo = new Text({
    text: 'mood42',
    style: {
      fontFamily: 'monospace',
      fontSize: Math.min(48, W * 0.05),
      fill: 0xffffff,
      fontWeight: 'bold',
      letterSpacing: 6,
    }
  })
  logo.x = W / 2 - logo.width / 2
  logo.y = headerY
  wallContainer.addChild(logo)

  // Tagline
  const tagline = new Text({
    text: 'tune in. zone out.',
    style: {
      fontFamily: 'monospace',
      fontSize: Math.min(14, W * 0.015),
      fill: 0x666677,
      letterSpacing: 4,
    }
  })
  tagline.x = W / 2 - tagline.width / 2
  tagline.y = headerY + logo.height + 8
  wallContainer.addChild(tagline)

  // Clock (user's local time)
  clockText = new Text({
    text: getLocalTime(),
    style: {
      fontFamily: 'monospace',
      fontSize: 12,
      fill: 0x444455,
    }
  })
  clockText.x = W - clockText.width - 30
  clockText.y = 25
  wallContainer.addChild(clockText)

  // Time period indicator
  const timePeriod = new Text({
    text: getTimePeriod(),
    style: {
      fontFamily: 'monospace',
      fontSize: 10,
      fill: 0x333344,
      letterSpacing: 2,
    }
  })
  timePeriod.x = W - timePeriod.width - 30
  timePeriod.y = 42
  wallContainer.addChild(timePeriod)

  // Channel grid - cinematic cards
  const gridStartY = H * 0.22
  const gridEndY = H * 0.85
  const gridH = gridEndY - gridStartY
  const gridW = Math.min(W * 0.92, 1400)
  const gridX = (W - gridW) / 2

  const cols = WALL_LAYOUT.cols
  const rows = WALL_LAYOUT.rows
  const gapX = Math.min(20, W * 0.015)
  const gapY = Math.min(25, H * 0.025)
  const cellW = (gridW - gapX * (cols - 1)) / cols
  const cellH = (gridH - gapY * (rows - 1)) / rows

  WALL_LAYOUT.channels.forEach((row, rowIdx) => {
    row.forEach((channelId, colIdx) => {
      const channel = getChannel(channelId)
      if (!channel) return

      const palette = CHANNEL_PALETTES[channelId]
      const x = gridX + colIdx * (cellW + gapX)
      const y = gridStartY + rowIdx * (cellH + gapY)

      // Channel card container
      const card = new Container()
      card.x = x
      card.y = y
      wallContainer.addChild(card)

      // Card background with gradient effect
      const cardBg = new Graphics()
      cardBg.roundRect(0, 0, cellW, cellH, 12)
      cardBg.fill({ color: palette.primary })
      card.addChild(cardBg)

      // Inner gradient layer
      const innerGradient = new Graphics()
      innerGradient.roundRect(0, 0, cellW, cellH * 0.6, 12)
      innerGradient.fill({ color: palette.secondary, alpha: 0.6 })
      card.addChild(innerGradient)

      // Accent glow at bottom
      const accentGlow = new Graphics()
      accentGlow.roundRect(0, cellH - 4, cellW, 4, 2)
      accentGlow.fill({ color: palette.accent })
      card.addChild(accentGlow)

      // Ambient glow effect
      const glow = new Graphics()
      glow.roundRect(0, 0, cellW, cellH, 12)
      glow.fill({ color: palette.accent, alpha: 0.03 })
      card.addChild(glow)

      // Channel number (top left, subtle)
      const chNum = new Text({
        text: channelId.replace('ch0', '').replace('ch', ''),
        style: {
          fontFamily: 'monospace',
          fontSize: Math.min(32, cellW * 0.18),
          fill: palette.accent,
          alpha: 0.15,
          fontWeight: 'bold',
        }
      })
      chNum.x = cellW - chNum.width - 12
      chNum.y = 8
      chNum.alpha = 0.2
      card.addChild(chNum)

      // Channel name
      const name = new Text({
        text: channel.name,
        style: {
          fontFamily: 'monospace',
          fontSize: Math.min(16, cellW * 0.09),
          fill: 0xffffff,
          fontWeight: 'bold',
        }
      })
      name.x = 16
      name.y = cellH * 0.35
      card.addChild(name)

      // Agent name with persona hint
      const agentName = new Text({
        text: channel.agent.name,
        style: {
          fontFamily: 'monospace',
          fontSize: Math.min(11, cellW * 0.06),
          fill: palette.accent,
        }
      })
      agentName.x = 16
      agentName.y = cellH * 0.35 + name.height + 4
      card.addChild(agentName)

      // Agent role/vibe
      const agentVibe = new Text({
        text: channel.agent.taste.slice(0, 2).join(' · '),
        style: {
          fontFamily: 'monospace',
          fontSize: Math.min(9, cellW * 0.05),
          fill: 0x555566,
        }
      })
      agentVibe.x = 16
      agentVibe.y = cellH - 28
      card.addChild(agentVibe)

      // Live indicator dot
      const liveDot = new Graphics()
      liveDot.circle(0, 0, 3)
      liveDot.fill({ color: palette.accent })
      liveDot.x = 16
      liveDot.y = 16
      card.addChild(liveDot)

      // Pulse animation on live dot
      gsap.to(liveDot, {
        alpha: 0.3,
        duration: 1.5,
        ease: 'sine.inOut',
        yoyo: true,
        repeat: -1,
      })

      // Interaction
      cardBg.eventMode = 'static'
      cardBg.cursor = 'pointer'

      cardBg.on('pointerover', () => {
        gsap.to(card.scale, { x: 1.02, y: 1.02, duration: 0.2 })
        gsap.to(glow, { alpha: 0.12, duration: 0.2 })
        gsap.to(accentGlow, { alpha: 1, duration: 0.2 })
      })

      cardBg.on('pointerout', () => {
        gsap.to(card.scale, { x: 1, y: 1, duration: 0.2 })
        gsap.to(glow, { alpha: 0.03, duration: 0.2 })
        gsap.to(accentGlow, { alpha: 1, duration: 0.2 })
      })

      cardBg.on('pointerdown', () => {
        tuneIn(channelId)
      })
    })
  })

  // Footer
  const footerText = new Text({
    text: '10 channels · 10 minds · always on',
    style: {
      fontFamily: 'monospace',
      fontSize: 11,
      fill: 0x333344,
      letterSpacing: 2,
    }
  })
  footerText.x = W / 2 - footerText.width / 2
  footerText.y = H - 50
  wallContainer.addChild(footerText)

  // Controls hint
  const controls = new Text({
    text: '[1-0] tune in · [M] music',
    style: {
      fontFamily: 'monospace',
      fontSize: 10,
      fill: 0x222233,
    }
  })
  controls.x = W / 2 - controls.width / 2
  controls.y = H - 30
  wallContainer.addChild(controls)
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
  showToast(channel.name, `${channel.agent.name.toUpperCase()} IS PROGRAMMING`)

  // Start channel programming (mock or live)
  programChannel(channelId)
}

function drawChannel() {
  if (!currentChannel) return

  const W = app.screen.width
  const H = app.screen.height
  const palette = CHANNEL_PALETTES[currentChannel.id]

  channelContainer.removeChildren()

  // Dynamic background based on channel
  const bg = new Graphics()
  bg.rect(0, 0, W, H)
  bg.fill({ color: palette.primary })
  channelContainer.addChild(bg)

  // Gradient layers for depth
  const gradLayer1 = new Graphics()
  gradLayer1.rect(0, 0, W, H * 0.5)
  gradLayer1.fill({ color: palette.secondary, alpha: 0.7 })
  channelContainer.addChild(gradLayer1)

  const gradLayer2 = new Graphics()
  gradLayer2.rect(0, H * 0.7, W, H * 0.3)
  gradLayer2.fill({ color: 0x000000, alpha: 0.5 })
  channelContainer.addChild(gradLayer2)

  // Get current visual from channel state - use channel-specific asset
  const state = getChannelState(currentChannel.id)
  const channelAsset = getChannelAsset(currentChannel.id)

  // Visual (using channel-specific scene)
  const visual = Sprite.from(channelAsset)
  visual.anchor.set(0.5)
  const scale = Math.max(W / visual.texture.width, H / visual.texture.height)
  visual.scale.set(scale * 1.05)
  visual.position.set(W / 2, H / 2)
  visual.alpha = 0.85  // Show the unique channel image more prominently
  channelContainer.addChild(visual)

  // Breathing animation
  gsap.to(visual, {
    scaleX: scale * 1.07,
    scaleY: scale * 1.06,
    duration: 6,
    ease: 'sine.inOut',
    yoyo: true,
    repeat: -1,
  })

  // Vignette overlay
  const vignette = new Graphics()
  vignette.rect(0, 0, W, H * 0.25)
  vignette.fill({ color: 0x000000, alpha: 0.7 })
  vignette.rect(0, H * 0.8, W, H * 0.2)
  vignette.fill({ color: 0x000000, alpha: 0.8 })
  channelContainer.addChild(vignette)

  // Channel info (top left)
  const chLabel = new Text({
    text: `CH ${currentChannel.id.replace('ch0', '').replace('ch', '')}`,
    style: {
      fontFamily: 'monospace',
      fontSize: 11,
      fill: palette.accent,
      letterSpacing: 2,
    }
  })
  chLabel.x = 40
  chLabel.y = 40
  channelContainer.addChild(chLabel)

  const chName = new Text({
    text: currentChannel.name.toUpperCase(),
    style: {
      fontFamily: 'monospace',
      fontSize: Math.min(36, W * 0.04),
      fill: 0xffffff,
      fontWeight: 'bold',
      letterSpacing: 4,
    }
  })
  chName.x = 40
  chName.y = 58
  channelContainer.addChild(chName)

  // Agent info
  const agentInfo = new Text({
    text: `programmed by ${currentChannel.agent.name}`,
    style: {
      fontFamily: 'monospace',
      fontSize: 12,
      fill: 0x888899,
    }
  })
  agentInfo.x = 40
  agentInfo.y = 58 + chName.height + 8
  channelContainer.addChild(agentInfo)

  // Agent persona snippet (first sentence)
  const personaSnippet = currentChannel.agent.persona.split('.')[0] + '.'
  const persona = new Text({
    text: personaSnippet,
    style: {
      fontFamily: 'monospace',
      fontSize: 10,
      fill: 0x555566,
      fontStyle: 'italic',
      wordWrap: true,
      wordWrapWidth: Math.min(W * 0.35, 450),
    }
  })
  persona.x = 40
  persona.y = 58 + chName.height + 30
  channelContainer.addChild(persona)

  // Current mood/vibe (bottom left)
  const currentMood = state?.mood || currentChannel.currentMood
  const moodText = new Text({
    text: `● ${currentMood}`,
    style: {
      fontFamily: 'monospace',
      fontSize: 14,
      fill: palette.accent,
    }
  })
  moodText.x = 40
  moodText.y = H - 100
  channelContainer.addChild(moodText)

  // Now playing (from music state)
  const musicState = getMusicState()
  if (musicState.currentTrack) {
    const nowPlaying = new Text({
      text: `♪ ${musicState.currentTrack.name}`,
      style: {
        fontFamily: 'monospace',
        fontSize: 11,
        fill: 0x888899,
      }
    })
    nowPlaying.x = 40
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
        wordWrapWidth: W * 0.4,
      }
    })
    thought.x = 40
    thought.y = H - 55
    channelContainer.addChild(thought)
  }

  // Local time display (top right)
  const timeDisplay = new Text({
    text: getLocalTime(),
    style: {
      fontFamily: 'monospace',
      fontSize: 14,
      fill: 0x444455,
    }
  })
  timeDisplay.x = W - timeDisplay.width - 40
  timeDisplay.y = 40
  channelContainer.addChild(timeDisplay)

  // Status indicator
  const status = new Text({
    text: useLiveLLM ? '● LIVE' : '○ AMBIENT',
    style: {
      fontFamily: 'monospace',
      fontSize: 10,
      fill: useLiveLLM ? palette.accent : 0x444455,
    }
  })
  status.x = W - status.width - 40
  status.y = 58
  channelContainer.addChild(status)

  // Memory stream (right side, subtle)
  const memories = getRecentMemories(currentChannel.id, 4)
  if (memories.length > 0) {
    const memoryTitle = new Text({
      text: 'MEMORY',
      style: {
        fontFamily: 'monospace',
        fontSize: 9,
        fill: 0x333344,
        letterSpacing: 2,
      }
    })
    memoryTitle.x = W - 260
    memoryTitle.y = H - 120
    channelContainer.addChild(memoryTitle)

    memories.slice().reverse().forEach((mem, i) => {
      const timeAgo = Math.floor((Date.now() - mem.timestamp) / 60000)
      const memText = new Text({
        text: `${timeAgo}m · ${mem.content.substring(0, 28)}${mem.content.length > 28 ? '...' : ''}`,
        style: {
          fontFamily: 'monospace',
          fontSize: 9,
          fill: 0x444455,
        }
      })
      memText.x = W - 260
      memText.y = H - 100 + i * 16
      channelContainer.addChild(memText)
    })
  }

  // Controls hint
  const controls = new Text({
    text: '[ESC] back · [N/P] switch · [M] music · [R] reprogram · [L] live ai',
    style: {
      fontFamily: 'monospace',
      fontSize: 10,
      fill: 0x333344,
    }
  })
  controls.x = W / 2 - controls.width / 2
  controls.y = H - 25
  channelContainer.addChild(controls)
}

async function programChannel(channelId) {
  const channel = CHANNELS[channelId]
  if (!channel) return

  const availableTracks = getTracksForChannel(channelId)
  const availableVisuals = getVisualsForChannel(channelId)

  if (useLiveLLM) {
    try {
      const decision = await generateProgrammingDecision(channelId, availableTracks, availableVisuals)

      if (decision) {
        const oldMood = channel.currentMood

        updateChannelState(channelId, {
          mood: decision.mood || oldMood,
          lastThought: decision.thought,
          musicVibe: decision.musicVibe,
          visualDesc: decision.visualDesc,
          currentVisual: decision.visualId || channel.defaultVisual,
        })

        if (decision.mood && decision.mood !== oldMood) {
          recordMoodShift(channelId, oldMood, decision.mood, decision.thought)
        }

        if (decision.trackId && TRACKS[decision.trackId]) {
          playTrack(decision.trackId)
          recordTrackPlayed(channelId, TRACKS[decision.trackId])
          musicPlaying = true
        }

        if (decision.visualId && VISUALS[decision.visualId]) {
          recordVisualShown(channelId, VISUALS[decision.visualId])
        }
      }
    } catch (err) {
      console.error('AI Programming error:', err)
      fallbackProgramming(channelId)
    }
  } else {
    fallbackProgramming(channelId)
  }

  if (currentChannel && currentChannel.id === channelId) {
    drawChannel()
  }
}

function fallbackProgramming(channelId) {
  const channel = CHANNELS[channelId]
  if (!channel) return

  const tracks = getTracksForChannel(channelId)
  const track = tracks[Math.floor(Math.random() * tracks.length)]
  if (track) {
    playTrack(track.id)
    recordTrackPlayed(channelId, track)
    musicPlaying = true
  }

  const visual = getRandomVisualForChannel(channelId)
  if (visual) {
    recordVisualShown(channelId, visual)
    updateChannelState(channelId, { currentVisual: visual.id })
  }

  const mockThoughts = [
    `Setting the mood for ${getTimePeriod()}...`,
    `${channel.agent.pacing} vibes right now.`,
    `Time for some ${channel.agent.taste[0]}.`,
    `The ${channel.currentMood} energy continues.`,
    `Let the music do the talking.`,
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

  for (let i = 0; i < 100; i++) {
    rainDrops.push({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      speed: 4 + Math.random() * 6,
      length: 8 + Math.random() * 12,
      opacity: 0.03 + Math.random() * 0.08,
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

  // Particles
  const particleGraphics = particleContainer.children[0] || new Graphics()
  if (!particleContainer.children.length) particleContainer.addChild(particleGraphics)
  particleGraphics.clear()

  particles.forEach(p => {
    p.x += p.vx
    p.y += p.vy

    if (p.x < 0) p.x = W
    if (p.x > W) p.x = 0
    if (p.y < 0) p.y = H
    if (p.y > H) p.y = 0

    particleGraphics.circle(p.x, p.y, p.size)
    particleGraphics.fill({ color: 0xffffff, alpha: p.alpha * (currentView === 'wall' ? 0.5 : 0.3) })
  })

  // Rain
  rainContainer.alpha = currentView === 'channel' ? 0.5 : 0.15
  const rainGraphics = rainContainer.children[0]
  if (rainGraphics) {
    rainGraphics.clear()

    const rainColor = currentChannel ? CHANNEL_PALETTES[currentChannel.id]?.accent || 0x6688aa : 0x6688aa

    rainDrops.forEach(drop => {
      drop.y += drop.speed
      drop.x -= drop.speed * 0.05

      if (drop.y > H) {
        drop.y = -20
        drop.x = Math.random() * W
      }

      rainGraphics.moveTo(drop.x, drop.y)
      rainGraphics.lineTo(drop.x - drop.length * 0.05, drop.y + drop.length)
      rainGraphics.stroke({ color: rainColor, alpha: drop.opacity, width: 1 })
    })
  }
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
        showToast(useLiveLLM ? 'live ai' : 'ambient mode', useLiveLLM ? 'KIMI K2 ACTIVE' : 'LOCAL MODE')
        if (useLiveLLM && currentChannel) {
          programChannel(currentChannel.id)
        }
        if (currentView === 'channel') drawChannel()
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
        if (currentView === 'channel' && currentChannel) {
          showToast('reprogramming...', `${currentChannel.agent.name.toUpperCase()} IS THINKING`)
          programChannel(currentChannel.id)
        }
        break

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

  particles.forEach(p => {
    p.x = Math.random() * W
    p.y = Math.random() * H
  })

  rainDrops.forEach(drop => {
    drop.x = Math.random() * W
    drop.y = Math.random() * H
  })
}

// Start
init().catch(console.error)
