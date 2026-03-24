// Window frame and glass for mood42

import { Graphics, Container } from 'pixi.js'
import { PALETTE } from '../sim/state.js'

export class WindowFrame {
  constructor(app) {
    this.app = app
    this.container = new Container()
    this.container.label = 'window-frame'

    this.frameGraphics = new Graphics()
    this.container.addChild(this.frameGraphics)
  }

  draw() {
    const W = this.app.screen.width
    const H = this.app.screen.height
    const windowBottom = H * 0.72

    this.frameGraphics.clear()

    // Window pane dividers - vertical center
    this.frameGraphics.moveTo(W / 2, 0)
    this.frameGraphics.lineTo(W / 2, windowBottom)
    this.frameGraphics.stroke({ color: PALETTE.paper, alpha: 0.06, width: 10 })

    // Horizontal divider
    this.frameGraphics.moveTo(0, H * 0.38)
    this.frameGraphics.lineTo(W, H * 0.38)
    this.frameGraphics.stroke({ color: PALETTE.paper, alpha: 0.06, width: 10 })

    // Outer frame
    this.frameGraphics.rect(0, 0, W, windowBottom)
    this.frameGraphics.stroke({ color: PALETTE.paper, alpha: 0.04, width: 18 })
  }

  resize() {
    this.draw()
  }
}
