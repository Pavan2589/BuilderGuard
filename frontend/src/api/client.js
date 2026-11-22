const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export class ApiError extends Error {
  constructor(message, status) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function request(path, options = {}) {
  let res
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
  } catch (err) {
    throw new ApiError(
      `Could not reach the BuilderGuard API at ${BASE_URL}${path}. ${err.message}`,
      0
    )
  }

  if (!res.ok) {
    let detail = ''
    try {
      const body = await res.json()
      detail = body?.detail || body?.message || JSON.stringify(body)
    } catch {
      detail = res.statusText
    }
    throw new ApiError(
      `Request to ${path} failed (${res.status}): ${detail}`,
      res.status
    )
  }

  if (res.status === 204) return null
  return res.json()
}

export function createReview(prUrl) {
  return request('/api/reviews', {
    method: 'POST',
    body: JSON.stringify({ pr_url: prUrl }),
  })
}

export function fetchSecurityTests() {
  return request('/api/security/tests', { method: 'GET' })
}

export function runSecurityTest(testId) {
  return request('/api/security/tests/run', {
    method: 'POST',
    body: JSON.stringify({ test_id: testId }),
  })
}
