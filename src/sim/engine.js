/**
 * Simulation Engine - main loop, LLM integration, event processing
 */

import { world, advanceWorldTime, getTimeString, logInteraction, getCharacter } from './world.js'
import { Character } from './character.js'

// LLM interface (to be implemented with Claude API)
let llmInterface = null

/**
 * Set the LLM interface for reflection/planning
 */
export function setLLMInterface(llm) {
  llmInterface = llm
}

/**
 * Default mock LLM for testing without API
 */
const mockLLM = {
  async reflect(character) {
    const moods = ['contemplative', 'restless', 'peaceful', 'uncertain']
    const mood = moods[Math.floor(Math.random() * moods.length)]
    return `I'm feeling ${mood} tonight. The rain outside makes me think about where I am in life.`
  },

  async plan(character) {
    const ctx = character.getCurrentContext()
    const hour = Math.floor(world.timeOfDay / 60)

    if (hour >= 23 || hour < 6) {
      return [
        { time: getTimeString(), action: 'wind down for the night', duration: 30 },
        { time: getTimeString(), action: 'try to sleep', duration: 60 },
      ]
    }

    return [
      { time: getTimeString(), action: 'work on personal project', duration: 45 },
      { time: getTimeString(), action: 'take a break, make tea', duration: 15 },
      { time: getTimeString(), action: 'read or watch something', duration: 30 },
    ]
  },

  async rateImportance(memory) {
    // Simple heuristic for importance
    const text = memory.text.toLowerCase()
    if (text.includes('realized') || text.includes('understand')) return 8
    if (text.includes('texted') || text.includes('spoke')) return 6
    if (text.includes('feel') || text.includes('emotion')) return 5
    return 3
  },

  async decideAction(character, context) {
    // What should the character do right now?
    const nextPlanned = character.getNextPlannedAction()
    if (nextPlanned) return { type: 'follow_plan', action: nextPlanned }
    return { type: 'idle', action: null }
  },
}

/**
 * Get the active LLM (real or mock)
 */
function getLLM() {
  return llmInterface ?? mockLLM
}

/**
 * Process a single simulation tick
 */
export async function tick(options = {}) {
  const { minutesPerTick = 5, verbose = false } = options

  // Advance world time
  advanceWorldTime(minutesPerTick)

  if (verbose) {
    console.log(`[Tick ${world.tick}] ${getTimeString()} Day ${world.day}`)
  }

  // Process each character
  for (const [id, character] of world.characters) {
    await processCharacter(character, options)
  }

  // Process pending interactions
  await processInteractions()

  // Process world events
  await processWorldEvents()

  return {
    tick: world.tick,
    time: world.timeOfDay,
    day: world.day,
  }
}

/**
 * Process a single character's tick
 */
async function processCharacter(character, options = {}) {
  const llm = getLLM()

  // 1. Environmental observations based on time/weather
  await generateObservations(character)

  // 2. Check if reflection is needed
  if (character.needsReflection) {
    const insight = await llm.reflect(character)
    character.addReflection(insight)

    if (options.verbose) {
      console.log(`  [${character.name}] Reflection: ${insight}`)
    }
  }

  // 3. Check if replanning is needed
  if (character.shouldReplan()) {
    const plan = await llm.plan(character)
    character.setPlan(plan)

    if (options.verbose) {
      console.log(`  [${character.name}] New plan:`, plan.map(p => p.action).join(', '))
    }
  }

  // 4. Execute current action or decide new one
  await executeOrDecide(character, llm, options)

  // 5. Update mood/energy based on state
  updateCharacterState(character)
}

/**
 * Generate environmental observations
 */
async function generateObservations(character) {
  const hour = Math.floor(world.timeOfDay / 60)

  // Time-based observations (occasional)
  if (world.tick % 12 === 0) { // Every hour
    if (hour === 1) {
      character.observe('The apartment across the street just turned off their light', 4)
    } else if (hour === 0) {
      character.observe('It\'s midnight. The city feels quieter', 3)
    } else if (world.weather.raining && Math.random() < 0.3) {
      character.observe('Rain continues to streak down the window', 2)
    }
  }

  // Random small observations
  if (Math.random() < 0.05) {
    const observations = [
      'Heard a car pass by on the wet street',
      'The coffee has gone cold',
      'A notification lit up my phone briefly',
      'The lamp flickered for a moment',
      'Someone laughed in the hallway outside',
    ]
    const obs = observations[Math.floor(Math.random() * observations.length)]
    character.observe(obs, 2)
  }
}

/**
 * Execute current planned action or decide what to do
 */
async function executeOrDecide(character, llm, options = {}) {
  // Check if current action should complete
  const current = character.currentPlan.find(p => p.started && !p.completed)
  if (current) {
    const elapsed = (world.tick - current.startTick) * 5 // minutes
    if (elapsed >= current.duration) {
      character.completeCurrentAction()

      if (options.verbose) {
        console.log(`  [${character.name}] Completed: ${current.action}`)
      }
    }
    return // Still doing current action
  }

  // Get next planned action
  const next = character.getNextPlannedAction()
  if (next) {
    character.startAction(next)

    if (options.verbose) {
      console.log(`  [${character.name}] Starting: ${next.action}`)
    }
    return
  }

  // No plan - character is idle (will trigger replan next tick)
}

/**
 * Update character's mood and energy
 */
function updateCharacterState(character) {
  const hour = Math.floor(world.timeOfDay / 60)

  // Energy decreases over time, especially late at night
  if (hour >= 23 || hour < 6) {
    character.state.energy = Math.max(0.1, character.state.energy - 0.01)
  }

  // Social need increases when alone
  character.state.socialNeed = Math.min(1, character.state.socialNeed + 0.002)

  // Mood can shift based on energy and social need
  if (character.state.energy < 0.3) {
    character.state.mood = 'exhausted'
  } else if (character.state.socialNeed > 0.8) {
    character.state.mood = 'lonely'
  }
}

/**
 * Process pending character interactions
 */
async function processInteractions() {
  // Check for random interactions between characters
  const characters = Array.from(world.characters.values())

  for (const char of characters) {
    // Small chance of texting someone they know
    if (Math.random() < 0.02 && char.relationships.size > 0) {
      const relationships = Array.from(char.relationships.entries())
      const [targetId, rel] = relationships[Math.floor(Math.random() * relationships.length)]
      const target = getCharacter(targetId)

      if (target && rel.familiarity > 0.2) {
        // Generate a simple text message
        const messages = [
          'Hey, you up?',
          'How\'s your night going?',
          'Saw something that reminded me of you',
          'Can\'t sleep',
        ]
        const msg = messages[Math.floor(Math.random() * messages.length)]

        // Log the interaction
        logInteraction(char.id, targetId, 'text', msg)

        // Target receives the message
        target.receiveInteraction(char, 'text', msg)

        // Update sender's memory
        char.addMemory(`I texted ${target.name}: "${msg}"`, { type: 'action', importance: 4 })
      }
    }
  }
}

/**
 * Process world events
 */
async function processWorldEvents() {
  // Weather changes
  if (Math.random() < 0.01) {
    world.weather.intensity = Math.max(0.3, Math.min(1, world.weather.intensity + (Math.random() - 0.5) * 0.3))
  }

  // Thunder during heavy rain
  if (world.weather.raining && world.weather.intensity > 0.8 && Math.random() < 0.05) {
    world.weather.thunder = true
    setTimeout(() => { world.weather.thunder = false }, 3000)

    // All characters notice thunder
    for (const [id, character] of world.characters) {
      character.observe('Thunder rumbled in the distance', 4)
    }
  }
}

/**
 * Run simulation for N ticks
 */
export async function runSimulation(ticks, options = {}) {
  const results = []

  for (let i = 0; i < ticks; i++) {
    const result = await tick(options)
    results.push(result)

    // Optional delay between ticks for real-time simulation
    if (options.realtime && options.tickDelayMs) {
      await new Promise(r => setTimeout(r, options.tickDelayMs))
    }
  }

  return results
}

/**
 * Start continuous simulation
 */
let simulationInterval = null

export function startContinuousSimulation(tickIntervalMs = 1000, options = {}) {
  if (simulationInterval) return

  simulationInterval = setInterval(async () => {
    await tick(options)
  }, tickIntervalMs)

  return () => stopContinuousSimulation()
}

export function stopContinuousSimulation() {
  if (simulationInterval) {
    clearInterval(simulationInterval)
    simulationInterval = null
  }
}

/**
 * Get simulation state for visualization
 */
export function getSimulationState() {
  const characters = {}

  for (const [id, char] of world.characters) {
    characters[id] = {
      name: char.name,
      apartment: char.apartment,
      mood: char.state.mood,
      energy: char.state.energy,
      currentAction: char.state.currentAction,
      recentMemories: char.memories.slice(-5).map(m => m.text),
    }
  }

  return {
    tick: world.tick,
    time: getTimeString(),
    day: world.day,
    weather: world.weather,
    characters,
  }
}

/**
 * Save simulation state to localStorage (browser) or file (Node)
 */
export function saveState() {
  const state = {
    world: {
      tick: world.tick,
      day: world.day,
      timeOfDay: world.timeOfDay,
      weather: world.weather,
      interactionLog: world.interactionLog,
    },
    characters: Array.from(world.characters.values()).map(c => c.serialize()),
  }

  if (typeof localStorage !== 'undefined') {
    localStorage.setItem('mood42_state', JSON.stringify(state))
  }

  return state
}

/**
 * Load simulation state
 */
export function loadState(state) {
  if (!state && typeof localStorage !== 'undefined') {
    const saved = localStorage.getItem('mood42_state')
    if (saved) state = JSON.parse(saved)
  }

  if (!state) return false

  // Restore world state
  world.tick = state.world.tick
  world.day = state.world.day
  world.timeOfDay = state.world.timeOfDay
  world.weather = state.world.weather
  world.interactionLog = state.world.interactionLog

  // Restore characters
  world.characters.clear()
  for (const charData of state.characters) {
    Character.deserialize(charData)
  }

  return true
}
