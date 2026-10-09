import { useEffect, useRef, useState } from 'react'
import { BackIcon, MicIcon, NewChatIcon, SendIcon } from '../icons.jsx'
import { useTypewriter } from './Typewriter.jsx'

const SpeechRecognition =
  typeof window !== 'undefined' && (window.SpeechRecognition || window.webkitSpeechRecognition)

const STARTERS = [
  'What projects has Zarwa built?',
  'Which ML tools does Zarwa use?',
  'How can I contact Zarwa?',
]

/* The backend answers in plain text with **bold** and "- " / "•" bullets. */
function renderInline(text) {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, index) =>
    part.startsWith('**') && part.endsWith('**') ? <strong key={index}>{part.slice(2, -2)}</strong> : part,
  )
}

function MessageBody({ content }) {
  const blocks = []
  for (let line of content.split('\n')) {
    // While an answer is being typed out a bold marker can still be open: close it.
    if ((line.match(/\*\*/g) || []).length % 2) line = line.endsWith('**') ? line.slice(0, -2) : `${line}**`
    const bullet = line.match(/^\s*[-•*]\s+(.*)$/)
    const last = blocks[blocks.length - 1]
    if (bullet) {
      if (last?.type === 'list') last.items.push(bullet[1])
      else blocks.push({ type: 'list', items: [bullet[1]] })
    } else if (line.trim()) {
      blocks.push({ type: 'text', text: line })
    }
  }
  return blocks.map((block, index) =>
    block.type === 'list' ? (
      <ul key={index}>
        {block.items.map((item, itemIndex) => (
          <li key={itemIndex}>{renderInline(item)}</li>
        ))}
      </ul>
    ) : (
      <p key={index}>{renderInline(block.text)}</p>
    ),
  )
}

/* An assistant reply. New replies are typed out; long ones type faster so no
   answer takes more than a few seconds to appear. */
function Answer({ message, animate }) {
  const step = Math.max(1, Math.ceil(message.content.length / 220))
  const { shown, done } = useTypewriter(message.content, { interval: 16, step, enabled: animate })
  return (
    <>
      <MessageBody content={shown} />
      {done && message.sections?.length > 0 && (
        <div className="sources">
          {message.sections.map((section) => (
            <span key={section}>{section}</span>
          ))}
        </div>
      )}
    </>
  )
}

export default function Chat({ conversation, pending, onBack, onNewChat, onSend }) {
  const [draft, setDraft] = useState('')
  const [listening, setListening] = useState(false)
  const endRef = useRef(null)
  const lastUserRef = useRef(null)
  // Only replies that arrive while this chat is open are typed out.
  const liveFrom = useRef(conversation.messages.length)
  const recognitionRef = useRef(null)

  const messages = conversation.messages
  const lastUserIndex = messages.findLastIndex((message) => message.role === 'user')

  // When an answer lands, bring the question to the top so a long answer is read
  // from its start; otherwise follow the newest message.
  useEffect(() => {
    const answered = messages.at(-1)?.role === 'assistant'
    const target = answered && lastUserRef.current ? lastUserRef.current : endRef.current
    target?.scrollIntoView({ behavior: 'smooth', block: answered ? 'start' : 'end' })
  }, [messages.length, pending])

  useEffect(() => () => recognitionRef.current?.abort(), [])

  function submit(text) {
    const message = text.trim()
    if (!message || pending) return
    onSend(message)
    setDraft('')
  }

  function toggleMic() {
    if (listening) {
      recognitionRef.current?.stop()
      return
    }
    const recognition = new SpeechRecognition()
    recognition.lang = 'en-US'
    recognition.interimResults = true
    recognition.onresult = (event) =>
      setDraft(Array.from(event.results, (result) => result[0].transcript).join(''))
    recognition.onend = () => setListening(false)
    recognition.onerror = () => setListening(false)
    recognitionRef.current = recognition
    recognition.start()
    setListening(true)
  }

  const showMic = SpeechRecognition && !draft.trim()

  return (
    <section className="screen chat">
      <header className="chat-header">
        <button className="round glass" onClick={onBack} aria-label="Back to home">
          <BackIcon />
        </button>
        <h2>{conversation.title}</h2>
        <button className="round glass" onClick={onNewChat} aria-label="Start a new chat">
          <NewChatIcon />
        </button>
      </header>

      <div className="scroll messages">
        {conversation.messages.length === 0 && !pending && (
          <div className="starters">
            <p>Ask me anything about Zarwa's skills, projects, experience or education.</p>
            {STARTERS.map((starter) => (
              <button key={starter} className="bubble bubble-user" onClick={() => submit(starter)}>
                {starter}
              </button>
            ))}
          </div>
        )}

        {conversation.messages.map((message, index) => (
          <div
            key={index}
            ref={index === lastUserIndex ? lastUserRef : null}
            className={`bubble bubble-${message.role}${message.error ? ' bubble-error' : ''}`}
          >
            {message.role === 'assistant' ? (
              <Answer message={message} animate={index >= liveFrom.current && !message.error} />
            ) : (
              <MessageBody content={message.content} />
            )}
          </div>
        ))}

        {pending && (
          <div className="bubble bubble-assistant typing" aria-label="Assistant is typing">
            <i />
            <i />
            <i />
          </div>
        )}
        <div ref={endRef} />
      </div>

      <form
        className="dock"
        onSubmit={(event) => {
          event.preventDefault()
          submit(draft)
        }}
      >
        <input
          className="dock-input glass"
          value={draft}
          onChange={(event) => setDraft(event.target.value)}
          placeholder={listening ? 'Listening…' : 'Your message…'}
          maxLength={2000}
          aria-label="Your message"
          autoFocus
        />
        {showMic ? (
          <button
            type="button"
            className={`round action${listening ? ' listening' : ''}`}
            onClick={toggleMic}
            aria-label={listening ? 'Stop listening' : 'Speak your message'}
          >
            <MicIcon />
          </button>
        ) : (
          <button type="submit" className="round action" disabled={!draft.trim() || pending} aria-label="Send message">
            <SendIcon />
          </button>
        )}
      </form>
    </section>
  )
}
