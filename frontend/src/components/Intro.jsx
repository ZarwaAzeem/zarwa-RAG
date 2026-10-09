import { useEffect, useRef, useState } from 'react'
import introVideo from '../assets/intro.mp4'

/* Plays once, with sound, when the page loads, then hands over to the welcome screen. */
export default function Intro({ onDone }) {
  const videoRef = useRef(null)
  const backdropRef = useRef(null)
  const [needsTap, setNeedsTap] = useState(false)

  function play() {
    // Browsers only let a video start with sound after the visitor has
    // interacted with the page; until then, ask for a tap.
    videoRef.current
      .play()
      .then(() => setNeedsTap(false))
      .catch(() => setNeedsTap(true))
  }

  useEffect(play, [])

  return (
    <section className="screen intro">
      {/* The video is landscape and the screen is portrait: a blurred copy fills
          the screen behind it so the whole frame shows without black bars. */}
      <video className="intro-backdrop" ref={backdropRef} src={introVideo} muted playsInline aria-hidden="true" />
      <video
        className="intro-video"
        ref={videoRef}
        src={introVideo}
        playsInline
        onPlay={() => backdropRef.current?.play().catch(() => {})}
        onEnded={onDone}
        onError={onDone}
      />
      {needsTap && (
        <button className="intro-play" onClick={play} aria-label="Play intro with sound">
          <span className="glass">
            <svg width="30" height="30" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M8 5.500v13l11-6.500Z" fill="currentColor" />
            </svg>
          </span>
          Tap to play
        </button>
      )}
      <button className="skip glass" onClick={onDone}>
        Skip
      </button>
    </section>
  )
}
