import { useRef, type PointerEvent } from 'react'
import { useMotionValue, useReducedMotion, useSpring, useTransform } from 'motion/react'

/** Inclinação 3D sutil que segue o ponteiro; desativada com movimento reduzido ou toque. */
export function usePointerTilt(maxDeg = 6) {
  const reduce = useReducedMotion()
  const ref = useRef<HTMLDivElement>(null)
  const px = useMotionValue(0)
  const py = useMotionValue(0)
  const spring = { stiffness: 120, damping: 20, mass: 0.6 }
  const rotateY = useSpring(useTransform(px, [-0.5, 0.5], [-maxDeg, maxDeg]), spring)
  const rotateX = useSpring(useTransform(py, [-0.5, 0.5], [maxDeg * 0.8, -maxDeg * 0.8]), spring)

  const onPointerMove = (e: PointerEvent<HTMLElement>) => {
    if (reduce || e.pointerType !== 'mouse' || !ref.current) return
    const r = ref.current.getBoundingClientRect()
    px.set((e.clientX - r.left) / r.width - 0.5)
    py.set((e.clientY - r.top) / r.height - 0.5)
  }
  const onPointerLeave = () => {
    px.set(0)
    py.set(0)
  }

  return { ref, px, py, rotateX, rotateY, handlers: { onPointerMove, onPointerLeave } }
}
