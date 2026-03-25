/**
 * Channel Agent System
 * Each channel is a self-aware AI agent with memory, planning, and programming decisions
 * Based on Stanford Generative Agents architecture
 */

import { CHANNELS } from './channels.js'
import { world } from './world.js'
import { callKimi } from './llm.js'

// Memory streams for each channel agent
const channelMemories = new Map()

// Planning state for each channel
const channelPlans = new Map()

// Programming history (what was played)
const channelHistory = new Map()

/**
 * Initialize a channel agent
 */
export function initChannelAgent(channelId) {
  const channel = CHANNELS[channelId]
  if (!channel) return

  channelMemories.set(channelId, [])
  channelPlans.set(channelId, {
    currentPlan: null,
    lastPlannedAt: null,
    upNext: [],
  })
  channelHistory.set(channelId, {
    tracks: [],
    visuals: [],
    moods: [],
    sessions: [],
  })
}

/**
 * Initialize all channel agents
 */
export function initAllChannelAgents() {
  Object.keys(CHANNELS).forEach(initChannelAgent)
}

/**
 * Add a memory to channel's memory stream
 */
export function addChannelMemory(channelId, memory) {
  const memories = channelMemories.get(channelId)
  if (!memories) return

  const entry = {
    id: `mem_${channelId}_${Date.now()}`,
    timestamp: Date.now(),
    worldTime: world.timeOfDay,
    type: memory.type, // 'track_played', 'visual_shown', 'mood_shift', 'reflection', 'viewer_interaction'
    content: memory.content,
    importance: memory.importance || 5,
    embedding: null, // for future vector search
  }

  memories.push(entry)

  // Keep last 100 memories per channel
  if (memories.length > 100) {
    memories.shift()
  }

  return entry
}

/**
 * Record that a track was played
 */
export function recordTrackPlayed(channelId, track) {
  const history = channelHistory.get(channelId)
  if (!history) return

  history.tracks.push({
    trackId: track.id,
    name: track.name,
    playedAt: Date.now(),
    worldTime: world.timeOfDay,
    mood: track.mood,
  })

  // Add to memory stream
  addChannelMemory(channelId, {
    type: 'track_played',
    content: `Played "${track.name}" (${track.mood?.join(', ') || 'ambient'})`,
    importance: 3,
  })

  // Keep last 50 tracks
  if (history.tracks.length > 50) {
    history.tracks.shift()
  }
}

/**
 * Record that a visual was shown
 */
export function recordVisualShown(channelId, visual) {
  const history = channelHistory.get(channelId)
  if (!history) return

  history.visuals.push({
    visualId: visual.id,
    description: visual.description,
    shownAt: Date.now(),
    worldTime: world.timeOfDay,
  })

  addChannelMemory(channelId, {
    type: 'visual_shown',
    content: `Displayed visual: ${visual.description}`,
    importance: 2,
  })

  if (history.visuals.length > 50) {
    history.visuals.shift()
  }
}

/**
 * Record a mood shift
 */
export function recordMoodShift(channelId, fromMood, toMood, reason) {
  const history = channelHistory.get(channelId)
  if (!history) return

  history.moods.push({
    from: fromMood,
    to: toMood,
    reason,
    at: Date.now(),
    worldTime: world.timeOfDay,
  })

  addChannelMemory(channelId, {
    type: 'mood_shift',
    content: `Mood shifted from ${fromMood} to ${toMood}: ${reason}`,
    importance: 6,
  })
}

/**
 * Get recent memories for context
 */
export function getRecentMemories(channelId, count = 10) {
  const memories = channelMemories.get(channelId) || []
  return memories.slice(-count)
}

/**
 * Get channel's programming history
 */
export function getChannelHistory(channelId) {
  return channelHistory.get(channelId) || { tracks: [], visuals: [], moods: [], sessions: [] }
}

/**
 * Format memories for LLM prompt
 */
export function formatMemoriesForAgent(channelId) {
  const memories = getRecentMemories(channelId, 15)
  if (memories.length === 0) return 'No recent memories.'

  return memories.map(m => {
    const timeAgo = Math.floor((Date.now() - m.timestamp) / 60000)
    return `[${timeAgo}m ago] ${m.content}`
  }).join('\n')
}

/**
 * Generate the next programming decision using AI
 */
export async function generateProgrammingDecision(channelId, availableTracks, availableVisuals) {
  const channel = CHANNELS[channelId]
  if (!channel) return null

  const hour = Math.floor((world.timeOfDay || 0) / 60) % 24
  const timeOfDay = hour >= 5 && hour < 12 ? 'morning' :
                    hour >= 12 && hour < 17 ? 'afternoon' :
                    hour >= 17 && hour < 21 ? 'evening' : 'late night'

  const memories = formatMemoriesForAgent(channelId)
  const history = getChannelHistory(channelId)
  const recentTracks = history.tracks.slice(-5).map(t => t.name).join(', ') || 'none yet'

  const prompt = {
    system: `You are ${channel.agent.name}, the AI programmer of the "${channel.name}" channel.

${channel.agent.persona}

Your musical taste: ${channel.agent.taste.join(', ')}
Your visual style: ${channel.agent.visualStyle.join(', ')}
Your pacing: ${channel.agent.pacing}

RECENT MEMORIES:
${memories}

RECENT TRACKS PLAYED:
${recentTracks}

TIME: It's ${timeOfDay} (${hour}:00)

AVAILABLE TRACKS:
${availableTracks.map(t => `- ${t.id}: "${t.name}" (mood: ${t.mood?.join(', ')})`).join('\n')}

AVAILABLE VISUALS:
${availableVisuals.map(v => `- ${v.id}: ${v.description}`).join('\n')}

Based on your persona, the time, and your recent programming history, decide what to play next.
Return JSON: {
  "trackId": "id of track to play",
  "visualId": "id of visual to show",
  "mood": "current mood word",
  "thought": "your internal thought (1-2 sentences)",
  "transitionStyle": "cut" | "crossfade" | "slow-fade"
}`,

    user: `What should play next on ${channel.name}?`,
  }

  try {
    const response = await callKimi([
      { role: 'system', content: prompt.system },
      { role: 'user', content: prompt.user },
    ], { temperature: 0.8, maxTokens: 200 })

    let decision
    try {
      decision = JSON.parse(response)
    } catch {
      decision = { thought: response, mood: channel.currentMood }
    }

    // Record the decision as a reflection
    addChannelMemory(channelId, {
      type: 'reflection',
      content: `Decided: ${decision.thought}`,
      importance: 4,
    })

    return decision
  } catch (err) {
    console.error(`[${channelId}] Programming decision failed:`, err)
    return null
  }
}

/**
 * Generate a reflection on recent programming
 */
export async function generateChannelReflection(channelId) {
  const channel = CHANNELS[channelId]
  if (!channel) return null

  const memories = formatMemoriesForAgent(channelId)
  const history = getChannelHistory(channelId)

  const prompt = {
    system: `You are ${channel.agent.name}, programmer of "${channel.name}".

${channel.agent.persona}

Review your recent programming decisions and reflect on them.

RECENT MEMORIES:
${memories}

Generate a brief reflection (2-3 sentences) about your programming choices and what you might do differently or continue doing.`,

    user: 'Reflect on your recent programming.',
  }

  try {
    const response = await callKimi([
      { role: 'system', content: prompt.system },
      { role: 'user', content: prompt.user },
    ], { temperature: 0.9, maxTokens: 150 })

    // Store reflection
    addChannelMemory(channelId, {
      type: 'reflection',
      content: response,
      importance: 7,
    })

    return response
  } catch (err) {
    console.error(`[${channelId}] Reflection failed:`, err)
    return null
  }
}

/**
 * Plan the next hour of programming
 */
export async function planChannelProgramming(channelId) {
  const channel = CHANNELS[channelId]
  if (!channel) return null

  const hour = Math.floor((world.timeOfDay || 0) / 60) % 24
  const timeOfDay = hour >= 5 && hour < 12 ? 'morning' :
                    hour >= 12 && hour < 17 ? 'afternoon' :
                    hour >= 17 && hour < 21 ? 'evening' : 'late night'

  const prompt = {
    system: `You are ${channel.agent.name}, programmer of "${channel.name}".

${channel.agent.persona}

It's ${timeOfDay}. Plan your programming for the next hour.

Consider:
- Your musical taste: ${channel.agent.taste.join(', ')}
- Your visual style: ${channel.agent.visualStyle.join(', ')}
- Your pacing preference: ${channel.agent.pacing}
- The time of day and how it affects mood

Return JSON: {
  "plan": "brief description of the vibe you're going for",
  "segments": [
    { "duration": "15min", "mood": "...", "musicVibe": "...", "visualVibe": "..." }
  ],
  "thought": "your reasoning"
}`,

    user: `Plan the next hour of ${channel.name}.`,
  }

  try {
    const response = await callKimi([
      { role: 'system', content: prompt.system },
      { role: 'user', content: prompt.user },
    ], { temperature: 0.8, maxTokens: 300 })

    let plan
    try {
      plan = JSON.parse(response)
    } catch {
      plan = { plan: response, segments: [] }
    }

    // Store the plan
    const plans = channelPlans.get(channelId)
    if (plans) {
      plans.currentPlan = plan
      plans.lastPlannedAt = Date.now()
    }

    addChannelMemory(channelId, {
      type: 'reflection',
      content: `Planned: ${plan.plan || plan.thought || 'new programming block'}`,
      importance: 5,
    })

    return plan
  } catch (err) {
    console.error(`[${channelId}] Planning failed:`, err)
    return null
  }
}

/**
 * Get channel's current plan
 */
export function getChannelPlan(channelId) {
  return channelPlans.get(channelId)
}

/**
 * Cross-channel awareness: what are related channels doing?
 */
export function getRelatedChannelContext(channelId) {
  const channel = CHANNELS[channelId]
  if (!channel) return ''

  const related = channel.agent.relationships || []
  const context = related.map(relId => {
    const relChannel = CHANNELS[relId]
    if (!relChannel) return null

    const relMemories = getRecentMemories(relId, 3)
    const lastMemory = relMemories[relMemories.length - 1]

    return `${relChannel.agent.name} (${relChannel.name}): ${lastMemory?.content || 'quiet'}`
  }).filter(Boolean)

  return context.join('\n')
}

/**
 * Export state for persistence
 */
export function exportChannelAgentState(channelId) {
  return {
    memories: channelMemories.get(channelId) || [],
    plans: channelPlans.get(channelId) || {},
    history: channelHistory.get(channelId) || {},
  }
}

/**
 * Import state from persistence
 */
export function importChannelAgentState(channelId, state) {
  if (state.memories) channelMemories.set(channelId, state.memories)
  if (state.plans) channelPlans.set(channelId, state.plans)
  if (state.history) channelHistory.set(channelId, state.history)
}
