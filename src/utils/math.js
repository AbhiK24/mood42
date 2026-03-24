// Math utilities for mood42

export const lerp = (a, b, t) => a + (b - a) * t

export const clamp = (val, min, max) => Math.min(Math.max(val, min), max)

export const random = (min, max) => Math.random() * (max - min) + min

export const randomInt = (min, max) => Math.floor(random(min, max + 1))

export const noise = (x, y = 0, z = 0) => {
  // Simple pseudo-noise function
  const n = Math.sin(x * 12.9898 + y * 78.233 + z * 37.719) * 43758.5453
  return n - Math.floor(n)
}

export const easeInOutSine = (t) => -(Math.cos(Math.PI * t) - 1) / 2

export const easeOutQuad = (t) => 1 - (1 - t) * (1 - t)

export const hexToRgb = (hex) => {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null
}

export const rgbToHex = (r, g, b) => {
  return '#' + [r, g, b].map(x => {
    const hex = Math.round(x).toString(16)
    return hex.length === 1 ? '0' + hex : hex
  }).join('')
}

export const lerpColor = (colorA, colorB, t) => {
  const a = hexToRgb(colorA)
  const b = hexToRgb(colorB)
  if (!a || !b) return colorA
  return rgbToHex(
    lerp(a.r, b.r, t),
    lerp(a.g, b.g, t),
    lerp(a.b, b.b, t)
  )
}
