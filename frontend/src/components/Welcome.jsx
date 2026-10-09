import Typewriter from './Typewriter.jsx'

export default function Welcome({ onStart }) {
  return (
    <section className="screen welcome">
      <div className="orb orb-top" />
      <div className="orb orb-side" />
      <div className="orb orb-main" />
      <div className="welcome-body">
        <p className="eyebrow">Zarwa Azeem · Resume assistant</p>
        <Typewriter as="h1" className="welcome-title" text={'One resume.\nMany ways\nto ask.'} interval={70} delay={300} />
        <Typewriter
          as="p"
          className="welcome-sub"
          text="Chat with an assistant that knows Zarwa Azeem's work."
          interval={24}
          delay={2300}
        />
        <button className="pill-button" onClick={onStart}>
          Get Started
        </button>
      </div>
    </section>
  )
}
