/**
 * Visuals Library - scenes and visual styles for mood42 channels
 * Each channel now has its own unique AI-generated scene
 */

// Channel-specific visual assets
export const CHANNEL_ASSETS = {
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

// Visual definitions with channel-specific scenes
export const VISUALS = {
  // Channel 01 - Late Night
  late_night: {
    id: 'late_night',
    name: 'Late Night Coding',
    description: 'Software engineer coding at 3AM, rain outside, city lights',
    asset: CHANNEL_ASSETS.ch01,
    mood: ['focused', 'cozy', 'productive'],
    style: ['rain', 'desk', 'city-window', 'cozy'],
  },

  // Channel 02 - Rain Café
  rain_cafe: {
    id: 'rain_cafe',
    name: 'Kyoto Kissaten',
    description: 'Cozy Japanese coffee shop, rainy afternoon, jazz vinyl',
    asset: CHANNEL_ASSETS.ch02,
    mood: ['cozy', 'warm', 'rainy'],
    style: ['coffee', 'rain', 'warm-light', 'steam'],
  },

  // Channel 03 - Jazz Noir
  jazz_noir: {
    id: 'jazz_noir',
    name: 'Noir Jazz Club',
    description: '1950s Chicago jazz club, smoky atmosphere, dim lighting',
    asset: CHANNEL_ASSETS.ch03,
    mood: ['mysterious', 'melancholic', 'smoky'],
    style: ['noir', 'smoke', 'shadows', 'city-night'],
  },

  // Channel 04 - Synthwave
  synthwave: {
    id: 'synthwave',
    name: 'Neon Grid',
    description: 'Retro-futuristic landscape, neon sunset, chrome aesthetic',
    asset: CHANNEL_ASSETS.ch04,
    mood: ['energetic', 'retro', 'driving'],
    style: ['neon', 'grid', 'sunset', 'cars', 'chrome'],
  },

  // Channel 05 - Deep Space
  deep_space: {
    id: 'deep_space',
    name: 'Cosmic Void',
    description: 'Deep space nebula, stars, infinite void',
    asset: CHANNEL_ASSETS.ch05,
    mood: ['transcendent', 'vast', 'calm'],
    style: ['stars', 'nebula', 'void', 'planets'],
  },

  // Channel 06 - Tokyo Drift
  tokyo_drift: {
    id: 'tokyo_drift',
    name: 'Shinjuku Night',
    description: 'Tokyo street after rain, neon reflections, empty alley',
    asset: CHANNEL_ASSETS.ch06,
    mood: ['urban', 'energetic', 'nostalgic'],
    style: ['tokyo', 'neon-signs', 'rain-street', 'cars'],
  },

  // Channel 07 - Sunday Morning
  sunday_morning: {
    id: 'sunday_morning',
    name: 'Vermont Morning',
    description: 'Sunlit farmhouse, plants, golden morning light',
    asset: CHANNEL_ASSETS.ch07,
    mood: ['hopeful', 'gentle', 'peaceful'],
    style: ['sunlight', 'plants', 'morning', 'nature'],
  },

  // Channel 08 - Focus
  focus: {
    id: 'focus',
    name: 'Minimal Studio',
    description: 'Clean Scandinavian workspace, perfect clarity',
    asset: CHANNEL_ASSETS.ch08,
    mood: ['productive', 'clean', 'steady'],
    style: ['abstract', 'geometric', 'clean', 'white-space'],
  },

  // Channel 09 - Melancholy
  melancholy: {
    id: 'melancholy',
    name: 'London Rain',
    description: 'Rainy London evening, writer\'s room, contemplative',
    asset: CHANNEL_ASSETS.ch09,
    mood: ['melancholic', 'sad', 'reflective'],
    style: ['rain', 'empty-rooms', 'grey', 'solitude'],
  },

  // Channel 10 - Golden Hour
  golden_hour: {
    id: 'golden_hour',
    name: 'Lisbon Sunset',
    description: 'Golden hour over Lisbon rooftops, warm magical light',
    asset: CHANNEL_ASSETS.ch10,
    mood: ['nostalgic', 'warm', 'peaceful'],
    style: ['sunset', 'golden', 'nature', 'warmth'],
  },

  // Legacy fallbacks
  scene_focused: {
    id: 'scene_focused',
    name: 'Focused Room',
    description: 'Cozy desk with rain outside, warm lamp light',
    asset: '/assets/scene_focused.png',
    mood: ['focused', 'cozy', 'productive'],
    style: ['rain', 'desk', 'city-window', 'cozy'],
  },
  scene_withdrawn: {
    id: 'scene_withdrawn',
    name: 'Withdrawn',
    description: 'Dark room, contemplative mood, soft shadows',
    asset: '/assets/scene_withdrawn.png',
    mood: ['melancholic', 'introspective', 'sad'],
    style: ['dark', 'solitude', 'shadows'],
  },
}

// Channel-to-visual mapping (primary visual for each channel)
export const CHANNEL_VISUALS = {
  ch01: ['late_night'],
  ch02: ['rain_cafe'],
  ch03: ['jazz_noir'],
  ch04: ['synthwave'],
  ch05: ['deep_space'],
  ch06: ['tokyo_drift'],
  ch07: ['sunday_morning'],
  ch08: ['focus'],
  ch09: ['melancholy'],
  ch10: ['golden_hour'],
}

// Default visual for each channel
export const CHANNEL_DEFAULT_VISUAL = {
  ch01: 'late_night',
  ch02: 'rain_cafe',
  ch03: 'jazz_noir',
  ch04: 'synthwave',
  ch05: 'deep_space',
  ch06: 'tokyo_drift',
  ch07: 'sunday_morning',
  ch08: 'focus',
  ch09: 'melancholy',
  ch10: 'golden_hour',
}

/**
 * Get all visuals
 */
export function getAllVisuals() {
  return Object.values(VISUALS)
}

/**
 * Get visual by ID
 */
export function getVisual(id) {
  return VISUALS[id]
}

/**
 * Get visuals by mood
 */
export function getVisualsByMood(mood) {
  return Object.values(VISUALS).filter(v =>
    v.mood && v.mood.includes(mood)
  )
}

/**
 * Get visuals by style
 */
export function getVisualsByStyle(style) {
  return Object.values(VISUALS).filter(v =>
    v.style && v.style.includes(style)
  )
}

/**
 * Get visuals for a channel
 */
export function getVisualsForChannel(channelId) {
  const visualIds = CHANNEL_VISUALS[channelId] || ['scene_focused']
  return visualIds.map(id => VISUALS[id]).filter(Boolean)
}

/**
 * Get the primary visual for a channel
 */
export function getChannelVisual(channelId) {
  const visualId = CHANNEL_DEFAULT_VISUAL[channelId]
  return VISUALS[visualId] || VISUALS.scene_focused
}

/**
 * Get random visual for a channel
 */
export function getRandomVisualForChannel(channelId) {
  const visuals = getVisualsForChannel(channelId)
  if (visuals.length === 0) return VISUALS.scene_focused
  return visuals[Math.floor(Math.random() * visuals.length)]
}

/**
 * Get channel asset path directly
 */
export function getChannelAsset(channelId) {
  return CHANNEL_ASSETS[channelId] || '/assets/scene_focused.png'
}
