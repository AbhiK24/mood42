/**
 * LLM Client - Kimi K2 (Moonshot AI) via OpenAI-compatible API
 *
 * Set VITE_MOONSHOT_API_KEY in .env or pass key directly
 */

const MOONSHOT_BASE_URL = 'https://api.moonshot.ai/v1'
const MODEL = 'kimi-k2-0711-preview'

let apiKey = null

/**
 * Initialize the LLM client with API key
 */
export function initLLM(key) {
  apiKey = key || import.meta.env?.VITE_MOONSHOT_API_KEY
  if (!apiKey) {
    console.warn('[LLM] No API key set - using mock responses')
  }
  return !!apiKey
}

/**
 * Call Kimi API
 */
export async function callKimi(messages, options = {}) {
  if (!apiKey) {
    return mockResponse(messages, options)
  }

  const {
    temperature = 0.7,
    maxTokens = 1024,
    responseFormat = null,
  } = options

  try {
    const body = {
      model: MODEL,
      messages,
      temperature,
      max_tokens: maxTokens,
    }

    if (responseFormat) {
      body.response_format = responseFormat
    }

    const response = await fetch(`${MOONSHOT_BASE_URL}/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${apiKey}`,
      },
      body: JSON.stringify(body),
    })

    if (!response.ok) {
      throw new Error(`Kimi API error: ${response.status}`)
    }

    const data = await response.json()
    return data.choices[0].message.content
  } catch (error) {
    console.error('[LLM] API call failed:', error)
    return mockResponse(messages, options)
  }
}

/**
 * Generate a reflection for a character
 */
export async function generateReflection(character, recentMemories) {
  const memoryText = recentMemories
    .map(m => `- ${m.text}`)
    .join('\n')

  const messages = [
    {
      role: 'system',
      content: `You are ${character.name}. ${character.persona}

Your traits: ${character.traits.join(', ')}

Based on recent experiences, generate 1-2 brief, introspective reflections.
These should be realizations about yourself, your situation, or your feelings.
Write in first person, authentically as the character.
Keep each reflection to 1-2 sentences.`,
    },
    {
      role: 'user',
      content: `Recent experiences:\n${memoryText}\n\nWhat thoughts or realizations arise?`,
    },
  ]

  return callKimi(messages, { temperature: 0.8, maxTokens: 256 })
}

/**
 * Generate a plan for a character
 */
export async function generatePlan(character, context, relevantMemories) {
  const memoryText = relevantMemories
    .slice(0, 8)
    .map(m => `- ${m.text}`)
    .join('\n')

  const messages = [
    {
      role: 'system',
      content: `You are ${character.name}. ${character.persona}

Traits: ${character.traits.join(', ')}
Current mood: ${character.state.mood}
Energy: ${Math.round(character.state.energy * 100)}%

Generate a simple plan for the next few hours. Return as JSON array:
[{"time": "11:30 PM", "action": "brief action description", "duration": 30}]

Keep actions simple and authentic to the character. 3-5 items max.`,
    },
    {
      role: 'user',
      content: `It's ${context.time}, Day ${context.day}. Weather: ${context.weather.raining ? 'Raining' : 'Clear'}.

Recent context:\n${memoryText}

What will you do?`,
    },
  ]

  const response = await callKimi(messages, {
    temperature: 0.7,
    maxTokens: 512,
    responseFormat: { type: 'json_object' },
  })

  try {
    const parsed = JSON.parse(response)
    return Array.isArray(parsed) ? parsed : parsed.plan || []
  } catch {
    // Parse from text if JSON fails
    return parseTextPlan(response)
  }
}

/**
 * Generate dialogue/text message between characters
 */
export async function generateMessage(fromChar, toChar, context) {
  const messages = [
    {
      role: 'system',
      content: `You are ${fromChar.name}. ${fromChar.persona}

You're texting ${toChar.name}, who you know from the building.
Write a brief, authentic text message (1-2 sentences max).
Match the time of day and your current mood: ${fromChar.state.mood}`,
    },
    {
      role: 'user',
      content: `It's ${context.time}. What do you text ${toChar.name}?`,
    },
  ]

  return callKimi(messages, { temperature: 0.9, maxTokens: 100 })
}

/**
 * Rate importance of a memory (1-10)
 */
export async function rateImportance(character, memoryText) {
  const messages = [
    {
      role: 'system',
      content: `You are evaluating the importance of an experience for ${character.name}.
Rate from 1-10 where:
1-3: Mundane, routine
4-6: Notable, worth remembering
7-9: Significant, emotionally impactful
10: Life-changing

Return only a number.`,
    },
    {
      role: 'user',
      content: memoryText,
    },
  ]

  const response = await callKimi(messages, { temperature: 0.3, maxTokens: 10 })
  const num = parseInt(response.trim())
  return isNaN(num) ? 5 : Math.min(10, Math.max(1, num))
}

/**
 * Generate a scene prompt for memory visualization
 */
export async function generateScenePrompt(character, memory) {
  const messages = [
    {
      role: 'system',
      content: `Generate a brief visual scene description for AI image generation.
Style: Lo-fi anime, Studio Ghibli inspired, atmospheric, emotional.
Include: character appearance, setting, lighting, mood.
Keep under 100 words.`,
    },
    {
      role: 'user',
      content: `Character: ${character.name}, ${character.persona.split('.')[0]}
Memory: ${memory.text}
Time: ${memory.time >= 1200 || memory.time < 360 ? 'night' : 'day'}`,
    },
  ]

  return callKimi(messages, { temperature: 0.7, maxTokens: 150 })
}

/**
 * Mock responses when no API key
 */
function mockResponse(messages, options) {
  const lastMessage = messages[messages.length - 1]?.content || ''

  // Reflection mock
  if (lastMessage.includes('thoughts') || lastMessage.includes('realizations')) {
    const reflections = [
      "I wonder if everyone in this building feels as untethered as I do.",
      "The rain makes everything feel more real somehow.",
      "Maybe I've been hiding from something I need to face.",
      "There's comfort in routine, even lonely routine.",
      "I should reach out to someone. Anyone.",
    ]
    return reflections[Math.floor(Math.random() * reflections.length)]
  }

  // Plan mock
  if (lastMessage.includes('What will you do')) {
    return JSON.stringify([
      { time: "11:30 PM", action: "finish current task", duration: 30 },
      { time: "12:00 AM", action: "make tea, stare out window", duration: 15 },
      { time: "12:15 AM", action: "try to read", duration: 45 },
    ])
  }

  // Text message mock
  if (lastMessage.includes('text')) {
    const texts = [
      "hey, you up?",
      "can't sleep either?",
      "the rain is nice tonight",
      "random thought - are you okay?",
    ]
    return texts[Math.floor(Math.random() * texts.length)]
  }

  // Importance mock
  if (lastMessage.length < 200) {
    return String(Math.floor(Math.random() * 4) + 3) // 3-6
  }

  return "I'm not sure what to say."
}

/**
 * Parse a text plan into structured format
 */
function parseTextPlan(text) {
  const lines = text.split('\n').filter(l => l.trim())
  const plan = []

  for (const line of lines) {
    const match = line.match(/(\d{1,2}:\d{2}\s*(?:AM|PM)?)\s*[-:]\s*(.+)/i)
    if (match) {
      plan.push({
        time: match[1].trim(),
        action: match[2].trim(),
        duration: 30,
      })
    }
  }

  return plan.length > 0 ? plan : [
    { time: "now", action: "continue with current activity", duration: 30 }
  ]
}

/**
 * Create LLM interface for simulation engine
 */
export function createLLMInterface() {
  return {
    async reflect(character) {
      const recentMemories = character.memories
        .filter(m => m.tick > character.lastReflectionTick)
        .slice(-15)
      return generateReflection(character, recentMemories)
    },

    async plan(character) {
      const ctx = character.getCurrentContext()
      const memories = character.recall(`planning ${ctx.period}`, 10)
      return generatePlan(character, ctx, memories.map(r => r.memory))
    },

    async rateImportance(memory) {
      // Use simple heuristics for now to reduce API calls
      const text = memory.text.toLowerCase()
      if (text.includes('realized') || text.includes('understand')) return 8
      if (text.includes('texted') || text.includes('spoke') || text.includes('said')) return 6
      if (text.includes('feel')) return 5
      return 3
    },

    async decideAction(character, context) {
      const next = character.getNextPlannedAction()
      return { type: next ? 'follow_plan' : 'idle', action: next }
    },
  }
}
