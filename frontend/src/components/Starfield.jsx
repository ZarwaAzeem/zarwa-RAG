import { Sparkle } from '../icons.jsx'

/* Where each star sits (% of the screen), its size in px, how bright it gets,
   and its own rhythm so the field never pulses in unison. */
const STARS = [
  { x: 68, y: 16, size: 96, glow: 0.6, duration: 7, delay: 0 },
  { x: 40, y: 27, size: 58, glow: 0.5, duration: 6, delay: 1.4 },
  { x: 47, y: 9, size: 36, glow: 0.55, duration: 5, delay: 0.6 },
  { x: 12, y: 14, size: 20, glow: 0.45, duration: 4.5, delay: 2.1 },
  { x: 88, y: 40, size: 26, glow: 0.4, duration: 5.5, delay: 0.9 },
  { x: 8, y: 48, size: 34, glow: 0.3, duration: 6.5, delay: 3 },
  { x: 80, y: 64, size: 18, glow: 0.4, duration: 4, delay: 1.8 },
  { x: 22, y: 76, size: 24, glow: 0.3, duration: 5, delay: 0.3 },
  { x: 62, y: 86, size: 40, glow: 0.28, duration: 7.5, delay: 2.6 },
  { x: 92, y: 90, size: 16, glow: 0.4, duration: 4.2, delay: 1.1 },
]

/* Twinkling stars behind every screen. */
export default function Starfield() {
  return (
    <div className="starfield" aria-hidden="true">
      {STARS.map((star, index) => (
        <span
          key={index}
          className="star"
          style={{
            left: `${star.x}%`,
            top: `${star.y}%`,
            width: star.size,
            '--glow': star.glow,
            '--duration': `${star.duration}s`,
            '--delay': `${-star.delay}s`,
          }}
        >
          <Sparkle />
        </span>
      ))}
    </div>
  )
}
