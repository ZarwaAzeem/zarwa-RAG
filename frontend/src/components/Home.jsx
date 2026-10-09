import { ChatIcon } from '../icons.jsx'
import Typewriter from './Typewriter.jsx'

const TOPICS = [
  { id: 'skills', label: 'Skills', question: "What are Zarwa's technical skills?" },
  { id: 'projects', label: 'Projects', question: 'What projects has Zarwa built?' },
  { id: 'experience', label: 'Experience', question: "What is Zarwa's work experience?" },
  { id: 'education', label: 'Education', question: 'Where did Zarwa study?' },
  { id: 'contact', label: 'Contact', question: 'How can I get in touch with Zarwa?' },
]

export default function Home({ onTopic, onNewChat }) {
  return (
    <section className="screen home">
      <header className="home-header">
        <div className="home-heading">
          <strong>Zarwa Azeem</strong>
          <Typewriter text="What would you like to know?" interval={34} delay={250} />
        </div>
      </header>

      <div className="scroll" />

      <footer className="dock dock-stacked">
        <div className="chips">
          {TOPICS.map((topic) => (
            <button key={topic.id} className="chip" onClick={() => onTopic(topic)}>
              {topic.label}
            </button>
          ))}
        </div>
        <button className="dock-input glass" onClick={onNewChat}>
          <ChatIcon />
          Ask anything about Zarwa…
        </button>
      </footer>
    </section>
  )
}
