/**
 * The Building - character definitions and initialization
 *
 * Three characters:
 * - Maya (3B) - Software engineer, our original lo-fi girl
 * - Daniel (2A) - Writer struggling with his second novel
 * - Iris (4C) - Artist who rarely leaves her apartment
 */

import { Character } from './character.js'
import { world } from './world.js'

/**
 * Character templates - personas and traits
 * Beliefs and detailed prompts can be customized
 */
export const CHARACTER_TEMPLATES = {
  maya: {
    id: 'maya_3b',
    name: 'Maya',
    apartment: '3B',
    persona: `A 28-year-old software engineer who moved to NYC from Mumbai two years ago.
She works remotely for a startup and often finds herself coding late into the night.
She's searching for connection in a city where she still feels like a stranger.
Her apartment is filled with plants she talks to and books she's been meaning to read.`,
    traits: ['introverted', 'analytical', 'quietly ambitious', 'homesick', 'night owl'],
    goals: [
      'Build something meaningful with her code',
      'Find a sense of belonging in NYC',
      'Call her mother more often',
      'Finish reading the stack of books by her bed',
    ],
    initialMood: 'focused',
    initialEnergy: 0.7,
  },

  daniel: {
    id: 'daniel_2a',
    name: 'Daniel',
    apartment: '2A',
    persona: `A 34-year-old writer whose first novel was a modest success three years ago.
He's been struggling with his second book, the pressure mounting with each passing month.
He drinks too much coffee, sleeps poorly, and often wonders if he's a fraud.
He moved to this building because it was cheap and quiet.`,
    traits: ['creative', 'self-doubting', 'observant', 'prone to melancholy', 'insomniac'],
    goals: [
      'Finish the second novel before his advance runs out',
      'Prove to himself he wasn\'t a one-hit wonder',
      'Stop checking his first book\'s Amazon ranking',
      'Find someone who understands the loneliness of creation',
    ],
    initialMood: 'anxious',
    initialEnergy: 0.5,
  },

  iris: {
    id: 'iris_4c',
    name: 'Iris',
    apartment: '4C',
    persona: `A 42-year-old artist who had gallery shows in her 30s but now works in isolation.
She hasn't left her apartment in three weeks, creating obsessively.
She orders everything online and communicates mostly through text.
Her apartment is a maze of canvases, and she's not sure if she's making her best work or losing her mind.`,
    traits: ['reclusive', 'intense', 'perceptive', 'eccentric', 'secretly lonely'],
    goals: [
      'Complete her current series before the vision fades',
      'Decide if she should accept the gallery\'s offer',
      'Remember what sunlight feels like',
      'Reconnect with the world without losing herself',
    ],
    initialMood: 'intense',
    initialEnergy: 0.6,
  },
}

/**
 * Initialize the building with all characters
 */
export function initializeBuilding(customTemplates = {}) {
  const templates = { ...CHARACTER_TEMPLATES, ...customTemplates }

  const maya = new Character(templates.maya)
  const daniel = new Character(templates.daniel)
  const iris = new Character(templates.iris)

  // Set up initial relationships
  // Maya and Daniel have met in the hallway a few times
  maya.updateRelationship('daniel_2a', { familiarity: 0.3, sentiment: 0.1 })
  daniel.updateRelationship('maya_3b', { familiarity: 0.3, sentiment: 0.2 })

  // Iris and Maya have texted a few times (Iris borrowed sugar once)
  iris.updateRelationship('maya_3b', { familiarity: 0.4, sentiment: 0.3 })
  maya.updateRelationship('iris_4c', { familiarity: 0.4, sentiment: 0.5 })

  // Daniel has heard Iris painting at odd hours, intrigued but never spoken
  daniel.updateRelationship('iris_4c', { familiarity: 0.1, sentiment: 0.2 })
  iris.updateRelationship('daniel_2a', { familiarity: 0.1, sentiment: 0 })

  // Seed some initial memories
  seedInitialMemories(maya, daniel, iris)

  return { maya, daniel, iris }
}

/**
 * Seed characters with some initial memories
 */
function seedInitialMemories(maya, daniel, iris) {
  // Maya's memories
  maya.addMemory('Moved into apartment 3B two years ago today', { importance: 7, type: 'reflection' })
  maya.addMemory('The neighbor in 2A seems nice, we nodded hello in the hallway', { importance: 3 })
  maya.addMemory('Iris from 4C texted asking if I had any sugar. She seems interesting.', { importance: 4 })
  maya.addMemory('Mom called asking when I\'m coming home for Diwali', { importance: 6 })

  // Daniel's memories
  daniel.addMemory('My editor called asking about the manuscript. I lied about my progress.', { importance: 8 })
  daniel.addMemory('Heard someone typing late at night - probably that tech worker in 3B', { importance: 2 })
  daniel.addMemory('There\'s a woman in 4C who paints at 3am. I hear her moving canvases.', { importance: 4 })
  daniel.addMemory('Re-read the first chapter today. Maybe it\'s not as bad as I thought.', { importance: 5 })

  // Iris's memories
  iris.addMemory('The new series is demanding everything from me. I haven\'t left in weeks.', { importance: 7 })
  iris.addMemory('The girl in 3B brought me sugar. She has kind eyes.', { importance: 4 })
  iris.addMemory('Gallery called again. I let it go to voicemail.', { importance: 6 })
  iris.addMemory('The rain on the window is the only conversation I\'ve had today.', { importance: 5, type: 'reflection' })
}

/**
 * Get all characters as array
 */
export function getAllCharacters() {
  return Array.from(world.characters.values())
}

/**
 * Get character by apartment
 */
export function getCharacterByApartment(apt) {
  for (const char of world.characters.values()) {
    if (char.apartment === apt) return char
  }
  return null
}

/**
 * Building layout for visualization
 */
export const BUILDING_LAYOUT = {
  floors: [
    { floor: 4, apartments: ['4A', '4B', '4C'] },
    { floor: 3, apartments: ['3A', '3B', '3C'] },
    { floor: 2, apartments: ['2A', '2B', '2C'] },
  ],
  occupied: {
    '3B': 'maya_3b',
    '2A': 'daniel_2a',
    '4C': 'iris_4c',
  },
  empty: ['4A', '4B', '3A', '3C', '2B', '2C'],
}

/**
 * Check if a window should be lit
 */
export function isWindowLit(apartment) {
  const characterId = BUILDING_LAYOUT.occupied[apartment]
  if (!characterId) return false

  const character = world.characters.get(characterId)
  if (!character) return false

  // Window is lit if character is awake (energy > 0.2 or has current action)
  return character.state.energy > 0.2 || character.state.currentAction !== null
}

/**
 * Get scene description for an apartment
 */
export function getApartmentScene(apartment) {
  const characterId = BUILDING_LAYOUT.occupied[apartment]
  if (!characterId) {
    return { empty: true, lit: false }
  }

  const character = world.characters.get(characterId)
  if (!character) return { empty: true, lit: false }

  return {
    empty: false,
    lit: isWindowLit(apartment),
    character: {
      name: character.name,
      mood: character.state.mood,
      action: character.state.currentAction,
      energy: character.state.energy,
    },
    recentActivity: character.memories.slice(-3).map(m => m.text),
  }
}
