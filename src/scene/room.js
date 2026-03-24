// Room, desk, and objects for mood42

import { Graphics, Container, BlurFilter } from 'pixi.js'
import { simState, PALETTE } from '../sim/state.js'
import { random } from '../utils/math.js'

export class Room {
  constructor(app) {
    this.app = app
    this.container = new Container()
    this.container.label = 'room'

    this.roomGraphics = new Graphics()
    this.container.addChild(this.roomGraphics)
  }

  draw() {
    const W = this.app.screen.width
    const H = this.app.screen.height

    this.roomGraphics.clear()

    // Room floor/walls - warm darkness from bottom
    for (let i = 0; i < 10; i++) {
      const y = H * 0.6 + (i / 10) * H * 0.4
      const alpha = 0.1 + (i / 10) * 0.8
      this.roomGraphics.rect(0, y, W, H * 0.04)
      this.roomGraphics.fill({ color: 0x080602, alpha })
    }

    // Left wall darkness
    for (let i = 0; i < 5; i++) {
      const x = (i / 5) * W * 0.12
      const alpha = 0.9 - (i / 5) * 0.9
      this.roomGraphics.rect(x, 0, W * 0.024, H)
      this.roomGraphics.fill({ color: 0x050402, alpha })
    }

    // Right wall darkness
    for (let i = 0; i < 5; i++) {
      const x = W - W * 0.12 + (i / 5) * W * 0.12
      const alpha = (i / 5) * 0.9
      this.roomGraphics.rect(x, 0, W * 0.024, H)
      this.roomGraphics.fill({ color: 0x050402, alpha })
    }
  }

  resize() {
    this.draw()
  }
}

export class Desk {
  constructor(app) {
    this.app = app
    this.container = new Container()
    this.container.label = 'desk'

    this.deskSurface = new Graphics()
    this.deskGlow = new Graphics()

    this.deskGlow.filters = [new BlurFilter({ strength: 20 })]

    this.container.addChild(this.deskGlow)
    this.container.addChild(this.deskSurface)
  }

  draw() {
    const W = this.app.screen.width
    const H = this.app.screen.height
    const dY = H * 0.72

    // Lamp glow on desk
    this.deskGlow.clear()
    this.deskGlow.circle(W * 0.78, dY, W * 0.2)
    this.deskGlow.fill({ color: PALETTE.tungsten, alpha: 0.1 * simState.lampIntensity })

    // Desk surface
    this.deskSurface.clear()
    this.deskSurface.rect(W * 0.05, dY, W * 0.9, 6)
    this.deskSurface.fill({ color: PALETTE.tungsten, alpha: 0.18 })

    // Edge highlight
    this.deskSurface.rect(W * 0.05, dY, W * 0.9, 2)
    this.deskSurface.fill({ color: PALETTE.tungsten, alpha: 0.25 })
  }

  resize() {
    this.draw()
  }
}

export class DeskObjects {
  constructor(app) {
    this.app = app
    this.container = new Container()
    this.container.label = 'desk-objects'

    this.laptop = new Graphics()
    this.coffee = new Graphics()
    this.secondCoffee = new Graphics()
    this.books = new Graphics()
    this.phone = new Graphics()
    this.corkBoard = new Graphics()

    this.container.addChild(this.corkBoard)
    this.container.addChild(this.books)
    this.container.addChild(this.laptop)
    this.container.addChild(this.coffee)
    this.container.addChild(this.secondCoffee)
    this.container.addChild(this.phone)

    this.steamParticles = []
  }

  draw() {
    const W = this.app.screen.width
    const H = this.app.screen.height
    const dY = H * 0.72

    this.drawLaptop(W, H, dY)
    this.drawCoffee(W, H, dY)
    this.drawBooks(W, H, dY)
    this.drawPhone(W, H, dY)
    this.drawCorkBoard(W, H)
  }

  drawLaptop(W, H, dY) {
    this.laptop.clear()

    if (simState.objects.laptopOpen) {
      // Screen
      this.laptop.roundRect(W * 0.38, dY - H * 0.22, W * 0.24, H * 0.2, 4)
      this.laptop.fill({ color: 0x080c14, alpha: 0.95 })

      // Screen content lines
      for (let i = 0; i < 4; i++) {
        const lw = (0.5 + random(0, 0.4)) * W * 0.18
        this.laptop.rect(W * 0.41, dY - H * 0.19 + i * H * 0.04, lw, 2)
        this.laptop.fill({ color: PALETTE.paper, alpha: 0.12 })
      }

      // Hinge
      this.laptop.rect(W * 0.38, dY - 6, W * 0.24, 6)
      this.laptop.fill({ color: PALETTE.paper, alpha: 0.06 })
    } else {
      // Closed laptop
      this.laptop.roundRect(W * 0.38, dY - 8, W * 0.22, 8, 2)
      this.laptop.fill({ color: 0x1e1914, alpha: 0.9 })
    }
  }

  drawCoffee(W, H, dY) {
    const scale = W / 1400
    const cx = W * 0.22
    const cy = dY - 32

    this.coffee.clear()

    // Cup body
    this.coffee.roundRect(cx, cy, 28 * scale, 22 * scale, 3)
    this.coffee.fill({ color: PALETTE.paper, alpha: 0.1 })

    // Rim
    this.coffee.ellipse(cx + 14 * scale, cy, 14 * scale, 5 * scale)
    this.coffee.fill({ color: PALETTE.paper, alpha: 0.06 })

    // Second cup
    this.secondCoffee.clear()
    if (simState.objects.secondCup) {
      const cx2 = W * 0.28
      const cy2 = dY - 28

      this.secondCoffee.roundRect(cx2, cy2, 28 * scale, 22 * scale, 3)
      this.secondCoffee.fill({ color: PALETTE.paper, alpha: 0.1 })
      this.secondCoffee.ellipse(cx2 + 14 * scale, cy2, 14 * scale, 5 * scale)
      this.secondCoffee.fill({ color: PALETTE.paper, alpha: 0.06 })
    }
  }

  drawBooks(W, H, dY) {
    this.books.clear()
    const bx = W * 0.08
    const books = [
      { h: 12, w: 72, c: PALETTE.paper, a: 0.1, r: -2 },
      { h: 11, w: 66, c: 0xa87ce8, a: 0.18, r: 1 },
      { h: 12, w: 75, c: PALETTE.tungsten, a: 0.14, r: -1 },
    ]

    let by = dY - 10
    books.forEach(b => {
      const scaleW = W / 1400
      const scaleH = H / 900

      this.books.rect(bx, by - b.h * scaleH, b.w * scaleW, b.h * scaleH)
      this.books.fill({ color: b.c, alpha: b.a })

      by -= b.h * scaleH - 2
    })
  }

  drawPhone(W, H, dY) {
    this.phone.clear()

    // Phone face down
    this.phone.roundRect(W * 0.65, dY - 18, W * 0.06, W * 0.035, 3)
    this.phone.fill({ color: PALETTE.paper, alpha: 0.07 })

    // Phone glow when notification
    if (simState.objects.phoneGlowing) {
      this.phone.roundRect(W * 0.65 - 2, dY - 20, W * 0.06 + 4, W * 0.035 + 4, 5)
      this.phone.fill({ color: PALETTE.paper, alpha: 0.15 })
    }
  }

  drawCorkBoard(W, H) {
    this.corkBoard.clear()

    // Board
    this.corkBoard.roundRect(W * 0.06, H * 0.15, W * 0.14, H * 0.25, 2)
    this.corkBoard.fill({ color: 0x644128, alpha: 0.12 })
    this.corkBoard.roundRect(W * 0.06, H * 0.15, W * 0.14, H * 0.25, 2)
    this.corkBoard.stroke({ color: PALETTE.paper, alpha: 0.04, width: 1 })

    // Notes
    const notes = [
      { x: 0.07, y: 0.17, w: 0.05, h: 0.06, c: PALETTE.tungsten, a: 0.12 },
      { x: 0.13, y: 0.16, w: 0.06, h: 0.05, c: PALETTE.paper, a: 0.05 },
      { x: 0.07, y: 0.26, w: 0.07, h: 0.04, c: PALETTE.neonBlue, a: 0.1 },
      { x: 0.13, y: 0.23, w: 0.06, h: 0.07, c: PALETTE.neonRed, a: 0.08 },
    ]

    notes.forEach(n => {
      this.corkBoard.rect(W * n.x, H * n.y, W * n.w, H * n.h)
      this.corkBoard.fill({ color: n.c, alpha: n.a })
    })
  }

  update() {
    this.drawPhone(this.app.screen.width, this.app.screen.height, this.app.screen.height * 0.72)
    this.drawLaptop(this.app.screen.width, this.app.screen.height, this.app.screen.height * 0.72)

    // Update second coffee visibility
    if (simState.objects.secondCup) {
      this.drawCoffee(this.app.screen.width, this.app.screen.height, this.app.screen.height * 0.72)
    }
  }

  resize() {
    this.draw()
  }
}

export class Plant {
  constructor(app) {
    this.app = app
    this.container = new Container()
    this.container.label = 'plant'

    this.potGraphics = new Graphics()
    this.stemsGraphics = new Graphics()

    this.container.addChild(this.potGraphics)
    this.container.addChild(this.stemsGraphics)

    this.stems = [
      { dx: -18, dy: -40, ddx: -28, ddy: -65 },
      { dx: 18, dy: -38, ddx: 30, ddy: -62 },
      { dx: 0, dy: -35, ddx: -5, ddy: -70 },
      { dx: -10, dy: -30, ddx: -30, ddy: -45 },
      { dx: 10, dy: -32, ddx: 35, ddy: -48 },
    ]
  }

  draw() {
    const W = this.app.screen.width
    const H = this.app.screen.height
    const px = W * 0.86
    const py = H * 0.6
    const scale = W / 1400

    // Pot
    this.potGraphics.clear()
    this.potGraphics.roundRect(px - 14 * scale, py, 28 * scale, 24 * (H / 900), 2)
    this.potGraphics.fill({ color: 0x785032, alpha: 0.25 })
  }

  update(time) {
    const W = this.app.screen.width
    const H = this.app.screen.height
    const px = W * 0.86
    const py = H * 0.6
    const t = time * 0.001

    this.stemsGraphics.clear()

    this.stems.forEach((s, i) => {
      const sway = Math.sin(t * 0.3 + i * 0.8) * 2

      this.stemsGraphics.moveTo(px, py)
      this.stemsGraphics.quadraticCurveTo(
        px + s.dx + sway,
        py + s.dy,
        px + s.ddx + sway,
        py + s.ddy
      )
      this.stemsGraphics.stroke({ color: 0x507832, alpha: 0.3 + i * 0.05, width: 2 })
    })
  }

  resize() {
    this.draw()
  }
}

export class Steam {
  constructor(app) {
    this.app = app
    this.container = new Container()
    this.container.label = 'steam'

    this.graphics = new Graphics()
    this.container.addChild(this.graphics)

    this.particles = []
  }

  addParticle(x, y) {
    if (this.particles.length < 30) {
      this.particles.push({
        x,
        y,
        vx: (Math.random() - 0.5) * 0.4,
        vy: -(0.3 + Math.random() * 0.5),
        life: 1.0,
        size: 2 + Math.random() * 3,
      })
    }
  }

  update() {
    const W = this.app.screen.width
    const dY = this.app.screen.height * 0.72
    const scale = W / 1400

    // Add steam from coffee
    if (Math.random() > 0.9) {
      this.addParticle(W * 0.22 + 12 * scale, dY - 37)
    }

    this.graphics.clear()

    this.particles = this.particles.filter(p => p.life > 0)

    this.particles.forEach(p => {
      p.x += p.vx
      p.y += p.vy
      p.life -= 0.015
      p.vx += (Math.random() - 0.5) * 0.1

      const r = Math.max(0.01, p.size * p.life)
      this.graphics.circle(p.x, p.y, r)
      this.graphics.fill({ color: PALETTE.paper, alpha: p.life * 0.12 })
    })
  }

  resize() {
    this.particles = []
  }
}
