import { useRef, useState } from 'react'
import { uploadResume } from '../api.js'
import { BackIcon, UploadIcon } from '../icons.jsx'

export default function Admin({ status, onBack, onUploaded }) {
  const [file, setFile] = useState(null)
  const [dragging, setDragging] = useState(false)
  const [busy, setBusy] = useState(false)
  const [result, setResult] = useState(null)
  const inputRef = useRef(null)

  function choose(candidate) {
    if (!candidate) return
    const isPdf = candidate.type === 'application/pdf' || candidate.name.toLowerCase().endsWith('.pdf')
    setResult(isPdf ? null : { error: true, text: 'Please choose a PDF file.' })
    setFile(isPdf ? candidate : null)
  }

  async function upload() {
    setBusy(true)
    setResult(null)
    try {
      const updated = await uploadResume(file)
      onUploaded(updated)
      setResult({ text: `Resume updated. ${updated.chunks} sections indexed and live in the chat.` })
      setFile(null)
    } catch (error) {
      setResult({ error: true, text: error.message })
    } finally {
      setBusy(false)
    }
  }

  return (
    <section className="screen admin">
      <header className="chat-header">
        <button className="round glass" onClick={onBack} aria-label="Back to home">
          <BackIcon />
        </button>
        <h2>Admin</h2>
        <span className="round" aria-hidden="true" />
      </header>

      <div className="scroll admin-body">
        <div className="section-title">
          <h3>Update resume</h3>
        </div>

        <dl className="facts glass">
          <div>
            <dt>Current file</dt>
            <dd>{status?.sources?.[0] || 'Not available'}</dd>
          </div>
          <div>
            <dt>Indexed</dt>
            <dd>{status?.indexed_at ? new Date(status.indexed_at).toLocaleString() : 'Not yet'}</dd>
          </div>
          <div>
            <dt>Sections</dt>
            <dd>{status?.chunks ?? 0}</dd>
          </div>
        </dl>

        <button
          className={`dropzone${dragging ? ' dragging' : ''}`}
          onClick={() => inputRef.current.click()}
          onDragOver={(event) => {
            event.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault()
            setDragging(false)
            choose(event.dataTransfer.files[0])
          }}
        >
          <UploadIcon />
          <strong>{file ? file.name : 'Attach a new resume'}</strong>
          <span>{file ? `${Math.ceil(file.size / 1024)} KB · tap to change` : 'PDF, up to 10 MB. Tap or drop it here.'}</span>
        </button>
        <input
          ref={inputRef}
          type="file"
          accept="application/pdf,.pdf"
          hidden
          onChange={(event) => {
            choose(event.target.files[0])
            event.target.value = ''
          }}
        />

        {result && (
          <p className={`notice${result.error ? ' notice-error' : ''}`} role="status">
            {result.text}
          </p>
        )}
      </div>

      <footer className="dock">
        <button className="pill-button" disabled={!file || busy} onClick={upload}>
          {busy ? 'Updating…' : 'Replace resume'}
        </button>
      </footer>
    </section>
  )
}
