/**
 * Simulation Module - Public API
 */

// World state
export { world, getTimeString, getTimePeriod, advanceWorldTime, getCharacter } from './world.js'

// Memory system
export { createMemory, retrieveMemories, formatMemoriesForPrompt } from './memory.js'

// Character class
export { Character } from './character.js'

// Simulation engine
export {
  tick,
  runSimulation,
  startContinuousSimulation,
  stopContinuousSimulation,
  getSimulationState,
  saveState,
  loadState,
  setLLMInterface,
  initializeLLM,
} from './engine.js'

// Building and characters
export {
  CHARACTER_TEMPLATES,
  initializeBuilding,
  getAllCharacters,
  getCharacterByApartment,
  BUILDING_LAYOUT,
  isWindowLit,
  getApartmentScene,
} from './building.js'

// Legacy exports for backward compatibility
export { simState, cycleMood, advanceTime } from './state.js'

// Bridge for visual integration
export {
  initSimulation,
  setActiveCharacter,
  getActiveCharacter,
  syncVisualState,
  simulationTick,
  getBuildingView,
  getCharacterDetail,
  viewerInteraction,
  getMemoryDive,
} from './bridge.js'

// LLM integration (Kimi K2)
export {
  initLLM,
  callKimi,
  generateReflection,
  generatePlan,
  generateMessage,
  rateImportance,
  generateScenePrompt,
  createLLMInterface,
} from './llm.js'
