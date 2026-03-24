/**
 * Demo - Run the simulation in console to test
 *
 * Run with: node --experimental-specifier-resolution=node src/sim/demo.js
 * Or import in browser console
 */

import {
  initializeBuilding,
  getAllCharacters,
  runSimulation,
  getSimulationState,
  tick,
  world,
  getTimeString,
} from './index.js'

async function demo() {
  console.log('=' .repeat(60))
  console.log('MOOD42 SIMULATION DEMO')
  console.log('=' .repeat(60))

  // Initialize the building with all three characters
  console.log('\n[Initializing Building...]')
  const { maya, daniel, iris } = initializeBuilding()

  console.log('\nCharacters:')
  for (const char of getAllCharacters()) {
    console.log(`  ${char.apartment}: ${char.name}`)
    console.log(`     Mood: ${char.state.mood}, Energy: ${Math.round(char.state.energy * 100)}%`)
    console.log(`     Traits: ${char.traits.join(', ')}`)
    console.log(`     Recent memories:`)
    char.memories.slice(-3).forEach(m => {
      console.log(`       - ${m.text}`)
    })
    console.log()
  }

  // Run simulation for 12 ticks (1 hour at 5 min/tick)
  console.log('[Running simulation for 1 hour...]')
  console.log('-'.repeat(60))

  for (let i = 0; i < 12; i++) {
    await tick({ verbose: true, minutesPerTick: 5 })
    console.log()
  }

  console.log('-'.repeat(60))
  console.log('\n[Final State]')

  const state = getSimulationState()
  console.log(`Time: ${state.time}, Day ${state.day}`)
  console.log(`Weather: ${state.weather.raining ? 'Raining' : 'Clear'} (intensity: ${state.weather.intensity.toFixed(2)})`)

  console.log('\nCharacter States:')
  for (const [id, charState] of Object.entries(state.characters)) {
    console.log(`  ${charState.name} (${charState.apartment}):`)
    console.log(`    Mood: ${charState.mood}`)
    console.log(`    Energy: ${Math.round(charState.energy * 100)}%`)
    console.log(`    Current: ${charState.currentAction || 'idle'}`)
    console.log(`    Recent:`)
    charState.recentMemories.forEach(m => console.log(`      - ${m}`))
    console.log()
  }

  // Show relationships
  console.log('\nRelationships:')
  for (const char of getAllCharacters()) {
    if (char.relationships.size > 0) {
      console.log(`  ${char.name}:`)
      for (const [targetId, rel] of char.relationships) {
        const target = world.characters.get(targetId)
        console.log(`    → ${target?.name || targetId}: familiarity ${rel.familiarity.toFixed(2)}, sentiment ${rel.sentiment.toFixed(2)}`)
      }
    }
  }

  console.log('\n' + '='.repeat(60))
  console.log('DEMO COMPLETE')
  console.log('='.repeat(60))
}

// Export for use in browser
export { demo }

// Run if executed directly
if (typeof process !== 'undefined' && process.argv[1]?.includes('demo')) {
  demo().catch(console.error)
}
