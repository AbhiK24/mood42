/**
 * Memory System - storage, retrieval with recency/importance/relevance scoring
 */

import { world } from './world.js'

/**
 * Create a new memory
 */
export function createMemory(text, options = {}) {
  return {
    id: `mem_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    tick: world.tick,
    time: world.timeOfDay,
    day: world.day,
    text,
    importance: options.importance ?? 5, // 1-10, will be rated by LLM later
    type: options.type ?? 'observation', // observation, action, reflection, dialogue, plan
    embedding: options.embedding ?? null, // for semantic similarity (future)
    metadata: options.metadata ?? {},
  }
}

/**
 * Calculate recency score (exponential decay)
 * More recent = higher score
 */
export function recencyScore(memory, decayFactor = 0.995) {
  const ticksAgo = world.tick - memory.tick
  return Math.pow(decayFactor, ticksAgo)
}

/**
 * Calculate importance score (normalized 0-1)
 */
export function importanceScore(memory) {
  return memory.importance / 10
}

/**
 * Calculate relevance score (keyword-based for now, embeddings later)
 * Returns 0-1 based on how relevant the memory is to the context
 */
export function relevanceScore(memory, context) {
  if (!context) return 0.5 // neutral if no context

  const memoryWords = new Set(memory.text.toLowerCase().split(/\s+/))
  const contextWords = context.toLowerCase().split(/\s+/)

  let matches = 0
  for (const word of contextWords) {
    if (memoryWords.has(word) && word.length > 3) {
      matches++
    }
  }

  return Math.min(1, matches / Math.max(contextWords.length, 1) * 3)
}

/**
 * Retrieve memories with combined scoring
 */
export function retrieveMemories(memories, context = null, options = {}) {
  const {
    limit = 10,
    recencyWeight = 1.0,
    importanceWeight = 1.0,
    relevanceWeight = 1.0,
    minScore = 0,
  } = options

  const scored = memories.map(memory => {
    const recency = recencyScore(memory) * recencyWeight
    const importance = importanceScore(memory) * importanceWeight
    const relevance = relevanceScore(memory, context) * relevanceWeight

    const totalScore = (recency + importance + relevance) / 3

    return { memory, score: totalScore, recency, importance, relevance }
  })

  return scored
    .filter(m => m.score >= minScore)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit)
}

/**
 * Get memories above importance threshold (for reflection triggers)
 */
export function getImportantMemories(memories, since = 0, threshold = 6) {
  return memories.filter(m => m.tick >= since && m.importance >= threshold)
}

/**
 * Calculate cumulative importance since last reflection
 */
export function cumulativeImportance(memories, sinceReflection = 0) {
  return memories
    .filter(m => m.tick > sinceReflection && m.type !== 'reflection')
    .reduce((sum, m) => sum + m.importance, 0)
}

/**
 * Format memories for LLM context
 */
export function formatMemoriesForPrompt(memories, maxTokens = 2000) {
  let output = ''
  let approxTokens = 0

  for (const mem of memories) {
    const line = `[Day ${mem.day}, ${formatTime(mem.time)}] ${mem.text}\n`
    const lineTokens = line.length / 4 // rough approximation

    if (approxTokens + lineTokens > maxTokens) break

    output += line
    approxTokens += lineTokens
  }

  return output
}

function formatTime(minutes) {
  const hours = Math.floor(minutes / 60) % 24
  const mins = minutes % 60
  const period = hours >= 12 ? 'PM' : 'AM'
  const h = hours % 12 || 12
  return `${h}:${mins.toString().padStart(2, '0')} ${period}`
}
