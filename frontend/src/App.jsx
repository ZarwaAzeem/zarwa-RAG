import { useEffect, useState } from 'react'
import { getStatus, sendMessage } from './api.js'
import Intro from './components/Intro.jsx'
import Welcome from './components/Welcome.jsx'
import Home from './components/Home.jsx'
import Chat from './components/Chat.jsx'
import Admin from './components/Admin.jsx'
import Starfield from './components/Starfield.jsx'

// Typing this anywhere in the app opens the admin page.
const CHEAT_CODE = 'zarwo'

export default function App() {
  const [view, setView] = useState('intro')
  // Chats are kept in memory only: every page load starts clean.
  const [conversation, setConversation] = useState(null)
  const [pending, setPending] = useState(false)
  const [status, setStatus] = useState(null)

  // Earlier versions saved chats in the browser; make sure none are left behind.
  useEffect(() => {
    try {
      localStorage.removeItem('zarwa-rag-conversations')
    } catch {
      // Storage unavailable: nothing to clean up.
    }
  }, [])

  // Poll the backend so the header can show whether the knowledge base is live.
  useEffect(() => {
    let cancelled = false
    const check = () =>
      getStatus()
        .then((result) => !cancelled && setStatus(result))
        .catch(() => !cancelled && setStatus({ ready: false, offline: true }))
    check()
    const timer = setInterval(check, 10000)
    return () => {
      cancelled = true
      clearInterval(timer)
    }
  }, [])

  useEffect(() => {
    let typed = ''
    const open = () => {
      typed = ''
      setView('admin')
    }
    const onKeyDown = (event) => {
      if (event.key.length !== 1) return
      typed = (typed + event.key.toLowerCase()).slice(-CHEAT_CODE.length)
      if (typed === CHEAT_CODE) open()
    }
    // Phone keyboards don't report individual keys, so also watch text fields.
    const onInput = (event) => {
      if (event.target.value?.toLowerCase().endsWith(CHEAT_CODE)) open()
    }
    window.addEventListener('keydown', onKeyDown)
    window.addEventListener('input', onInput)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      window.removeEventListener('input', onInput)
    }
  }, [])

  // Replies that arrive after the visitor has moved to another chat are dropped.
  function appendMessage(id, message) {
    setConversation((current) =>
      current?.id === id ? { ...current, messages: [...current.messages, message] } : current,
    )
  }

  async function ask(id, text) {
    appendMessage(id, { role: 'user', content: text })
    setPending(true)
    try {
      const reply = await sendMessage(text, id)
      const sections = [...new Set(reply.sources.map((source) => source.section))]
      appendMessage(id, { role: 'assistant', content: reply.answer, sections })
    } catch (error) {
      appendMessage(id, { role: 'assistant', content: error.message, error: true })
    } finally {
      setPending(false)
    }
  }

  function startConversation(title, firstMessage) {
    const id = crypto.randomUUID()
    setConversation({ id, title, messages: [] })
    setView('chat')
    if (firstMessage) ask(id, firstMessage)
  }

  return (
    <div className="stage">
      <main className="device">
        <Starfield />
        {view === 'intro' && <Intro onDone={() => setView('welcome')} />}
        {view === 'welcome' && <Welcome onStart={() => setView('home')} />}
        {view === 'home' && (
          <Home
            onTopic={(topic) => startConversation(topic.label, topic.question)}
            onNewChat={() => startConversation('New chat')}
          />
        )}
        {view === 'admin' && <Admin status={status} onBack={() => setView('home')} onUploaded={setStatus} />}
        {view === 'chat' && conversation && (
          <Chat
            key={conversation.id}
            conversation={conversation}
            pending={pending}
            onBack={() => setView('home')}
            onNewChat={() => startConversation('New chat')}
            onSend={(text) => ask(conversation.id, text)}
          />
        )}
      </main>
    </div>
  )
}
