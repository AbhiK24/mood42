/**
 * Test the simulation with live Kimi K2 API
 */

const MOONSHOT_API_KEY = 'sk-lbkA0bF4jCQfMP41ddC9Uax6Mry5ehtRmO0dTWyFr4ASTlJL'
const MOONSHOT_BASE_URL = 'https://api.moonshot.ai/v1'
const MODEL = 'kimi-k2-0711-preview'

// Simple character for testing
const maya = {
  name: 'Maya',
  persona: 'A 28-year-old software engineer who moved to NYC from Mumbai two years ago. She works remotely and often codes late into the night.',
  traits: ['introverted', 'analytical', 'night owl', 'homesick'],
  state: { mood: 'focused', energy: 0.7 },
  memories: [
    'Moved into apartment 3B two years ago',
    'Mom called asking when I\'m coming home for Diwali',
    'The rain has been falling all night',
    'Finished a tough debugging session at work',
    'The neighbor\'s light went off at 1am like it always does',
  ]
}

async function callKimi(messages, options = {}) {
  const response = await fetch(`${MOONSHOT_BASE_URL}/chat/completions`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${MOONSHOT_API_KEY}`,
    },
    body: JSON.stringify({
      model: MODEL,
      messages,
      temperature: options.temperature ?? 0.7,
      max_tokens: options.maxTokens ?? 512,
    }),
  })

  const data = await response.json()
  return data.choices[0].message.content
}

async function testReflection() {
  console.log('\n' + '='.repeat(60))
  console.log('TEST 1: REFLECTION')
  console.log('='.repeat(60))

  const memoryText = maya.memories.map(m => `- ${m}`).join('\n')

  const response = await callKimi([
    {
      role: 'system',
      content: `You are ${maya.name}. ${maya.persona}

Your traits: ${maya.traits.join(', ')}

Based on recent experiences, generate 1-2 brief, introspective reflections.
Write in first person, authentically as the character. Keep each to 1-2 sentences.`,
    },
    {
      role: 'user',
      content: `Recent experiences:\n${memoryText}\n\nWhat thoughts or realizations arise?`,
    },
  ], { temperature: 0.8 })

  console.log(`\n[Maya reflects...]`)
  console.log(`"${response}"`)
}

async function testPlan() {
  console.log('\n' + '='.repeat(60))
  console.log('TEST 2: PLANNING')
  console.log('='.repeat(60))

  const response = await callKimi([
    {
      role: 'system',
      content: `You are ${maya.name}. ${maya.persona}

Traits: ${maya.traits.join(', ')}
Current mood: ${maya.state.mood}
Energy: ${Math.round(maya.state.energy * 100)}%

It's 11:30 PM. Generate a simple plan for the next few hours.
Return as a JSON array: [{"time": "11:30 PM", "action": "description", "duration": 30}]
Keep actions authentic. 3-4 items.`,
    },
    {
      role: 'user',
      content: `The rain is falling outside. You just finished work. What will you do?`,
    },
  ])

  console.log(`\n[Maya plans her night...]`)
  console.log(response)
}

async function testDialogue() {
  console.log('\n' + '='.repeat(60))
  console.log('TEST 3: TEXT MESSAGE')
  console.log('='.repeat(60))

  const daniel = {
    name: 'Daniel',
    description: 'the writer who lives in 2A, struggling with his second novel'
  }

  const response = await callKimi([
    {
      role: 'system',
      content: `You are ${maya.name}. ${maya.persona}

You're texting ${daniel.name}, ${daniel.description}. You've seen each other in the hallway a few times.
It's late, you can't sleep. Write a brief, authentic text message (1-2 sentences max).`,
    },
    {
      role: 'user',
      content: `It's 12:30 AM. The rain is heavy. You're feeling a bit lonely. What do you text Daniel?`,
    },
  ], { temperature: 0.9, maxTokens: 100 })

  console.log(`\n[Maya texts Daniel...]`)
  console.log(`"${response}"`)
}

async function testInteraction() {
  console.log('\n' + '='.repeat(60))
  console.log('TEST 4: FULL INTERACTION')
  console.log('='.repeat(60))

  // Maya texts Daniel
  const mayaText = await callKimi([
    {
      role: 'system',
      content: `You are Maya, a 28-year-old software engineer. Write a late-night text to your neighbor Daniel. Be authentic, brief.`,
    },
    {
      role: 'user',
      content: `It's 1 AM, raining. You can't sleep and noticed his light is still on. Text him.`,
    },
  ], { temperature: 0.9, maxTokens: 60 })

  console.log(`\n[1:00 AM - Maya → Daniel]`)
  console.log(`"${mayaText}"`)

  // Daniel responds
  const danielResponse = await callKimi([
    {
      role: 'system',
      content: `You are Daniel, a 34-year-old writer struggling with your second novel. You're up late, avoiding your manuscript. Your neighbor Maya just texted you. Respond authentically, briefly.`,
    },
    {
      role: 'user',
      content: `Maya texted: "${mayaText}"\n\nHow do you respond?`,
    },
  ], { temperature: 0.9, maxTokens: 80 })

  console.log(`\n[1:02 AM - Daniel → Maya]`)
  console.log(`"${danielResponse}"`)

  // Maya's internal reflection after the exchange
  const mayaReflection = await callKimi([
    {
      role: 'system',
      content: `You are Maya. After this brief text exchange with Daniel, what do you think/feel? One sentence internal monologue.`,
    },
    {
      role: 'user',
      content: `You texted: "${mayaText}"\nHe replied: "${danielResponse}"\n\nYour thought:`,
    },
  ], { temperature: 0.8, maxTokens: 60 })

  console.log(`\n[Maya thinks...]`)
  console.log(`(${mayaReflection})`)
}

async function main() {
  console.log('='.repeat(60))
  console.log('MOOD42 SIMULATION TEST - KIMI K2 LIVE')
  console.log('='.repeat(60))
  console.log(`Time: 11:30 PM | Weather: Raining | Location: NYC`)

  try {
    await testReflection()
    await testPlan()
    await testDialogue()
    await testInteraction()

    console.log('\n' + '='.repeat(60))
    console.log('ALL TESTS PASSED - LLM INTEGRATION WORKING')
    console.log('='.repeat(60))
  } catch (error) {
    console.error('Test failed:', error)
  }
}

main()
