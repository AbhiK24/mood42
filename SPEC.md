# mood42 — agentically programmed tv

## ONE-LINER
A wall of AI-programmed TV channels. Tune in. Zone out. It's always on.

---

## THE VISION

Television died when it asked you to choose. Netflix killed the channel.
We're bringing it back — but the programmers are AI.

**mood42** is a wall of screens. Each screen is a channel. Each channel is programmed by an AI agent that curates music, visuals, and narrative in real-time. You don't search. You don't scroll. You tune in.

All content is open source. All music is royalty-free. The AI is the DJ, VJ, and showrunner. This is generative television for the ambient age.

---

## THE INTERFACE

```
┌─────────────────────────────────────────────────────────────────┐
│                         MOOD42.TV                                │
│                                                                  │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│   │ CH 01   │ │ CH 02   │ │ CH 03   │ │ CH 04   │ │ CH 05   │  │
│   │ ~~~~~~  │ │ ~~~~~~  │ │ ~~~~~~  │ │ ~~~~~~  │ │ ~~~~~~  │  │
│   │ lofi    │ │ rain    │ │ jazz    │ │ synth   │ │ ambient │  │
│   │ night   │ │ cafe    │ │ noir    │ │ drive   │ │ space   │  │
│   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │
│   ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐  │
│   │ CH 06   │ │ CH 07   │ │ CH 08   │ │ CH 09   │ │ CH 10   │  │
│   │ ~~~~~~  │ │ ~~~~~~  │ │ ~~~~~~  │ │ ~~~~~~  │ │ ~~~~~~  │  │
│   │ drama   │ │ chill   │ │ focus   │ │ melancholy│ │ dawn   │  │
│   └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘  │
│                                                                  │
│                    [ CLICK ANY CHANNEL TO TUNE IN ]             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Tuned In View:**
```
┌─────────────────────────────────────────────────────────────────┐
│ CH 03 · JAZZ NOIR                                    [ESC] back │
│─────────────────────────────────────────────────────────────────│
│                                                                  │
│                                                                  │
│                    ┌─────────────────────────┐                  │
│                    │                         │                  │
│                    │   [ FULLSCREEN VISUAL ] │                  │
│                    │                         │                  │
│                    │   rain on window        │                  │
│                    │   saxophone playing     │                  │
│                    │   2:47 AM               │                  │
│                    │                         │                  │
│                    └─────────────────────────┘                  │
│                                                                  │
│                    ♪ Art Tatum - Willow Weep For Me             │
│                    ○○○●○○○○○○ vol                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## CORE PRINCIPLES

### 1. PASSIVE CONSUMPTION
No choices. No algorithms asking what you want. You tune in like it's 1995.
The AI decides what plays. You watch. That's the point.

### 2. OPEN SOURCE EVERYTHING
- **Music**: Creative Commons, royalty-free, public domain
- **Visuals**: AI-generated, open source clips, CC-licensed footage
- **Code**: MIT license, fork it, run your own station

### 3. AGENTS AS PROGRAMMERS
Each channel has an AI agent (persona) that:
- Curates the music playlist
- Sequences the visuals
- Maintains the mood
- Evolves the vibe over hours/days

### 4. ALWAYS ON
Channels run 24/7. Time of day affects programming.
- 2 AM: slower, darker, introspective
- 6 AM: gradual awakening
- 10 PM: peak mood, full immersion

---

## CHANNEL ANATOMY

Each channel is defined by:

```javascript
{
  id: "ch03",
  name: "Jazz Noir",
  agent: {
    persona: "A late-night radio DJ from 1958...",
    taste: ["jazz", "blues", "noir"],
    visualStyle: ["rain", "city", "shadows", "smoke"],
    pacing: "slow",
  },
  musicSources: [
    "freemusicarchive.org/jazz",
    "musopen.org",
    "incompetech.com",
  ],
  visualSources: [
    "/visuals/rain/",
    "/visuals/city-night/",
    "ai-generated",
  ],
  schedule: {
    lateNight: { tempo: "slow", mood: "melancholic" },
    morning: { tempo: "medium", mood: "hopeful" },
  }
}
```

---

## THE STACK

```
┌──────────────────────────────────────────┐
│            FRONTEND (Browser)            │
│  Pixi.js visuals + Web Audio API         │
└────────────────────┬─────────────────────┘
                     │
┌────────────────────▼─────────────────────┐
│           CHANNEL ENGINE                  │
│  - Music queue + crossfade               │
│  - Visual sequencer                      │
│  - Mood state machine                    │
└────────────────────┬─────────────────────┘
                     │
┌────────────────────▼─────────────────────┐
│           AI DIRECTOR (per channel)       │
│  - Kimi K2 / Claude / local LLM          │
│  - Decides next track                    │
│  - Decides next visual                   │
│  - Responds to time/mood                 │
└────────────────────┬─────────────────────┘
                     │
┌────────────────────▼─────────────────────┐
│           CONTENT LIBRARY                 │
│  - /music (CC0, royalty-free MP3s)       │
│  - /visuals (loops, AI-generated)        │
│  - /prompts (for live generation)        │
└──────────────────────────────────────────┘
```

---

## CONTENT SOURCES (FREE & LEGAL)

### MUSIC
| Source | License | Type |
|--------|---------|------|
| Free Music Archive | CC | Lo-fi, Jazz, Ambient |
| Musopen | Public Domain | Classical |
| ccMixter | CC | Remixes, Electronic |
| Incompetech | Royalty-Free | Cinematic |
| YouTube Audio Library | Royalty-Free | Everything |

### VISUALS
| Source | License | Type |
|--------|---------|------|
| Pexels Video | CC0 | Nature, City, Abstract |
| Coverr | CC0 | Lifestyle, Mood |
| AI-Generated | Owned | Seedream, Midjourney |
| OpenGameArt | CC | Pixel art, Loops |

---

## MVP SCOPE

### Phase 1: Single Channel (Current)
- [x] One "apartment" channel
- [x] AI characters with memory
- [x] Music playback
- [x] Rain/mood visuals
- [x] Manual controls

### Phase 2: The Wall (Next)
- [ ] 6-10 channel grid
- [ ] Each channel = different vibe
- [ ] Click to tune in fullscreen
- [ ] Channels run independently
- [ ] ESC to return to wall

### Phase 3: AI Director
- [ ] LLM picks next track based on mood
- [ ] LLM sequences visuals
- [ ] Time-aware programming
- [ ] Cross-channel awareness

### Phase 4: Community
- [ ] Create your own channel
- [ ] Share channel configs
- [ ] Contribute music/visuals
- [ ] Channel discovery

---

## NON-GOALS

- No user accounts (anonymous viewing)
- No recommendations ("you might like...")
- No comments/chat (passive only)
- No ads (ever)
- No metrics shown to users

---

## SUCCESS =

You open mood42.tv at 2 AM.
You click a channel.
You forget you clicked.
An hour passes.
You feel better.

That's it. That's the product.

---

## INSPIRATION

- Lo-fi Girl (but AI-programmed)
- Adult Swim bumps (but infinite)
- Hotel lobby TV (but intentional)
- MTV before they stopped playing music
- The feeling of stumbling onto a perfect radio station at 3 AM

---

## NAME OPTIONS

- mood42.tv
- tuned.in
- static.fm
- channel0.tv
- ambientTV

---

*"The best TV is the TV you don't have to think about."*

---

## APPENDIX: SAMPLE CHANNELS

| CH | Name | Vibe | Music | Visual |
|----|------|------|-------|--------|
| 01 | Late Night Apartment | lo-fi study | lo-fi hip hop | rain, desk, city |
| 02 | Rain Café | cozy | jazz piano | coffee shop, rain |
| 03 | Jazz Noir | moody | 50s jazz | noir city, smoke |
| 04 | Synthwave Drive | retro | synthwave | neon, cars, grid |
| 05 | Deep Space | ambient | space ambient | stars, nebula |
| 06 | Tokyo Night | urban | city pop | tokyo streets |
| 07 | Sunday Morning | gentle | acoustic | sunlight, plants |
| 08 | Focus Mode | productive | minimal | abstract, clean |
| 09 | Melancholy | sad | sad piano | rain, empty rooms |
| 10 | Golden Hour | warm | indie | sunset, nature |

---

Built with love. Programmed by AI. Watched by humans.

**mood42 — agentic tv**
