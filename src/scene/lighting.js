// Lighting system for mood42

import { Graphics, Container, BlurFilter } from 'pixi.js'
import { simState, PALETTE } from '../sim/state.js'
import { lerp } from '../utils/math.js'

export class NeonLighting {
  constructor(app) {
    this.app = app
    this.container = new Container()
    this.container.label = 'neon-lighting'

    this.redGlow = new Graphics()
    this.blueGlow = new Graphics()
    this.neonSign = new Graphics()

    // Add blur to glows
    this.redGlow.filters = [new BlurFilter({ strength: 30 })]
    this.blueGlow.filters = [new BlurFilter({ strength: 25 })]

    this.container.addChild(this.redGlow)
    this.container.addChild(this.blueGlow)
    this.container.addChild(this.neonSign)

    this.phase = 0
  }

  update(time) {
    const W = this.app.screen.width
    const H = this.app.screen.height

    this.phase += 0.008
    const flicker1 = 0.8 + 0.2 * Math.sin(this.phase * 7.3)
    const flicker2 = 0.7 + 0.3 * Math.sin(this.phase * 11.1 + 1.5)

    // Occasional stutter
    const stutter = Math.random() > 0.995 ? 0.3 : 1

    // Red neon glow (upper right)
    this.redGlow.clear()
    this.redGlow.circle(W * 0.72, H * 0.55, W * 0.15)
    this.redGlow.fill({ color: PALETTE.neonRed, alpha: 0.12 * flicker1 * stutter })

    // Blue neon glow (upper left)
    this.blueGlow.clear()
    this.blueGlow.circle(W * 0.2, H * 0.4, W * 0.12)
    this.blueGlow.fill({ color: PALETTE.neonBlue, alpha: 0.1 * flicker2 })

    // Neon "OPEN" sign
    this.drawNeonSign(flicker1 * stutter)
  }

  drawNeonSign(flicker) {
    const W = this.app.screen.width
    const H = this.app.screen.height

    this.neonSign.clear()

    // Simple representation of OPEN sign
    const x = W * 0.74
    const y = H * 0.54
    const size = W * 0.03

    // O
    this.neonSign.circle(x, y, size * 0.4)
    this.neonSign.stroke({ color: PALETTE.neonRed, alpha: 0.8 * flicker, width: 2 })

    // P
    this.neonSign.moveTo(x + size * 0.8, y + size * 0.4)
    this.neonSign.lineTo(x + size * 0.8, y - size * 0.4)
    this.neonSign.arc(x + size * 0.8, y - size * 0.2, size * 0.2, -Math.PI / 2, Math.PI / 2)
    this.neonSign.stroke({ color: PALETTE.neonRed, alpha: 0.8 * flicker, width: 2 })

    // E
    this.neonSign.moveTo(x + size * 1.6, y - size * 0.4)
    this.neonSign.lineTo(x + size * 1.3, y - size * 0.4)
    this.neonSign.lineTo(x + size * 1.3, y + size * 0.4)
    this.neonSign.lineTo(x + size * 1.6, y + size * 0.4)
    this.neonSign.moveTo(x + size * 1.3, y)
    this.neonSign.lineTo(x + size * 1.5, y)
    this.neonSign.stroke({ color: PALETTE.neonRed, alpha: 0.8 * flicker, width: 2 })

    // N
    this.neonSign.moveTo(x + size * 1.8, y + size * 0.4)
    this.neonSign.lineTo(x + size * 1.8, y - size * 0.4)
    this.neonSign.lineTo(x + size * 2.2, y + size * 0.4)
    this.neonSign.lineTo(x + size * 2.2, y - size * 0.4)
    this.neonSign.stroke({ color: PALETTE.neonRed, alpha: 0.8 * flicker, width: 2 })
  }

  resize() {
    // Will redraw on next update
  }
}

export class LampLight {
  constructor(app) {
    this.app = app
    this.container = new Container()
    this.container.label = 'lamp-light'

    this.lampPost = new Graphics()
    this.lampShade = new Graphics()
    this.lampGlow = new Graphics()

    this.lampGlow.filters = [new BlurFilter({ strength: 40 })]

    this.container.addChild(this.lampGlow)
    this.container.addChild(this.lampPost)
    this.container.addChild(this.lampShade)
  }

  draw() {
    const W = this.app.screen.width
    const H = this.app.screen.height
    const lx = W * 0.78
    const ly = H * 0.45
    const intensity = simState.lampIntensity

    // Lamp glow
    this.lampGlow.clear()
    this.lampGlow.circle(lx, ly + 20, W * 0.25)
    this.lampGlow.fill({ color: PALETTE.tungsten, alpha: 0.15 * intensity })

    // Lamp post
    this.lampPost.clear()
    this.lampPost.moveTo(lx, H)
    this.lampPost.lineTo(lx, ly + 30)
    this.lampPost.stroke({ color: PALETTE.tungsten, alpha: 0.3 * intensity, width: 3 })

    // Lamp shade
    this.lampShade.clear()
    this.lampShade.ellipse(lx, ly + 28, 20 * (W / 1200), 8 * (W / 1200))
    this.lampShade.fill({ color: PALETTE.tungsten, alpha: 0.25 * intensity })
  }

  update() {
    this.draw()
  }

  resize() {
    this.draw()
  }
}

export class CandleLight {
  constructor(app) {
    this.app = app
    this.container = new Container()
    this.container.label = 'candle-light'
    this.container.visible = false

    this.candleBody = new Graphics()
    this.flame = new Graphics()
    this.glow = new Graphics()

    this.glow.filters = [new BlurFilter({ strength: 20 })]

    this.container.addChild(this.glow)
    this.container.addChild(this.candleBody)
    this.container.addChild(this.flame)

    this.phase = 0
  }

  update(time) {
    this.container.visible = simState.objects.candle

    if (!simState.objects.candle) return

    const W = this.app.screen.width
    const H = this.app.screen.height
    const dY = H * 0.72
    const cx = W * 0.32
    const cy = dY - 30 * (H / 900)

    this.phase += 0.1
    const flicker = 0.7 + 0.3 * Math.sin(this.phase)

    // Candle body
    this.candleBody.clear()
    this.candleBody.rect(cx, cy, 10 * (W / 1400), 28 * (H / 900))
    this.candleBody.fill({ color: PALETTE.paper, alpha: 0.15 })

    // Flame
    this.flame.clear()
    this.flame.ellipse(cx + 5 * (W / 1400), cy - 8 * (H / 900), 4 * (W / 1400), 8 * (H / 900))
    this.flame.fill({ color: 0xffb43c, alpha: 0.8 * flicker })

    // Glow
    this.glow.clear()
    this.glow.circle(cx + 5 * (W / 1400), cy, 60)
    this.glow.fill({ color: 0xffa030, alpha: 0.15 * flicker })
  }

  resize() {
    // Will redraw on next update
  }
}

export class ScreenGlow {
  constructor(app) {
    this.app = app
    this.container = new Container()
    this.container.label = 'screen-glow'

    this.glow = new Graphics()
    this.glow.filters = [new BlurFilter({ strength: 30 })]
    this.container.addChild(this.glow)
  }

  update() {
    const W = this.app.screen.width
    const H = this.app.screen.height
    const dY = H * 0.72

    this.glow.clear()

    if (simState.objects.laptopOpen) {
      const cx = W * 0.5
      const cy = dY - H * 0.12
      const color = simState.characterMood === 'WITHDRAWN' ? 0x4d5078 : 0x4d789f

      this.glow.circle(cx, cy, W * 0.12)
      this.glow.fill({ color, alpha: 0.15 })
    }
  }

  resize() {
    // Will redraw on next update
  }
}
