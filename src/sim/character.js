/**
 * Character - an agent with memory, reflection, and planning
 */

import { world, registerCharacter, getTimeString, getTimePeriod } from './world.js'
import {
  createMemory,
  retrieveMemories,
  cumulativeImportance,
  formatMemoriesForPrompt,
} from './memory.js'

export class Character {
  constructor(config) {
    this.id = config.id
    this.name = config.name
    this.apartment = config.apartment // e.g., "3B"
    this.persona = config.persona // Core personality/background
    this.traits = config.traits ?? [] // ["introverted", "creative", "anxious"]
    this.goals = config.goals ?? [] // Long-term goals/desires

    // Memory stream
    this.memories = []
    this.lastReflectionTick = 0
    this.reflectionThreshold = 50 // cumulative importance to trigger reflection

    // Current state
    this.state = {
      mood: config.initialMood ?? 'neutral', // focused, anxious, content, melancholic, energetic
      energy: config.initialEnergy ?? 0.7, // 0-1
      location: 'apartment',
      currentAction: null,
      socialNeed: 0.5, // 0 = satisfied, 1 = lonely
    }

    // Planning
    this.currentPlan = [] // Array of planned actions
    this.planHorizon = 4 * 60 // Plan 4 hours ahead (in minutes)

    // Relationships
    this.relationships = new Map() // characterId -> { familiarity, sentiment, lastInteraction }

    // Register in world
    registerCharacter(this)
  }

  /**
   * Add a memory to the stream
   */
  addMemory(text, options = {}) {
    const memory = createMemory(text, options)
    this.memories.push(memory)

    // Check if reflection is needed
    const cumulative = cumulativeImportance(this.memories, this.lastReflectionTick)
    if (cumulative >= this.reflectionThreshold) {
      this.needsReflection = true
    }

    return memory
  }

  /**
   * Observe something in the environment
   */
  observe(observation, importance = 3) {
    return this.addMemory(observation, { type: 'observation', importance })
  }

  /**
   * Perform an action (logged as memory)
   */
  act(action, importance = 4) {
    this.state.currentAction = action
    return this.addMemory(`I ${action}`, { type: 'action', importance })
  }

  /**
   * Receive a message/interaction from another character
   */
  receiveInteraction(fromCharacter, type, content) {
    const importance = type === 'text' ? 6 : 5

    // Update relationship
    this.updateRelationship(fromCharacter.id, { lastInteraction: world.tick })

    return this.addMemory(
      `${fromCharacter.name} ${type === 'text' ? 'texted me' : 'spoke to me'}: "${content}"`,
      { type: 'dialogue', importance, metadata: { from: fromCharacter.id } }
    )
  }

  /**
   * Update relationship with another character
   */
  updateRelationship(characterId, updates) {
    const existing = this.relationships.get(characterId) ?? {
      familiarity: 0,
      sentiment: 0,
      interactions: 0,
      lastInteraction: 0,
    }

    this.relationships.set(characterId, {
      ...existing,
      ...updates,
      interactions: existing.interactions + 1,
    })
  }

  /**
   * Get relevant memories for current context
   */
  recall(context, limit = 10) {
    return retrieveMemories(this.memories, context, { limit })
  }

  /**
   * Get current situation description for LLM
   */
  getCurrentContext() {
    const period = getTimePeriod()
    const time = getTimeString()

    return {
      time,
      period,
      day: world.day,
      weather: world.weather,
      mood: this.state.mood,
      energy: this.state.energy,
      currentAction: this.state.currentAction,
      location: this.state.location,
    }
  }

  /**
   * Generate a prompt for reflection (to be sent to LLM)
   */
  getReflectionPrompt() {
    const recentMemories = this.memories
      .filter(m => m.tick > this.lastReflectionTick)
      .slice(-20)

    const memoryText = formatMemoriesForPrompt(recentMemories)

    return {
      system: `You are ${this.name}, ${this.persona}.
Your traits: ${this.traits.join(', ')}.
Your goals: ${this.goals.join(', ')}.

Based on recent experiences, generate 1-3 higher-level insights or reflections.
These should be realizations about yourself, others, or your situation.
Be introspective and authentic to the character.`,

      user: `Recent memories:\n${memoryText}\n\nWhat insights or reflections arise from these experiences?`,
    }
  }

  /**
   * Add a reflection (called after LLM generates insights)
   */
  addReflection(insightText) {
    this.lastReflectionTick = world.tick
    this.needsReflection = false
    return this.addMemory(insightText, { type: 'reflection', importance: 8 })
  }

  /**
   * Generate a prompt for planning (to be sent to LLM)
   */
  getPlanningPrompt() {
    const ctx = this.getCurrentContext()
    const relevantMemories = this.recall(`planning ${ctx.period} activities`, 10)
    const memoryText = formatMemoriesForPrompt(relevantMemories.map(r => r.memory))

    // Get current plan if exists
    const currentPlanText = this.currentPlan.length > 0
      ? `Current plan:\n${this.currentPlan.map(p => `- ${p.time}: ${p.action}`).join('\n')}`
      : 'No current plan.'

    return {
      system: `You are ${this.name}, ${this.persona}.
Your traits: ${this.traits.join(', ')}.
Current mood: ${ctx.mood}. Energy level: ${Math.round(ctx.energy * 100)}%.

Generate a plan for the next few hours. Be specific about actions.
Format each action as: TIME - ACTION (DURATION in minutes)
Actions should reflect your personality and current state.`,

      user: `It's ${ctx.time}, Day ${ctx.day}. Weather: ${ctx.weather.raining ? 'Raining' : 'Clear'}.

Relevant memories:\n${memoryText}

${currentPlanText}

What will you do for the next few hours?`,
    }
  }

  /**
   * Set plan (called after LLM generates plan)
   */
  setPlan(planItems) {
    this.currentPlan = planItems.map(item => ({
      time: item.time,
      action: item.action,
      duration: item.duration ?? 30,
      started: false,
      completed: false,
    }))
  }

  /**
   * Check if current plan needs adjustment
   */
  shouldReplan(trigger = null) {
    // Replan if no plan
    if (this.currentPlan.length === 0) return true

    // Replan if all items completed
    if (this.currentPlan.every(p => p.completed)) return true

    // Replan on significant triggers
    if (trigger && trigger.importance >= 7) return true

    return false
  }

  /**
   * Get the next planned action
   */
  getNextPlannedAction() {
    return this.currentPlan.find(p => !p.completed && !p.started)
  }

  /**
   * Start executing a planned action
   */
  startAction(planItem) {
    planItem.started = true
    planItem.startTick = world.tick
    this.state.currentAction = planItem.action
    this.act(planItem.action, 3)
  }

  /**
   * Complete current action
   */
  completeCurrentAction() {
    const current = this.currentPlan.find(p => p.started && !p.completed)
    if (current) {
      current.completed = true
      this.state.currentAction = null
    }
  }

  /**
   * Serialize character state for persistence
   */
  serialize() {
    return {
      id: this.id,
      name: this.name,
      apartment: this.apartment,
      persona: this.persona,
      traits: this.traits,
      goals: this.goals,
      memories: this.memories,
      lastReflectionTick: this.lastReflectionTick,
      state: this.state,
      currentPlan: this.currentPlan,
      relationships: Array.from(this.relationships.entries()),
    }
  }

  /**
   * Restore character from serialized state
   */
  static deserialize(data) {
    const character = new Character({
      id: data.id,
      name: data.name,
      apartment: data.apartment,
      persona: data.persona,
      traits: data.traits,
      goals: data.goals,
      initialMood: data.state.mood,
      initialEnergy: data.state.energy,
    })

    character.memories = data.memories
    character.lastReflectionTick = data.lastReflectionTick
    character.state = data.state
    character.currentPlan = data.currentPlan
    character.relationships = new Map(data.relationships)

    return character
  }
}
