// Sky, city skyline, and rain for mood42

import { Graphics, Container, BlurFilter } from 'pixi.js'
import { simState, PALETTE } from '../sim/state.js'
import { random, lerp } from '../utils/math.js'

export class Sky {
  constructor(app) {
    this.app = app
    this.container = new Container()
    this.container.label = 'sky'

    this.skyGraphics = new Graphics()
    this.cityGraphics = new Graphics()
    this.windowLightsGraphics = new Graphics()
    this.oneAmLight = new Graphics()

    this.container.addChild(this.skyGraphics)
    this.container.addChild(this.cityGraphics)
    this.container.addChild(this.windowLightsGraphics)
    this.container.addChild(this.oneAmLight)

    this.buildings = this.generateBuildings()
    this.windowFlickers = []
  }

  generateBuildings() {
    return [
      { x: 0, w: 60, h: 0.55, windows: [[0.3, 0.45], [0.5, 0.6], [0.7, 0.8]] },
      { x: 55, w: 80, h: 0.48, windows: [[0.2, 0.35], [0.55, 0.65]] },
      { x: 130, w: 45, h: 0.52, windows: [[0.4, 0.5]] },
      { x: 170, w: 100, h: 0.40, windows: [[0.25, 0.35], [0.5, 0.6], [0.7, 0.75]] },
      { x: 265, w: 60, h: 0.46, windows: [[0.3, 0.4]] },
      { x: 320, w: 110, h: 0.35, windows: [[0.2, 0.3], [0.45, 0.55], [0.65, 0.7]], empire: true },
      { x: 430, w: 70, h: 0.44, windows: [[0.35, 0.45], [0.6, 0.7]] },
      { x: 495, w: 85, h: 0.38, windows: [[0.25, 0.35], [0.5, 0.6]] },
      { x: 570, w: 55, h: 0.47, windows: [[0.4, 0.5]] },
      { x: 620, w: 100, h: 0.36, windows: [[0.3, 0.4], [0.6, 0.7]] },
      { x: 710, w: 70, h: 0.50, windows: [] },
    ]
  }

  draw() {
    const W = this.app.screen.width
    const H = this.app.screen.height
    const skylineY = H * 0.65

    // Sky gradient
    this.skyGraphics.clear()
    this.skyGraphics.rect(0, 0, W, skylineY)
    this.skyGraphics.fill({
      color: 0x040810,
      alpha: 1
    })

    // Add gradient layers
    for (let i = 0; i < 10; i++) {
      const y = (i / 10) * skylineY
      const alpha = lerp(0.0, 0.4, i / 10)
      this.skyGraphics.rect(0, y, W, skylineY / 10)
      this.skyGraphics.fill({ color: 0x0d1f3c, alpha })
    }

    // City silhouettes
    this.cityGraphics.clear()
    const scale = W / 800

    this.buildings.forEach(b => {
      const bH = H * b.h
      const bY = skylineY - bH
      const bX = b.x * scale
      const bW = b.w * scale

      // Building silhouette
      this.cityGraphics.rect(bX, bY, bW, bH + 10)
      this.cityGraphics.fill({ color: 0x030810 })

      // Empire State spire
      if (b.empire) {
        this.cityGraphics.rect(bX + bW * 0.35, bY - H * 0.08, bW * 0.3, H * 0.08)
        this.cityGraphics.fill({ color: 0x020608 })
        this.cityGraphics.rect(bX + bW * 0.42, bY - H * 0.12, bW * 0.16, H * 0.04)
        this.cityGraphics.fill({ color: 0x020608 })
        this.cityGraphics.rect(bX + bW * 0.46, bY - H * 0.15, bW * 0.08, H * 0.03)
        this.cityGraphics.fill({ color: 0x020608 })

        // Antenna blink
        this.cityGraphics.circle(bX + bW * 0.5, bY - H * 0.155, 2)
        this.cityGraphics.fill({ color: PALETTE.neonRed, alpha: 0.8 })
      }
    })

    // Water tower
    const wtX = W * 0.44
    const wtY = H * 0.22
    this.cityGraphics.rect(wtX, wtY, 20 * scale, 28 * scale)
    this.cityGraphics.fill({ color: 0x020608 })
    this.cityGraphics.moveTo(wtX - 8 * scale, wtY)
    this.cityGraphics.lineTo(wtX + 28 * scale, wtY)
    this.cityGraphics.lineTo(wtX + 10 * scale, wtY - 14 * scale)
    this.cityGraphics.closePath()
    this.cityGraphics.fill({ color: 0x020507 })

    // The special 1am light building
    const sbX = W * 0.62
    const sbW = 50 * scale
    const sbH = H * 0.38
    const sbY = skylineY - sbH
    this.cityGraphics.rect(sbX, sbY, sbW, sbH + 10)
    this.cityGraphics.fill({ color: 0x030810 })

    this.drawOneAmLight()
  }

  drawOneAmLight() {
    const W = this.app.screen.width
    const H = this.app.screen.height
    const scale = W / 800
    const skylineY = H * 0.65

    const sbX = W * 0.62
    const sbW = 50 * scale
    const sbH = H * 0.38
    const sbY = skylineY - sbH

    this.oneAmLight.clear()

    if (!simState.oneAmLightOff) {
      // THE light — warm, always on until 1am
      this.oneAmLight.rect(sbX + sbW * 0.4, sbY + sbH * 0.35, 6 * scale, 7 * scale)
      this.oneAmLight.fill({ color: 0xffdc8c, alpha: 0.65 })

      // Glow around the light
      this.oneAmLight.circle(sbX + sbW * 0.4 + 3 * scale, sbY + sbH * 0.35 + 3.5 * scale, 12 * scale)
      this.oneAmLight.fill({ color: 0xffdc8c, alpha: 0.1 })
    }
  }

  drawWindowLights(time) {
    const W = this.app.screen.width
    const H = this.app.screen.height
    const scale = W / 800
    const skylineY = H * 0.65

    this.windowLightsGraphics.clear()

    this.buildings.forEach((b, bi) => {
      const bH = H * b.h
      const bY = skylineY - bH
      const bX = b.x * scale
      const bW = b.w * scale

      b.windows.forEach(([wx, wy], wi) => {
        // Flicker effect
        const flicker = 0.3 + 0.1 * Math.sin(time * 0.001 + bi * 0.5 + wi * 0.3)
        const wX = bX + bW * wx
        const wY = bY + bH * wy

        this.windowLightsGraphics.rect(wX, wY, 5 * scale, 6 * scale)
        this.windowLightsGraphics.fill({ color: 0xffdc8c, alpha: flicker })
      })
    })
  }

  update(time) {
    this.drawWindowLights(time)
    this.drawOneAmLight()
  }

  resize() {
    this.draw()
  }
}

export class Rain {
  constructor(app) {
    this.app = app
    this.container = new Container()
    this.container.label = 'rain'

    this.rainGraphics = new Graphics()
    this.container.addChild(this.rainGraphics)

    this.drops = []
    this.initDrops()
  }

  initDrops() {
    const count = 400
    this.drops = []

    for (let i = 0; i < count; i++) {
      this.drops.push({
        x: random(0, this.app.screen.width),
        y: random(-50, this.app.screen.height * 0.72),
        speed: random(4, 12),
        len: random(12, 25),
        opacity: random(0.05, 0.25),
      })
    }
  }

  update() {
    if (!simState.raining) {
      this.rainGraphics.clear()
      return
    }

    const W = this.app.screen.width
    const H = this.app.screen.height
    const maxY = H * 0.72
    const intensity = simState.rainIntensity

    this.rainGraphics.clear()

    this.drops.forEach(d => {
      d.y += d.speed
      d.x -= d.speed * 0.15 // Wind angle

      if (d.y > maxY) {
        d.y = random(-50, -10)
        d.x = random(0, W)
      }

      // Draw raindrop as line
      const alpha = d.opacity * intensity
      this.rainGraphics.moveTo(d.x, d.y)
      this.rainGraphics.lineTo(d.x - d.len * 0.15, d.y + d.len)
      this.rainGraphics.stroke({ color: 0xa0b9dc, alpha, width: 0.8 })
    })
  }

  resize() {
    this.initDrops()
  }
}

export class Condensation {
  constructor(app) {
    this.app = app
    this.container = new Container()
    this.container.label = 'condensation'

    this.graphics = new Graphics()
    this.container.addChild(this.graphics)

    this.drops = []
    this.initDrops()
  }

  initDrops() {
    const W = this.app.screen.width
    const H = this.app.screen.height
    this.drops = []

    for (let i = 0; i < 40; i++) {
      this.drops.push({
        x: random(W * 0.1, W * 0.9),
        y: random(H * 0.05, H * 0.7),
        r: random(1, 4),
        opacity: random(0.1, 0.3),
      })
    }
  }

  draw() {
    if (!simState.raining) {
      this.graphics.clear()
      return
    }

    this.graphics.clear()

    this.drops.forEach(d => {
      this.graphics.circle(d.x, d.y, d.r)
      this.graphics.fill({ color: 0xb4c8e6, alpha: d.opacity })
    })
  }

  resize() {
    this.initDrops()
    this.draw()
  }
}
