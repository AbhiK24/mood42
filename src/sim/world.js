/**
 * World State - shared clock, weather, global events
 */

export const world = {
  // Time in minutes since midnight, day 0
  tick: 0,
  day: 0,
  timeOfDay: 23 * 60, // Start at 11pm

  // Weather
  weather: {
    raining: true,
    intensity: 0.7,
    thunder: false,
  },

  // Global events queue
  events: [],

  // All characters in the building
  characters: new Map(),

  // Interaction log (for cross-character events)
  interactionLog: [],
}

/**
 * Get current time as HH:MM string
 */
export function getTimeString() {
  const hours = Math.floor(world.timeOfDay / 60) % 24
  const mins = world.timeOfDay % 60
  const period = hours >= 12 ? 'PM' : 'AM'
  const h = hours % 12 || 12
  return `${h}:${mins.toString().padStart(2, '0')} ${period}`
}

/**
 * Get time of day category
 */
export function getTimePeriod() {
  const hour = Math.floor(world.timeOfDay / 60) % 24
  if (hour >= 5 && hour < 9) return 'early_morning'
  if (hour >= 9 && hour < 12) return 'morning'
  if (hour >= 12 && hour < 14) return 'midday'
  if (hour >= 14 && hour < 17) return 'afternoon'
  if (hour >= 17 && hour < 20) return 'evening'
  if (hour >= 20 && hour < 23) return 'night'
  return 'late_night'
}

/**
 * Advance world time
 */
export function advanceWorldTime(minutes = 1) {
  world.timeOfDay += minutes
  world.tick++

  // Handle day rollover
  if (world.timeOfDay >= 24 * 60) {
    world.timeOfDay -= 24 * 60
    world.day++
  }
}

/**
 * Register a character in the world
 */
export function registerCharacter(character) {
  world.characters.set(character.id, character)
}

/**
 * Get character by ID
 */
export function getCharacter(id) {
  return world.characters.get(id)
}

/**
 * Log an interaction between characters
 */
export function logInteraction(fromId, toId, type, content) {
  const interaction = {
    tick: world.tick,
    time: world.timeOfDay,
    day: world.day,
    from: fromId,
    to: toId,
    type, // 'text', 'encounter', 'overheard', 'knock'
    content,
  }
  world.interactionLog.push(interaction)
  return interaction
}

/**
 * Get recent interactions involving a character
 */
export function getRecentInteractions(characterId, limit = 10) {
  return world.interactionLog
    .filter(i => i.from === characterId || i.to === characterId)
    .slice(-limit)
}
