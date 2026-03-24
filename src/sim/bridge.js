/**
 * Bridge - connects the simulation engine to the visual layer
 *
 * Maps simulation state to visual state for rendering
 */

import { simState, setMood, MOODS } from './state.js'
import { tick as simTick, getSimulationState, initializeLLM } from './engine.js'
import { world, getCharacter, getTimeString } from './world.js'
import { initializeBuilding, getAllCharacters, BUILDING_LAYOUT, isWindowLit } from './building.js'

let initialized = false
let activeCharacterId = 'maya_3b' // Default view

/**
 * Initialize simulation and bridge
 */
export function initSimulation(apiKey = null) {
  if (initialized) return

  // Initialize LLM (will use mock if no key)
  const hasLLM = initializeLLM(apiKey)
  console.log(`[Simulation] LLM: ${hasLLM ? 'Kimi K2 connected' : 'Using mock responses'}`)

  // Initialize the building with all characters
  initializeBuilding()
  initialized = true

  console.log('[Simulation] Building initialized with characters:')
  for (const char of getAllCharacters()) {
    console.log(`  - ${char.name} (${char.apartment})`)
  }
}

/**
 * Set which character we're viewing
 */
export function setActiveCharacter(characterId) {
  activeCharacterId = characterId
  syncVisualState()
}

/**
 * Get the active character
 */
export function getActiveCharacter() {
  return getCharacter(activeCharacterId)
}

/**
 * Sync simulation state to visual state
 */
export function syncVisualState() {
  const character = getActiveCharacter()
  if (!character) return

  // Map character mood to visual mood
  const moodMap = {
    'focused': 'FOCUSED',
    'content': 'GOOD',
    'peaceful': 'GOOD',
    'anxious': 'ANXIOUS',
    'restless': 'ANXIOUS',
    'exhausted': 'WITHDRAWN',
    'lonely': 'WITHDRAWN',
    'melancholic': 'WITHDRAWN',
    'intense': 'FOCUSED',
    'neutral': 'FOCUSED',
  }

  const visualMood = moodMap[character.state.mood] || 'FOCUSED'
  if (MOODS[visualMood]) {
    simState.characterMood = visualMood
  }

  // Sync time
  simState.time = world.timeOfDay

  // Sync rain
  simState.raining = world.weather.raining
  simState.rainIntensity = world.weather.intensity

  // Lamp on if character is awake
  simState.lampOn = character.state.energy > 0.2
  simState.lampIntensity = Math.max(0.3, character.state.energy)
}

/**
 * Run one simulation tick and sync to visual
 */
export async function simulationTick(options = {}) {
  if (!initialized) initSimulation()

  await simTick({ minutesPerTick: 5, ...options })
  syncVisualState()

  return getSimulationState()
}

/**
 * Get building view data for visualization
 */
export function getBuildingView() {
  const floors = BUILDING_LAYOUT.floors.map(floor => ({
    floor: floor.floor,
    apartments: floor.apartments.map(apt => {
      const characterId = BUILDING_LAYOUT.occupied[apt]
      const character = characterId ? getCharacter(characterId) : null

      return {
        id: apt,
        occupied: !!character,
        lit: isWindowLit(apt),
        character: character ? {
          id: character.id,
          name: character.name,
          mood: character.state.mood,
          action: character.state.currentAction,
        } : null,
        isActive: characterId === activeCharacterId,
      }
    }),
  }))

  return {
    time: getTimeString(),
    day: world.day,
    weather: world.weather,
    floors,
  }
}

/**
 * Get character details for detail view
 */
export function getCharacterDetail(characterId = activeCharacterId) {
  const character = getCharacter(characterId)
  if (!character) return null

  return {
    id: character.id,
    name: character.name,
    apartment: character.apartment,
    mood: character.state.mood,
    energy: character.state.energy,
    currentAction: character.state.currentAction,
    recentMemories: character.memories.slice(-10).map(m => ({
      text: m.text,
      type: m.type,
      importance: m.importance,
      time: formatMemoryTime(m),
    })),
    relationships: Array.from(character.relationships.entries()).map(([id, rel]) => {
      const other = getCharacter(id)
      return {
        id,
        name: other?.name || id,
        apartment: other?.apartment,
        familiarity: rel.familiarity,
        sentiment: rel.sentiment,
      }
    }),
  }
}

function formatMemoryTime(memory) {
  const hours = Math.floor(memory.time / 60) % 24
  const mins = memory.time % 60
  const period = hours >= 12 ? 'PM' : 'AM'
  const h = hours % 12 || 12
  return `Day ${memory.day}, ${h}:${mins.toString().padStart(2, '0')} ${period}`
}

/**
 * Trigger an interaction from the viewer
 */
export function viewerInteraction(type, data) {
  const character = getActiveCharacter()
  if (!character) return

  // The viewer's presence affects the character subtly
  switch (type) {
    case 'focus':
      // Someone is watching closely
      character.observe('I feel like someone is watching', 2)
      break

    case 'click_memory':
      // Viewer clicked on a memory - character reflects on it
      if (data.memoryText) {
        character.observe(`The memory surfaces: "${data.memoryText}"`, 4)
      }
      break

    case 'time_skip':
      // Viewer skipped time - run simulation forward
      const ticks = Math.floor(data.minutes / 5)
      for (let i = 0; i < ticks; i++) {
        simTick({ minutesPerTick: 5 })
      }
      syncVisualState()
      break
  }
}

/**
 * Get data for a memory dive visualization
 */
export function getMemoryDive(memoryId) {
  const character = getActiveCharacter()
  if (!character) return null

  const memory = character.memories.find(m => m.id === memoryId)
  if (!memory) return null

  // Get context around this memory
  const index = character.memories.indexOf(memory)
  const before = character.memories.slice(Math.max(0, index - 3), index)
  const after = character.memories.slice(index + 1, index + 4)

  return {
    memory: {
      text: memory.text,
      type: memory.type,
      importance: memory.importance,
      time: formatMemoryTime(memory),
    },
    context: {
      before: before.map(m => ({ text: m.text, type: m.type })),
      after: after.map(m => ({ text: m.text, type: m.type })),
    },
    // Scene prompt for image generation
    scenePrompt: generateScenePrompt(character, memory),
  }
}

/**
 * Generate a scene prompt for a memory
 */
function generateScenePrompt(character, memory) {
  const timeOfDay = memory.time >= 20 * 60 || memory.time < 6 * 60 ? 'night' : 'day'
  const mood = memory.type === 'reflection' ? 'contemplative' : 'observational'

  return `Lo-fi anime illustration, ${character.name}, ${character.persona.split('.')[0]},
${memory.text}, ${timeOfDay} scene, ${mood} mood,
Studio Ghibli style, atmospheric lighting, emotional, high quality digital art`
}
