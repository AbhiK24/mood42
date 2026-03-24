// Character for mood42

import { Graphics, Container, BlurFilter } from 'pixi.js'
import { simState, PALETTE } from '../sim/state.js'
import gsap from 'gsap'

export class Character {
  constructor(app) {
    this.app = app
    this.container = new Container()
    this.container.label = 'character'

    // Create graphics layers
    this.chairGraphics = new Graphics()
    this.bodyGraphics = new Graphics()
    this.headGraphics = new Graphics()
    this.hairGraphics = new Graphics()
    this.faceGlow = new Graphics()
    this.floorPose = new Graphics()

    this.faceGlow.filters = [new BlurFilter({ strength: 15 })]

    this.container.addChild(this.chairGraphics)
    this.container.addChild(this.faceGlow)
    this.container.addChild(this.bodyGraphics)
    this.container.addChild(this.headGraphics)
    this.container.addChild(this.hairGraphics)
    this.container.addChild(this.floorPose)

    // Animation state
    this.breathePhase = 0
    this.headTilt = 0
    this.shoulderDrop = 0

    // Target values for GSAP
    this.targetHeadTilt = 0
    this.targetShoulderDrop = 0
  }

  updateMoodAnimation() {
    const mood = simState.characterMood

    switch (mood) {
      case 'FOCUSED':
        gsap.to(this, { targetHeadTilt: 0, targetShoulderDrop: 0, duration: 2.5, ease: 'power2.inOut' })
        break
      case 'THINKING':
        gsap.to(this, { targetHeadTilt: 0.08, targetShoulderDrop: 0, duration: 2, ease: 'power2.inOut' })
        break
      case 'WITHDRAWN':
        gsap.to(this, { targetHeadTilt: 0.12, targetShoulderDrop: 0.08, duration: 2.5, ease: 'power2.inOut' })
        break
      case 'GOOD':
        gsap.to(this, { targetHeadTilt: -0.05, targetShoulderDrop: -0.02, duration: 2, ease: 'power2.inOut' })
        break
      case 'ANXIOUS':
        gsap.to(this, { targetHeadTilt: 0.05, targetShoulderDrop: 0.03, duration: 1.5, ease: 'power2.inOut' })
        break
      case 'FLOOR':
        // Handled separately
        break
    }
  }

  drawFloorPose(W, H, dY) {
    this.floorPose.clear()

    if (!simState.objects.characterOnFloor) {
      this.floorPose.visible = false
      return
    }

    this.floorPose.visible = true

    const skinTone = PALETTE.skinWarm
    const clothTone = PALETTE.cloth

    // Body slumped against desk
    this.floorPose.ellipse(W * 0.44, dY + H * 0.09, W * 0.07, H * 0.05)
    this.floorPose.fill({ color: clothTone, alpha: 0.55 })

    // Legs
    this.floorPose.moveTo(W * 0.44, dY + H * 0.1)
    this.floorPose.lineTo(W * 0.56, dY + H * 0.12)
    this.floorPose.stroke({ color: clothTone, alpha: 0.4, width: W * 0.022, cap: 'round' })

    // Head resting on knees
    this.floorPose.ellipse(W * 0.41, dY + H * 0.04, W * 0.022, H * 0.032)
    this.floorPose.fill({ color: skinTone, alpha: 0.7 })

    // Hair
    this.floorPose.ellipse(W * 0.41, dY + H * 0.02, W * 0.025, H * 0.028)
    this.floorPose.fill({ color: PALETTE.hairDark, alpha: 0.8 })
  }

  drawSittingPose(W, H, dY, breathe) {
    const cx = W * 0.5
    const skinTone = PALETTE.skinWarm
    const clothTone = PALETTE.cloth

    // Lerp current values toward targets
    this.headTilt += (this.targetHeadTilt - this.headTilt) * 0.05
    this.shoulderDrop += (this.targetShoulderDrop - this.shoulderDrop) * 0.05

    // Chair back
    this.chairGraphics.clear()
    this.chairGraphics.moveTo(cx - W * 0.06, dY - H * 0.02)
    this.chairGraphics.lineTo(cx - W * 0.06, dY - H * 0.28)
    this.chairGraphics.stroke({ color: 0xb4a078, alpha: 0.12, width: W * 0.008, cap: 'round' })

    this.chairGraphics.moveTo(cx + W * 0.06, dY - H * 0.02)
    this.chairGraphics.lineTo(cx + W * 0.06, dY - H * 0.28)
    this.chairGraphics.stroke({ color: 0xb4a078, alpha: 0.12, width: W * 0.008, cap: 'round' })

    this.chairGraphics.moveTo(cx - W * 0.06, dY - H * 0.26)
    this.chairGraphics.lineTo(cx + W * 0.06, dY - H * 0.26)
    this.chairGraphics.stroke({ color: 0xb4a078, alpha: 0.12, width: W * 0.008, cap: 'round' })

    // Body - torso
    this.bodyGraphics.clear()
    const torsoY = dY - H * 0.1 + breathe * 0.4 + this.shoulderDrop * H * 0.5
    this.bodyGraphics.ellipse(cx, torsoY, W * 0.055, H * 0.1)
    this.bodyGraphics.fill({ color: clothTone, alpha: 0.7 })

    // Arms
    const armY = dY - H * 0.1 + this.shoulderDrop * H * 0.3

    // Left arm
    this.bodyGraphics.moveTo(cx - W * 0.04, armY)
    this.bodyGraphics.quadraticCurveTo(cx - W * 0.07, dY - H * 0.06, cx - W * 0.08, dY - H * 0.02)
    this.bodyGraphics.stroke({ color: clothTone, alpha: 0.65, width: W * 0.025, cap: 'round' })

    // Right arm
    this.bodyGraphics.moveTo(cx + W * 0.04, armY)
    this.bodyGraphics.quadraticCurveTo(cx + W * 0.07, dY - H * 0.06, cx + W * 0.08, dY - H * 0.02)
    this.bodyGraphics.stroke({ color: clothTone, alpha: 0.65, width: W * 0.025, cap: 'round' })

    // Hands
    this.bodyGraphics.ellipse(cx - W * 0.075, dY - H * 0.015, W * 0.018, H * 0.012)
    this.bodyGraphics.fill({ color: skinTone, alpha: 0.75 })
    this.bodyGraphics.ellipse(cx + W * 0.075, dY - H * 0.015, W * 0.018, H * 0.012)
    this.bodyGraphics.fill({ color: skinTone, alpha: 0.75 })

    // Neck
    const neckY = dY - H * 0.2 + breathe * 0.3
    this.bodyGraphics.ellipse(cx, neckY, W * 0.014, H * 0.022)
    this.bodyGraphics.fill({ color: skinTone, alpha: 0.75 })

    // Head
    this.headGraphics.clear()
    const headY = dY - H * 0.245 + breathe * 0.3

    // Apply head tilt rotation via position offset
    const headOffsetX = this.headTilt * W * 0.05

    this.headGraphics.ellipse(cx + headOffsetX, headY, W * 0.028, H * 0.042)
    this.headGraphics.fill({ color: skinTone, alpha: 0.75 })

    // Ear
    this.headGraphics.ellipse(cx + headOffsetX + W * 0.028, headY + H * 0.005, W * 0.006, H * 0.01)
    this.headGraphics.fill({ color: skinTone, alpha: 0.6 })

    // Hair
    this.hairGraphics.clear()
    const hairY = dY - H * 0.268 + breathe * 0.3

    // Main hair mass
    this.hairGraphics.ellipse(cx + headOffsetX, hairY, W * 0.032, H * 0.03)
    this.hairGraphics.fill({ color: PALETTE.hairDark, alpha: 0.92 })

    // Loose strand falling
    const strandSway = Math.sin(this.breathePhase * 0.3) * 1
    this.hairGraphics.moveTo(cx + headOffsetX + W * 0.02, hairY + H * 0.013)
    this.hairGraphics.quadraticCurveTo(
      cx + headOffsetX + W * 0.04 + strandSway,
      dY - H * 0.24,
      cx + headOffsetX + W * 0.03,
      dY - H * 0.22
    )
    this.hairGraphics.quadraticCurveTo(
      cx + headOffsetX + W * 0.035,
      dY - H * 0.21,
      cx + headOffsetX + W * 0.025,
      dY - H * 0.2
    )
    this.hairGraphics.stroke({ color: PALETTE.hairDark, alpha: 0.5, width: W * 0.008 })

    // Face glow from laptop
    this.faceGlow.clear()
    if (simState.objects.laptopOpen) {
      const glowColor = simState.characterMood === 'WITHDRAWN' ? 0x4d5078 : 0x4d82b4
      this.faceGlow.circle(cx, headY, W * 0.08)
      this.faceGlow.fill({ color: glowColor, alpha: 0.25 })
    }
  }

  update(time) {
    const W = this.app.screen.width
    const H = this.app.screen.height
    const dY = H * 0.72

    // Breathing animation
    this.breathePhase = time * 0.0015
    const breathe = Math.sin(this.breathePhase) * 1.5

    // Clear all graphics
    this.chairGraphics.visible = !simState.objects.characterOnFloor
    this.bodyGraphics.visible = !simState.objects.characterOnFloor
    this.headGraphics.visible = !simState.objects.characterOnFloor
    this.hairGraphics.visible = !simState.objects.characterOnFloor
    this.faceGlow.visible = !simState.objects.characterOnFloor && simState.objects.laptopOpen

    if (simState.objects.characterOnFloor) {
      this.drawFloorPose(W, H, dY)
    } else {
      this.drawSittingPose(W, H, dY, breathe)
    }
  }

  resize() {
    // Will redraw on next update
  }
}
