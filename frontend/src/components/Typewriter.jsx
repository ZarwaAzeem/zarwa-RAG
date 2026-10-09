import { useEffect, useState } from 'react'

const reducedMotion = () =>
  typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches

/* Reveals `text` a few characters at a time. Shows everything at once when
   disabled or when the visitor prefers reduced motion. */
export function useTypewriter(text, { interval = 38, step = 1, delay = 0, enabled = true } = {}) {
  const animate = enabled && !reducedMotion()
  const [count, setCount] = useState(animate ? 0 : text.length)

  useEffect(() => {
    if (!animate) {
      setCount(text.length)
      return
    }
    setCount(0)
    let timer
    const start = setTimeout(() => {
      timer = setInterval(() => {
        setCount((current) => {
          if (current + step >= text.length) clearInterval(timer)
          return Math.min(text.length, current + step)
        })
      }, interval)
    }, delay)
    return () => {
      clearTimeout(start)
      clearInterval(timer)
    }
  }, [text, interval, step, delay, animate])

  return { shown: text.slice(0, count), rest: text.slice(count), done: count >= text.length }
}

/* Types `text` in place. The untyped remainder is rendered invisibly so the
   layout never shifts while the text appears. */
export default function Typewriter({ text, as: Tag = 'span', className, ...options }) {
  const { shown, rest, done } = useTypewriter(text, options)
  return (
    <Tag className={className} aria-label={text}>
      <span aria-hidden="true">{shown}</span>
      {!done && <span className="caret" aria-hidden="true" />}
      <span className="untyped" aria-hidden="true">
        {rest}
      </span>
    </Tag>
  )
}
