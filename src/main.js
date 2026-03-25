// mood42 — tune in. zone out.
// Infinite drag canvas with animated channel previews

import { Application, Container, Graphics, Text, Sprite, Assets, BlurFilter, DisplacementFilter } from 'pixi.js'
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

// Channel color palettes
const CHANNEL_PALETTES = {
  ch01: { primary: 0x1a1520, secondary: 0x2d2235, accent: 0xe8c89a, glow: '#e8c89a', name: 'Late Night' },
  ch02: { primary: 0x1a1812, secondary: 0x2d2820, accent: 0x8b7355, glow: '#8b7355', name: 'Rain Café' },
  ch03: { primary: 0x12121a, secondary: 0x1e1e2d, accent: 0x4a4a6a, glow: '#6a6a9a', name: 'Jazz Noir' },
  ch04: { primary: 0x1a0a1a, secondary: 0x2d1030, accent: 0xff00ff, glow: '#ff00ff', name: 'Synthwave' },
  ch05: { primary: 0x08080f, secondary: 0x0f0f1a, accent: 0x3a3a8a, glow: '#5a5aba', name: 'Deep Space' },
  ch06: { primary: 0x1a0a12, secondary: 0x2d1520, accent: 0xff4d6d, glow: '#ff4d6d', name: 'Tokyo Drift' },
  ch07: { primary: 0x1a1810, secondary: 0x2d2818, accent: 0xffd700, glow: '#ffd700', name: 'Sunday Morning' },
  ch08: { primary: 0x101418, secondary: 0x182028, accent: 0x4a9fff, glow: '#4a9fff', name: 'Focus' },
  ch09: { primary: 0x101520, secondary: 0x182030, accent: 0x6688aa, glow: '#6688aa', name: 'Melancholy' },
  ch10: { primary: 0x1a1208, secondary: 0x2d2010, accent: 0xffa500, glow: '#ffa500', name: 'Golden Hour' },
}

// Assets
const ASSETS = {
  sceneFocused: '/assets/scene_focused.png',
  sceneWithdrawn: '/assets/scene_withdrawn.png',
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
let worldContainer, wallContainer, channelContainer
let channelCards = []
let particleContainer, particles = []
let musicPlaying = false
let useLiveLLM = false

// Drag state for infinite canvas
let isDragging = false
let dragStartX = 0
let dragStartY = 0
let worldOffsetX = 0
let worldOffsetY = 0
let targetOffsetX = 0
let targetOffsetY = 0
let velocityX = 0
let velocityY = 0
let lastDragX = 0
let lastDragY = 0

// Canvas dimensions (much larger than viewport for infinite feel)
const WORLD_WIDTH = 4000
const WORLD_HEIGHT = 3000

// Channel card positions - scattered artistic layout
const CARD_POSITIONS = [
  { x: 0.15, y: 0.18, scale: 1.1, rotation: -2 },
  { x: 0.45, y: 0.12, scale: 0.95, rotation: 1.5 },
  { x: 0.75, y: 0.22, scale: 1.0, rotation: -1 },
  { x: 0.25, y: 0.45, scale: 1.15, rotation: 2 },
  { x: 0.55, y: 0.38, scale: 1.05, rotation: -2.5 },
  { x: 0.85, y: 0.48, scale: 0.9, rotation: 1 },
  { x: 0.12, y: 0.72, scale: 1.0, rotation: -1.5 },
  { x: 0.42, y: 0.68, scale: 1.1, rotation: 2.5 },
  { x: 0.72, y: 0.75, scale: 0.95, rotation: -1 },
  { x: 0.92, y: 0.82, scale: 1.0, rotation: 1.5 },
]

// API Key
const MOONSHOT_API_KEY = 'sk-lbkA0bF4jCQfMP41ddC9Uax6Mry5ehtRmO0dTWyFr4ASTlJL'

/**
 * Get user's local time
 */
function getLocalTime() {
  const now = new Date()
  return now.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: false })
}

/**
 * Get time period
 */
function getTimePeriod() {
  const hour = new Date().getHours()
  if (hour >= 5 && hour < 12) return 'morning broadcast'
  if (hour >= 12 && hour < 17) return 'afternoon session'
  if (hour >= 17 && hour < 21) return 'evening programming'
  return 'late night stream'
}

/**
 * Update HTML clock elements
 */
function updateHTMLClock() {
  const clockEl = document.getElementById('clock')
  const periodEl = document.getElementById('time-period')
  if (clockEl) clockEl.textContent = getLocalTime()
  if (periodEl) periodEl.textContent = getTimePeriod()
}

async function init() {
  await app.init({
    resizeTo: window,
    backgroundColor: 0x0a0a0c,
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
  createInfiniteCanvas()
  createChannelView()
  createAmbientParticles()

  // Start with wall
  showWall()

  // Animation loop
  app.ticker.add(update)

  // Update clock
  updateHTMLClock()
  setInterval(updateHTMLClock, 1000)

  // Setup interactions
  setupDragInteraction()
  setupKeyboard()
  window.addEventListener('resize', handleResize)
  handleResize()
}

// ============ AMBIENT PARTICLES ============

function createAmbientParticles() {
  particleContainer = new Container()
  particleContainer.label = 'particles'
  app.stage.addChild(particleContainer)

  for (let i = 0; i < 80; i++) {
    particles.push({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      vx: (Math.random() - 0.5) * 0.2,
      vy: (Math.random() - 0.5) * 0.15,
      size: 0.5 + Math.random() * 1.5,
      alpha: 0.05 + Math.random() * 0.1,
      pulse: Math.random() * Math.PI * 2,
    })
  }
}

// ============ INFINITE CANVAS ============

function createInfiniteCanvas() {
  // World container that moves with drag
  worldContainer = new Container()
  worldContainer.label = 'world'
  app.stage.addChild(worldContainer)

  // Wall container inside world
  wallContainer = new Container()
  wallContainer.label = 'wall'
  worldContainer.addChild(wallContainer)

  // Center the world initially
  worldOffsetX = (window.innerWidth - WORLD_WIDTH) / 2
  worldOffsetY = (window.innerHeight - WORLD_HEIGHT) / 2
  targetOffsetX = worldOffsetX
  targetOffsetY = worldOffsetY
}

function showWall() {
  currentView = 'wall'
  currentChannel = null
  worldContainer.visible = true
  if (channelContainer) channelContainer.visible = false
  drawInfiniteWall()
}

function drawInfiniteWall() {
  wallContainer.removeChildren()
  channelCards = []

  // Large world background
  const bg = new Graphics()
  bg.rect(0, 0, WORLD_WIDTH, WORLD_HEIGHT)
  bg.fill({ color: 0x0a0a0c })
  wallContainer.addChild(bg)

  // Subtle grid pattern
  const grid = new Graphics()
  const gridSize = 100
  for (let x = 0; x < WORLD_WIDTH; x += gridSize) {
    grid.moveTo(x, 0)
    grid.lineTo(x, WORLD_HEIGHT)
    grid.stroke({ color: 0x151518, width: 1 })
  }
  for (let y = 0; y < WORLD_HEIGHT; y += gridSize) {
    grid.moveTo(0, y)
    grid.lineTo(WORLD_WIDTH, y)
    grid.stroke({ color: 0x151518, width: 1 })
  }
  wallContainer.addChild(grid)

  // Create channel cards with scattered positions
  const channels = Object.keys(CHANNELS)
  channels.forEach((channelId, index) => {
    const channel = getChannel(channelId)
    if (!channel) return

    const pos = CARD_POSITIONS[index]
    const x = pos.x * WORLD_WIDTH
    const y = pos.y * WORLD_HEIGHT

    createChannelCard(channel, x, y, pos.scale, pos.rotation, index)
  })
}

function createChannelCard(channel, x, y, scale, rotation, index) {
  const palette = CHANNEL_PALETTES[channel.id]
  const cardWidth = 320
  const cardHeight = 200

  const card = new Container()
  card.x = x
  card.y = y
  card.scale.set(scale)
  card.rotation = (rotation * Math.PI) / 180
  card.pivot.set(cardWidth / 2, cardHeight / 2)
  wallContainer.addChild(card)

  // Card data for animations
  card.channelId = channel.id
  card.baseX = x
  card.baseY = y
  card.floatOffset = Math.random() * Math.PI * 2
  card.floatSpeed = 0.3 + Math.random() * 0.2
  card.floatAmplitude = 3 + Math.random() * 4

  // Glow effect behind card
  const glow = new Graphics()
  glow.roundRect(-20, -20, cardWidth + 40, cardHeight + 40, 20)
  glow.fill({ color: palette.accent, alpha: 0.08 })
  const blurFilter = new BlurFilter({ strength: 15 })
  glow.filters = [blurFilter]
  card.addChild(glow)

  // Main card background
  const cardBg = new Graphics()
  cardBg.roundRect(0, 0, cardWidth, cardHeight, 12)
  cardBg.fill({ color: palette.primary })
  card.addChild(cardBg)

  // Inner gradient layer
  const innerGrad = new Graphics()
  innerGrad.roundRect(0, 0, cardWidth, cardHeight * 0.5, 12)
  innerGrad.fill({ color: palette.secondary, alpha: 0.6 })
  card.addChild(innerGrad)

  // Preview image (animated)
  try {
    const previewTexture = Assets.get(ASSETS[channel.id])
    if (previewTexture) {
      const preview = new Sprite(previewTexture)
      preview.width = cardWidth - 24
      preview.height = cardHeight - 70
      preview.x = 12
      preview.y = 12
      preview.alpha = 0.7

      // Create mask for preview
      const previewMask = new Graphics()
      previewMask.roundRect(12, 12, cardWidth - 24, cardHeight - 70, 8)
      previewMask.fill({ color: 0xffffff })
      card.addChild(previewMask)
      preview.mask = previewMask

      card.addChild(preview)

      // Animate preview - subtle zoom/pan
      gsap.to(preview, {
        x: preview.x - 5 + Math.random() * 10,
        duration: 4 + Math.random() * 3,
        ease: 'sine.inOut',
        yoyo: true,
        repeat: -1,
      })

      gsap.to(preview.scale, {
        x: 1.05,
        y: 1.05,
        duration: 6 + Math.random() * 4,
        ease: 'sine.inOut',
        yoyo: true,
        repeat: -1,
      })
    }
  } catch (e) {
    // Fallback if texture not found
  }

  // Accent line at bottom
  const accentLine = new Graphics()
  accentLine.roundRect(0, cardHeight - 4, cardWidth, 4, 2)
  accentLine.fill({ color: palette.accent, alpha: 0.8 })
  card.addChild(accentLine)

  // Pulsing accent animation
  gsap.to(accentLine, {
    alpha: 0.4,
    duration: 2 + Math.random(),
    ease: 'sine.inOut',
    yoyo: true,
    repeat: -1,
  })

  // Channel number (top right)
  const chNum = new Text({
    text: channel.id.replace('ch0', '').replace('ch', ''),
    style: {
      fontFamily: 'Space Mono, monospace',
      fontSize: 28,
      fill: palette.accent,
      fontWeight: 'bold',
    }
  })
  chNum.x = cardWidth - chNum.width - 16
  chNum.y = cardHeight - 45
  chNum.alpha = 0.25
  card.addChild(chNum)

  // Channel name
  const name = new Text({
    text: channel.name,
    style: {
      fontFamily: 'Space Mono, monospace',
      fontSize: 14,
      fill: 0xffffff,
      fontWeight: 'bold',
    }
  })
  name.x = 16
  name.y = cardHeight - 50
  card.addChild(name)

  // Agent name
  const agentName = new Text({
    text: channel.agent.name,
    style: {
      fontFamily: 'Space Mono, monospace',
      fontSize: 10,
      fill: palette.accent,
    }
  })
  agentName.x = 16
  agentName.y = cardHeight - 30
  card.addChild(agentName)

  // Live dot
  const liveDot = new Graphics()
  liveDot.circle(0, 0, 4)
  liveDot.fill({ color: palette.accent })
  liveDot.x = 20
  liveDot.y = 26
  card.addChild(liveDot)

  // Pulse live dot
  gsap.to(liveDot.scale, {
    x: 1.4,
    y: 1.4,
    duration: 1.2,
    ease: 'sine.inOut',
    yoyo: true,
    repeat: -1,
  })

  gsap.to(liveDot, {
    alpha: 0.3,
    duration: 1.2,
    ease: 'sine.inOut',
    yoyo: true,
    repeat: -1,
  })

  // Interaction
  cardBg.eventMode = 'static'
  cardBg.cursor = 'pointer'

  cardBg.on('pointerover', () => {
    if (isDragging) return
    gsap.to(card.scale, { x: scale * 1.08, y: scale * 1.08, duration: 0.3, ease: 'power2.out' })
    gsap.to(glow, { alpha: 0.2, duration: 0.3 })
  })

  cardBg.on('pointerout', () => {
    gsap.to(card.scale, { x: scale, y: scale, duration: 0.3, ease: 'power2.out' })
    gsap.to(glow, { alpha: 0.08, duration: 0.3 })
  })

  cardBg.on('pointerdown', (e) => {
    if (!isDragging) {
      tuneIn(channel.id)
    }
  })

  // Staggered entrance animation
  card.alpha = 0
  card.scale.set(scale * 0.8)
  gsap.to(card, {
    alpha: 1,
    duration: 0.8,
    delay: index * 0.1,
    ease: 'power2.out',
  })
  gsap.to(card.scale, {
    x: scale,
    y: scale,
    duration: 0.8,
    delay: index * 0.1,
    ease: 'back.out(1.5)',
  })

  channelCards.push(card)
}

// ============ DRAG INTERACTION ============

function setupDragInteraction() {
  const canvas = app.canvas

  canvas.addEventListener('pointerdown', (e) => {
    if (currentView !== 'wall') return
    isDragging = true
    dragStartX = e.clientX
    dragStartY = e.clientY
    lastDragX = e.clientX
    lastDragY = e.clientY
    document.body.style.cursor = 'grabbing'
  })

  canvas.addEventListener('pointermove', (e) => {
    if (!isDragging || currentView !== 'wall') return

    const dx = e.clientX - lastDragX
    const dy = e.clientY - lastDragY

    velocityX = dx * 0.6
    velocityY = dy * 0.6

    targetOffsetX += dx
    targetOffsetY += dy

    lastDragX = e.clientX
    lastDragY = e.clientY
  })

  canvas.addEventListener('pointerup', () => {
    isDragging = false
    document.body.style.cursor = 'grab'
  })

  canvas.addEventListener('pointerleave', () => {
    isDragging = false
    document.body.style.cursor = 'grab'
  })

  // Mouse wheel for smooth pan
  canvas.addEventListener('wheel', (e) => {
    if (currentView !== 'wall') return
    e.preventDefault()
    targetOffsetX -= e.deltaX * 0.5
    targetOffsetY -= e.deltaY * 0.5
  }, { passive: false })
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
  worldContainer.visible = false
  channelContainer.visible = true

  addChannelMemory(channelId, {
    type: 'viewer_interaction',
    content: 'A viewer tuned in',
    importance: 2,
  })

  drawChannel()
  showToast(channel.name, `${channel.agent.name.toUpperCase()} IS PROGRAMMING`)
  programChannel(channelId)
}

function drawChannel() {
  if (!currentChannel) return

  const W = app.screen.width
  const H = app.screen.height
  const palette = CHANNEL_PALETTES[currentChannel.id]

  channelContainer.removeChildren()

  // Background
  const bg = new Graphics()
  bg.rect(0, 0, W, H)
  bg.fill({ color: palette.primary })
  channelContainer.addChild(bg)

  // Gradient layers
  const grad1 = new Graphics()
  grad1.rect(0, 0, W, H * 0.5)
  grad1.fill({ color: palette.secondary, alpha: 0.7 })
  channelContainer.addChild(grad1)

  const grad2 = new Graphics()
  grad2.rect(0, H * 0.7, W, H * 0.3)
  grad2.fill({ color: 0x000000, alpha: 0.5 })
  channelContainer.addChild(grad2)

  // Channel visual
  const channelAsset = getChannelAsset(currentChannel.id)
  const visual = Sprite.from(channelAsset)
  visual.anchor.set(0.5)
  const scale = Math.max(W / visual.texture.width, H / visual.texture.height)
  visual.scale.set(scale * 1.05)
  visual.position.set(W / 2, H / 2)
  visual.alpha = 0.85
  channelContainer.addChild(visual)

  // Breathing animation
  gsap.to(visual, {
    scaleX: scale * 1.07,
    scaleY: scale * 1.06,
    duration: 8,
    ease: 'sine.inOut',
    yoyo: true,
    repeat: -1,
  })

  // Vignette
  const vignette = new Graphics()
  vignette.rect(0, 0, W, H * 0.2)
  vignette.fill({ color: 0x000000, alpha: 0.7 })
  vignette.rect(0, H * 0.85, W, H * 0.15)
  vignette.fill({ color: 0x000000, alpha: 0.8 })
  channelContainer.addChild(vignette)

  // Channel info
  const chLabel = new Text({
    text: `CH ${currentChannel.id.replace('ch0', '').replace('ch', '')}`,
    style: {
      fontFamily: 'Space Mono, monospace',
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
      fontFamily: 'Space Mono, monospace',
      fontSize: Math.min(36, W * 0.04),
      fill: 0xffffff,
      fontWeight: 'bold',
      letterSpacing: 4,
    }
  })
  chName.x = 40
  chName.y = 58
  channelContainer.addChild(chName)

  const agentInfo = new Text({
    text: `programmed by ${currentChannel.agent.name}`,
    style: {
      fontFamily: 'Space Mono, monospace',
      fontSize: 12,
      fill: 0x888899,
    }
  })
  agentInfo.x = 40
  agentInfo.y = 58 + chName.height + 8
  channelContainer.addChild(agentInfo)

  // Current mood
  const state = getChannelState(currentChannel.id)
  const currentMood = state?.mood || currentChannel.currentMood
  const moodText = new Text({
    text: `● ${currentMood}`,
    style: {
      fontFamily: 'Space Mono, monospace',
      fontSize: 14,
      fill: palette.accent,
    }
  })
  moodText.x = 40
  moodText.y = H - 100
  channelContainer.addChild(moodText)

  // Now playing
  const musicState = getMusicState()
  if (musicState.currentTrack) {
    const nowPlaying = new Text({
      text: `♪ ${musicState.currentTrack.name}`,
      style: {
        fontFamily: 'Space Mono, monospace',
        fontSize: 11,
        fill: 0x888899,
      }
    })
    nowPlaying.x = 40
    nowPlaying.y = H - 78
    channelContainer.addChild(nowPlaying)
  }

  // Agent thought
  if (state && state.lastThought) {
    const thought = new Text({
      text: `"${state.lastThought}"`,
      style: {
        fontFamily: 'Space Mono, monospace',
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

  // Time
  const timeDisplay = new Text({
    text: getLocalTime(),
    style: {
      fontFamily: 'Space Mono, monospace',
      fontSize: 14,
      fill: 0x444455,
    }
  })
  timeDisplay.x = W - timeDisplay.width - 40
  timeDisplay.y = 40
  channelContainer.addChild(timeDisplay)

  // Status
  const status = new Text({
    text: useLiveLLM ? '● LIVE' : '○ AMBIENT',
    style: {
      fontFamily: 'Space Mono, monospace',
      fontSize: 10,
      fill: useLiveLLM ? palette.accent : 0x444455,
    }
  })
  status.x = W - status.width - 40
  status.y = 58
  channelContainer.addChild(status)

  // Memory stream
  const memories = getRecentMemories(currentChannel.id, 4)
  if (memories.length > 0) {
    const memoryTitle = new Text({
      text: 'MEMORY',
      style: {
        fontFamily: 'Space Mono, monospace',
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
          fontFamily: 'Space Mono, monospace',
          fontSize: 9,
          fill: 0x444455,
        }
      })
      memText.x = W - 260
      memText.y = H - 100 + i * 16
      channelContainer.addChild(memText)
    })
  }
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

// ============ UPDATE LOOP ============

function update(ticker) {
  const W = app.screen.width
  const H = app.screen.height
  const time = ticker.lastTime / 1000

  if (currentView === 'wall') {
    // Smooth drag following
    if (!isDragging) {
      // Apply momentum
      targetOffsetX += velocityX
      targetOffsetY += velocityY
      velocityX *= 0.92
      velocityY *= 0.92
    }

    // Clamp to bounds
    const minX = -WORLD_WIDTH + W * 0.3
    const maxX = W * 0.7
    const minY = -WORLD_HEIGHT + H * 0.3
    const maxY = H * 0.7

    targetOffsetX = Math.max(minX, Math.min(maxX, targetOffsetX))
    targetOffsetY = Math.max(minY, Math.min(maxY, targetOffsetY))

    // Smooth interpolation
    worldOffsetX += (targetOffsetX - worldOffsetX) * 0.15
    worldOffsetY += (targetOffsetY - worldOffsetY) * 0.15

    worldContainer.x = worldOffsetX
    worldContainer.y = worldOffsetY

    // Animate floating cards
    channelCards.forEach((card) => {
      const floatY = Math.sin(time * card.floatSpeed + card.floatOffset) * card.floatAmplitude
      card.y = card.baseY + floatY
    })
  }

  // Particles
  const particleGraphics = particleContainer.children[0] || new Graphics()
  if (!particleContainer.children.length) particleContainer.addChild(particleGraphics)
  particleGraphics.clear()

  particles.forEach(p => {
    p.x += p.vx
    p.y += p.vy
    p.pulse += 0.02

    if (p.x < 0) p.x = W
    if (p.x > W) p.x = 0
    if (p.y < 0) p.y = H
    if (p.y > H) p.y = 0

    const pulseAlpha = p.alpha * (0.6 + 0.4 * Math.sin(p.pulse))
    particleGraphics.circle(p.x, p.y, p.size)
    particleGraphics.fill({ color: 0xffffff, alpha: pulseAlpha * (currentView === 'wall' ? 0.6 : 0.3) })
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
    // Recenter on resize
    targetOffsetX = (W - WORLD_WIDTH) / 2
    targetOffsetY = (H - WORLD_HEIGHT) / 2
    drawInfiniteWall()
  } else {
    drawChannel()
  }

  particles.forEach(p => {
    p.x = Math.random() * W
    p.y = Math.random() * H
  })
}

// Start
init().catch(console.error)
