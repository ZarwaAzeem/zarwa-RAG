const API_URL = (import.meta.env.VITE_API_URL || 'http://localhost:8080').replace(/\/$/, '')

async function request(path, options) {
  let response
  try {
    response = await fetch(`${API_URL}${path}`, options)
  } catch {
    throw new Error("Can't reach the assistant right now. Is the backend running on port 8080?")
  }
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = typeof body?.detail === 'string' ? body.detail : null
    const error = new Error(detail || `The assistant ran into a problem (${response.status}).`)
    error.status = response.status
    throw error
  }
  return response.json()
}

// Each page load gets its own private session from the backend. The id lives
// only in memory, so a visitor's chats are theirs alone and end with the tab.
let session = null

function getSession() {
  session ??= request('/api/session', { method: 'POST' }).then((body) => body.session_id)
  session.catch(() => (session = null))
  return session
}

export async function sendMessage(message, conversationId) {
  const send = async () =>
    request('/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Session-Id': await getSession() },
      body: JSON.stringify({ message, conversation_id: conversationId }),
    })
  try {
    return await send()
  } catch (error) {
    if (error.status !== 401) throw error
    // The session expired (or the backend restarted): start a new one and retry.
    session = null
    return send()
  }
}

export function uploadResume(file) {
  return request('/api/admin/resume', {
    method: 'POST',
    headers: { 'Content-Type': 'application/pdf' },
    body: file,
  })
}

export function getStatus() {
  return request('/api/status')
}
