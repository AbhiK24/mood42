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

// Music library
export {
  TRACKS,
  PLAYLISTS,
  CHANNEL_PLAYLISTS,
  initMusic,
  playTrack,
  playPlaylist,
  toggle as toggleMusic,
  nextTrack,
  prevTrack,
  setVolume,
  getState as getMusicState,
  getAllTracks,
  addTrack,
  getTracksByMood,
  getTracksByGenre,
  getTracksForChannel,
  getRandomTrackForChannel,
  playChannelMusic,
} from './music.js'

// Channel agents (self-aware programmers)
export {
  initAllChannelAgents,
  initChannelAgent,
  addChannelMemory,
  recordTrackPlayed,
  recordVisualShown,
  recordMoodShift,
  getRecentMemories,
  getChannelHistory,
  formatMemoriesForAgent,
  generateProgrammingDecision,
  generateChannelReflection,
  planChannelProgramming,
  getChannelPlan,
  getRelatedChannelContext,
  exportChannelAgentState,
  importChannelAgentState,
} from './channelAgent.js'

// Channels
export {
  CHANNELS,
  WALL_LAYOUT,
  getAllChannels,
  getChannel,
  getChannelState,
  updateChannelState,
  initChannels,
  getAgentProgrammingPrompt,
  getFeaturedChannels,
} from './channels.js'

// Visuals
export {
  VISUALS,
  CHANNEL_VISUALS,
  getAllVisuals,
  getVisual,
  getVisualsByMood,
  getVisualsByStyle,
  getVisualsForChannel,
  getRandomVisualForChannel,
} from './visuals.js'
