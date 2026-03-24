# mood42 — scene build brief
### for Claude Code

---

## what you are building

a high-fidelity, continuously animated browser scene called **mood42**.
it is a living apartment window — nyc, 11pm, raining — where an AI agent character
sits at a desk and her world visibly changes based on a simulation ticking underneath.

this is the primary product surface. visual quality is everything.
people must want to screenshot it and leave it open all night.

reference: **Studio Ghibli backgrounds × Edward Hopper × Blade Runner 2049 color grading × lo-fi girl format**

---

## tech stack — use these

| layer | tool | why |
|---|---|---|
| scene rendering | **Pixi.js v8** | WebGL-accelerated 2D. smooth 60fps. filters, blur, glow, compositing |
| rain / particles | **Pixi.js ParticleContainer** | thousands of raindrops without killing fps |
| animation timeline | **GSAP** | smooth scene state transitions, eases, morph between moods |
| lighting / glow effects | **Pixi.js filters** — BlurFilter, GlowFilter, ColorMatrixFilter | neon bleed, lamp warmth, neon flicker |
| character animation | **Spine runtime for Pixi** OR hand-keyed GSAP tweens | breathing, head tilt, arm movement |
| sim tick engine | vanilla JS state machine | no overkill needed here |
| build | **Vite** | fast dev, single bundle output |

if Spine is unavailable, use GSAP morphSVG or hand-keyed Pixi Graphics redraws.

---

## scene layout

full viewport. no scroll. one scene, always full screen.

```
┌─────────────────────────────────────────────────┐
│  [cork board]          [city skyline + rain]     │
│                    [window frame / panes]        │
│           [neon sign bleed from outside]         │
│                                                  │
│  [lamp]    [character at desk]     [plant]       │
│         [laptop] [books] [coffee]                │
│              [desk surface]                      │
│                    [floor]                       │
├─────────────────────────────────────────────────┤
│ [clock + sim status — top left HUD]              │
│ [tick feed — bottom left]                        │
│ [mood bar — right edge]                          │
│ [event toast — center, fades in/out]             │
└─────────────────────────────────────────────────┘
```

---

## color palette

```js
const PALETTE = {
  nightInk:    '#080810',  // bg, deep shadow
  rainysky:    '#0d1f3c',  // sky behind city
  lampOak:     '#1e1508',  // warm room shadow
  tungsten:    '#e8c89a',  // lamp light, warm glow
  paper:       '#f2efe8',  // highlights, text
  neonRed:     '#ff4d6d',  // outside neon sign
  neonBlue:    '#4d9fff',  // second neon source
  exitGreen:   '#39ff8a',  // mood bar high state
  steam:       '#606078',  // dim UI text
  skinWarm:    '#c39b78',  // character skin
  hairDark:    '#23160c',  // character hair
  cloth:       '#504b5a',  // character clothing
}
```

---

## layers — render order (back to front)

### 1. sky + atmosphere
- deep gradient: `#040810` top → `#0d1f3c` mid → `#060d1a` horizon
- subtle cloud texture using Pixi noise filter, very slow drift

### 2. city skyline
- ~12 building silhouettes, varying heights, dark fills `#030810`
- lit windows: warm yellow `rgba(255,220,140,0.6)`, scattered, some flicker slowly
- **empire state** silhouette center-right with antenna red blink
- **water tower** on one rooftop
- **THE detail**: one specific window in one specific building. warm light. goes off at exactly 1am sim-time. never explained. always noticed.

### 3. rain
- Pixi ParticleContainer, 300-500 drops
- slight diagonal fall (wind from left), varying speed/opacity/length
- streaks not dots — draw as short lines
- intensity: 0.0 → 1.0 state variable, GSAP transition when toggled
- rain ripples on desk surface when intensity > 0.5

### 4. neon bleed
- two radial light sources bleeding in from outside:
  - **red** `#ff4d6d` — upper right quadrant, "OPEN" sign outside
  - **blue** `#4d9fff` — upper left, second sign
- both use Pixi GlowFilter on an invisible rect
- both flicker: slow sine wave + occasional stutter (2-3 frame dropout, rare)
- neon reflects as colored smear on wet desk surface
- color bleeds onto character face subtly

### 5. window glass + frame
- window divided into 4 panes (2x2 grid)
- frame: dark wood, `rgba(242,239,232,0.06)` lines, ~10px wide
- condensation: 30-50 small water droplets on glass, static, slight transparency
- rain streak trails on glass — faint, slow downward drift
- very subtle reflection of the room interior on glass (low opacity, ColorMatrix tinted)

### 6. room — background objects

**cork board** (left wall, bg)
- warm brown rectangle, slightly tilted 1-2 degrees
- pinned items: 4 small rectangles in different paper colors
- one is clearly a concert/event ticket (distinctive shape)
- one is a photo — just a slightly lighter rectangle with rounded corners
- tiny pushpin dots in corners

**bookshelves suggestion** (far left edge, very dark)
- vertical rectangles, barely visible, more texture than object

**plant** (right side, windowsill)
- terracotta pot
- 5-6 stems with leaves using quadraticCurveTo
- gentle sway animation: each stem on slightly different sine cycle
- more overgrown than tidy

**radiator** (below window, right)
- cast iron shape, dark, barely visible
- very faint warm glow from top when heating is "on" (winter night)

### 7. desk surface
- warm dark wood: `#1e1508` with subtle grain texture (Pixi noise)
- lamp glow pools on surface — warm radial gradient
- desk edge catches light: thin line `rgba(232,200,154,0.2)`

**desk objects:**
- **laptop** — open, screen emits blue-white glow, reflected on face
  - screen content: faint lines suggesting text/code/writing
  - hinge detail
  - closes in WITHDRAWN event
- **coffee cup** — ceramic, steam particles rising (5-8 particles, slow drift)
  - second cup appears in VISITOR event
- **book stack** — 3 books, slightly askew, different thicknesses
  - spines: one warm cream, one muted purple, one dark green
- **phone** — face down, always. occasionally lights up (notification)
  - when it lights, a faint glow around edges. character may or may not look.
- **small plant/succulent** on desk corner
- **notebook** — open, few faint lines suggesting handwriting

### 8. character — the anchor

**design: south asian woman, late 20s, working late on something that matters**

posture states (GSAP tween between them, 2-3s ease):
- `FOCUSED` — upright, slight forward lean, typing
- `THINKING` — leaned back slightly, looking at screen
- `WITHDRAWN` — shoulders dropped, head lower, not typing
- `GOOD` — slight lift, maybe a small movement
- `FLOOR` — moved off chair, sitting against desk leg, knees up

anatomy (draw with Pixi Graphics, smooth curves):
- head: ellipse, `#c39b78` skin, slightly warm
- hair: dark `#23160c`, pulled back loosely, few strands falling forward
  - small bun or loose updo at back
  - 2-3 loose strands framing face — quadraticCurveTo
- neck: short cylinder connecting to torso
- torso: oversized sweater or hoodie, muted dark color `#504b5a` or `#3a3545`
- arms: resting on desk in neutral, move to lap in WITHDRAWN
- hands: subtle, at keyboard or in lap
- legs: not visible in default (desk blocks)

**critical animations:**
- **breathing** — torso height oscillates ±2px on 4s sine cycle. always running.
- **laptop glow on face** — blue-tinted radial gradient on face/chest, pulses very slightly with "typing" rhythm
- **hair micro-movement** — one loose strand moves ±1px on slow 6s cycle
- **eye direction** — not fully drawn but implied by head angle. in THINKING state, head turns 5° toward window.
- **typing** — subtle arm micro-movements every few seconds in FOCUSED state

**mood → visual mapping:**
| sim mood | character state | scene change |
|---|---|---|
| FOCUSED | upright, typing | screen bright, lamp warm |
| WITHDRAWN | slouched, still | screen dims, no typing |
| GOOD | lifted posture | small smile implied by head angle |
| ANXIOUS | slight tension | phone glows, she looks at it |
| FLOOR | sits on floor against desk | chair empty |

### 9. lamp
- floor lamp, right of character
- post: thin dark metal
- shade: simple drum or cone shape
- **lamp glow**: large radial gradient, `rgba(232,200,154,0.15)` center → transparent
  - illuminates everything in its radius with warm color grade (Pixi ColorMatrixFilter)
  - this is the dominant light source in the room
  - intensity: 0.6 at night, 0.3 when candle is lit alongside it

### 10. HUD layer (HTML overlay, not canvas)

**top left — clock + status**
```
11:47
tue, march 24
raining · 48°f · nyc

● WORLD RUNNING
SIM TICK #247
APT 4F · 2ND AVE
MOOD: FOCUSED
```
- font: Cormorant Garamond italic for time, Space Mono for status
- opacity: 0.2-0.3. barely there. part of the aesthetic.

**bottom left — tick feed**
- last 5 sim events, newest at bottom
- fade in on arrival, dim over time
- event ticks in red `rgba(255,77,109,0.7)`, normal ticks in `rgba(242,239,232,0.3)`
- max width 300px

**right edge — mood bar**
- 10 vertical pips
- color reflects mood: warm for focused, green for good, red for withdrawn
- label "MOOD" in Space Mono rotated vertical

**center — event toast**
- fires on major sim events
- Cormorant Garamond italic, large, fades in over 0.8s, holds 3s, fades out
- example: *"she lights a candle."* / *"the light goes off."*

---

## sim state machine

```js
const simState = {
  time: 23 * 60 + 47,       // minutes since midnight
  raining: true,
  rainIntensity: 0.7,        // 0.0 → 1.0
  characterMood: 'FOCUSED',  // FOCUSED | WITHDRAWN | GOOD | ANXIOUS | FLOOR
  lampOn: true,
  objects: {
    laptopOpen: true,
    secondCup: false,
    candle: false,
    phoneGlowing: false,
    characterOnFloor: false,
  },
  tickCount: 0,
  oneAmLightOff: false,
}
```

**tick events** — fire every 5-8s, random from weighted pool:
```js
const tickPool = [
  { text: "she checks her phone. doesn't respond.",   weight: 3, type: 'normal' },
  { text: "types for 3 minutes. deletes it all.",     weight: 3, type: 'normal' },
  { text: "looks out the window. rain picks up.",     weight: 2, type: 'normal' },
  { text: "reaches for coffee. it's cold.",           weight: 3, type: 'normal' },
  { text: "someone texts. she reads it twice.",       weight: 1, type: 'event',  trigger: 'phoneGlow' },
  { text: "the neon outside flickers.",               weight: 2, type: 'normal' },
  { text: "she almost smiles at something on screen.",weight: 1, type: 'event'  },
  { text: "RELATIONSHIP_EVENT: message from riya",   weight: 1, type: 'event',  trigger: 'moodShift' },
  { text: "she stands. stretches. sits back down.",  weight: 2, type: 'normal' },
  { text: "refills coffee. still hot this time.",    weight: 1, type: 'normal' },
]
```

**scene events** — triggered manually (dev) or by sim logic:
```
SECOND_CUP     → secondCup: true, mood: ANXIOUS, toast: "someone's coming."
CANDLE_LIT     → candle: true, mood: GOOD, toast: "she lights a candle."
LAPTOP_CLOSE   → laptopOpen: false, mood: WITHDRAWN, toast: "laptop closes."
TO_FLOOR       → characterOnFloor: true, mood: WITHDRAWN, toast: "she moves to the floor."
RECOVER        → characterOnFloor: false, laptopOpen: true, mood: FOCUSED, toast: "back to it."
ONE_AM         → oneAmLightOff: true, toast: "the light goes off." (fires automatically at 1:00am sim time)
```

---

## lighting model

three light sources, all dynamic:

| source | color | radius | notes |
|---|---|---|---|
| lamp | `#e8c89a` warm | 35% viewport | dominant. always on. dims slightly in candle event |
| laptop screen | `#4d9fff` cool blue | 15% viewport | on character face/chest. off when laptop closes |
| candle | `#ffb43c` orange | 10% viewport | only in CANDLE event. flickers on 12-frame sine |
| neon bleed (red) | `#ff4d6d` | 20% viewport | from outside. always present |
| neon bleed (blue) | `#4d9fff` | 15% viewport | from outside. always present |

implement with Pixi ColorMatrixFilter zones or radial gradient compositing.

---

## rain system

```
particles: 400
speed: 4-12 px/frame (vary per drop)
angle: 5-10° from vertical (slight wind)
length: 12-25px per streak
opacity: 0.05-0.25 per drop
color: rgba(160,185,220,α)
```

- ParticleContainer for performance
- drops reset to top when they exit viewport
- intensity controlled by `rainIntensity` state var
- GSAP tween intensity changes over 3s
- when intensity > 0.6: add distant thunder sound hint (optional)
- condensation on glass: 40 static dots, `rgba(180,200,230,0.15-0.3)`, never move

---

## transition system

all scene state changes go through GSAP:

```js
// example: mood shift to WITHDRAWN
gsap.to(character, { 
  shoulderDrop: 0.08, 
  headTilt: 0.12, 
  duration: 2.5, 
  ease: 'power2.inOut' 
})

gsap.to(lampFilter, { 
  brightness: 0.85, 
  duration: 3, 
  ease: 'sine.inOut' 
})
```

no snapping. everything eases. the world breathes.

---

## performance targets

- 60fps on MacBook Pro M-series
- 45fps minimum on mid-range Windows laptop
- if fps drops below 45: reduce rain particle count by 30%, disable condensation drift
- canvas resolution: `devicePixelRatio` capped at 2

---

## file structure

```
mood42/
├── index.html          # entry point
├── src/
│   ├── main.js         # init, game loop
│   ├── scene/
│   │   ├── sky.js      # sky, city, rain
│   │   ├── room.js     # desk, objects, lamp
│   │   ├── character.js # character draw + animation states
│   │   ├── window.js   # frame, glass, condensation
│   │   └── lighting.js # light sources, filters
│   ├── sim/
│   │   ├── state.js    # simState object
│   │   ├── ticker.js   # tick engine, event pool
│   │   └── events.js   # scene event handlers
│   ├── hud/
│   │   └── hud.js      # HTML overlay: clock, feed, mood bar, toast
│   └── utils/
│       └── math.js     # lerp, clamp, noise helpers
├── package.json
└── vite.config.js
```

---

## what makes this unforgettable

one thing. the **1am light**.

a light in the building across the street. warm. always on when the scene starts.
at exactly 1:00am sim time — it goes off.

no explanation. no toast. just: the light goes off.

the audience notices. wonders. comes back tomorrow to watch for it again.
that's the product.

---

## dev controls (keyboard shortcuts)

```
E       → cycle through scene events
T       → advance sim time +1 hour
R       → toggle rain
M       → cycle character mood
Space   → pause/resume world tick
```

---

## deliverable

single `index.html` + `src/` directory.
`npm run dev` starts Vite dev server.
`npm run build` produces `dist/` with single-page output.
no backend required. sim is client-side only for v0.
