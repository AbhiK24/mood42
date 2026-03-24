// Scene events for mood42

import { simState, setMood } from './state.js'

export const sceneEvents = [
  {
    name: 'second cup appears',
    sub: 'RELATIONSHIP_EVENT · VISITOR INCOMING',
    action: () => {
      simState.objects.secondCup = true
      setMood('ANXIOUS')
    }
  },
  {
    name: 'she lights a candle.',
    sub: 'MOOD_SHIFT · SOMETHING RESOLVED',
    action: () => {
      simState.objects.candle = true
      setMood('GOOD')
    }
  },
  {
    name: 'laptop closes.',
    sub: 'SIM_EVENT · EMOTIONAL WEIGHT · DONE FOR NIGHT',
    action: () => {
      simState.objects.laptopOpen = false
      setMood('WITHDRAWN')
    }
  },
  {
    name: 'she moves\nto the floor.',
    sub: 'CONFLICT_EVENT · SHE\'S NOT OK',
    action: () => {
      simState.objects.characterOnFloor = true
      setMood('FLOOR')
    }
  },
  {
    name: 'she opens\nthe laptop.',
    sub: 'MOOD_RECOVERY · BACK TO WORK',
    action: () => {
      simState.objects.laptopOpen = true
      simState.objects.characterOnFloor = false
      setMood('FOCUSED')
    }
  },
]

let eventIndex = 0

export function triggerNextEvent() {
  const evt = sceneEvents[eventIndex % sceneEvents.length]
  evt.action()
  eventIndex++
  return evt
}

export function resetEvents() {
  eventIndex = 0
}
