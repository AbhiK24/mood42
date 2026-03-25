/**
 * Visuals Library - scenes and visual styles for mood42 channels
 */

// Visual definitions
export const VISUALS = {
  // Cozy / Lo-fi
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

  // Rain / Cafe
  cafe: {
    id: 'cafe',
    name: 'Rain Cafe',
    description: 'Coffee shop window, rain, warm interior',
    asset: '/assets/scene_focused.png', // placeholder
    mood: ['cozy', 'warm', 'rainy'],
    style: ['coffee', 'rain', 'warm-light', 'steam'],
  },

  // Noir
  noir: {
    id: 'noir',
    name: 'Noir City',
    description: 'Dark city streets, neon signs, smoke, shadows',
    asset: '/assets/scene_withdrawn.png',
    mood: ['mysterious', 'melancholic', 'smoky'],
    style: ['noir', 'smoke', 'shadows', 'city-night'],
  },

  // Synthwave
  synthwave: {
    id: 'synthwave',
    name: 'Neon Grid',
    description: 'Retro neon grid, sunset, chrome aesthetic',
    asset: '/assets/scene_focused.png',
    mood: ['energetic', 'retro', 'driving'],
    style: ['neon', 'grid', 'sunset', 'cars', 'chrome'],
  },

  // Space
  space: {
    id: 'space',
    name: 'Deep Space',
    description: 'Stars, nebula, infinite void, planets',
    asset: '/assets/scene_withdrawn.png',
    mood: ['transcendent', 'vast', 'calm'],
    style: ['stars', 'nebula', 'void', 'planets'],
  },

  // Tokyo
  tokyo: {
    id: 'tokyo',
    name: 'Tokyo Night',
    description: 'Neon streets, rain reflections, urban energy',
    asset: '/assets/scene_focused.png',
    mood: ['urban', 'energetic', 'nostalgic'],
    style: ['tokyo', 'neon-signs', 'rain-street', 'cars'],
  },

  // Morning
  morning: {
    id: 'morning',
    name: 'Sunday Morning',
    description: 'Sunlight through plants, peaceful, hopeful',
    asset: '/assets/scene_focused.png',
    mood: ['hopeful', 'gentle', 'peaceful'],
    style: ['sunlight', 'plants', 'morning', 'nature'],
  },

  // Minimal
  minimal: {
    id: 'minimal',
    name: 'Minimal',
    description: 'Clean abstract shapes, white space, focus',
    asset: '/assets/scene_focused.png',
    mood: ['productive', 'clean', 'steady'],
    style: ['abstract', 'geometric', 'clean', 'white-space'],
  },

  // Melancholy
  melancholy: {
    id: 'melancholy',
    name: 'Empty Room',
    description: 'Rain, empty rooms, grey light, solitude',
    asset: '/assets/scene_withdrawn.png',
    mood: ['melancholic', 'sad', 'reflective'],
    style: ['rain', 'empty-rooms', 'grey', 'solitude'],
  },

  // Sunset
  sunset: {
    id: 'sunset',
    name: 'Golden Hour',
    description: 'Warm sunset light, golden haze, nature',
    asset: '/assets/scene_focused.png',
    mood: ['nostalgic', 'warm', 'peaceful'],
    style: ['sunset', 'golden', 'nature', 'warmth'],
  },
}

// Channel-to-visual mapping
export const CHANNEL_VISUALS = {
  ch01: ['scene_focused', 'cafe', 'melancholy'],           // Late Night
  ch02: ['cafe', 'scene_focused'],                          // Rain Cafe
  ch03: ['noir', 'scene_withdrawn', 'melancholy'],         // Jazz Noir
  ch04: ['synthwave'],                                      // Synthwave
  ch05: ['space'],                                          // Deep Space
  ch06: ['tokyo', 'synthwave', 'noir'],                    // Tokyo Drift
  ch07: ['morning', 'sunset'],                              // Sunday Morning
  ch08: ['minimal', 'scene_focused'],                       // Focus
  ch09: ['melancholy', 'scene_withdrawn', 'noir'],         // Melancholy
  ch10: ['sunset', 'morning'],                              // Golden Hour
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
 * Get random visual for a channel
 */
export function getRandomVisualForChannel(channelId) {
  const visuals = getVisualsForChannel(channelId)
  if (visuals.length === 0) return VISUALS.scene_focused
  return visuals[Math.floor(Math.random() * visuals.length)]
}
